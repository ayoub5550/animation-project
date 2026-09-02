"""Multi-account Beam.cloud render farm for Blender.

Spreads frame chunks of one .blend across several Beam.cloud accounts (each account has its
own GPU concurrency quota, ~5 containers) and its own free $ credit, then collects the frames
and assembles an MP4.

Accounts file (NEVER commit it; keep it outside the repo, default ~/.beam/accounts.json):
  [{"name": "beam1", "token": "....", "max_parallel": 5},
   {"name": "beam2", "token": "....", "max_parallel": 5}]

Usage (run from the folder that contains render_beam.py, with the beam venv on PATH):
  python beam_farm.py upload  street_night.blend            # push .blend to every account's volume
  python beam_farm.py render  street_night.blend 1 720 --chunk 90 [--samples 64] [--engine CYCLES]
  python beam_farm.py collect street_night.blend frames/    # download frames from all accounts
  python beam_farm.py check   frames/ 1 720                 # list missing frames
  python beam_farm.py assemble frames/ film.mp4 [--fps 24] [--audio ambience.wav]

How it works: every chunk is one subprocess `python render_beam.py ranges A-B` executed with a
private HOME whose ~/.beam/config.ini holds that account's token (the Beam SDK reads the token
from ~/.beam/config.ini). A chunk that fails (quota rejected, timeout, crash) is re-queued and
handed to the next free account. State is written to farm_state.json so a killed run can resume.
"""
import os, sys, json, time, subprocess, shutil, glob, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCOUNTS_FILE = Path(os.environ.get("BEAM_ACCOUNTS", "~/.beam/accounts.json")).expanduser()
VOL = "blender-jobs"
STATE = HERE / "farm_state.json"
HOMES = Path(os.environ.get("BEAM_FARM_HOMES", "/tmp/beam_farm_homes"))


# ---------- accounts / auth ----------
def load_accounts():
    if not ACCOUNTS_FILE.exists():
        sys.exit(f"accounts file not found: {ACCOUNTS_FILE} (see docstring)")
    accs = json.loads(ACCOUNTS_FILE.read_text())
    for a in accs:
        a.setdefault("max_parallel", 5)
        a["home"] = str(HOMES / a["name"])
        cfg = Path(a["home"]) / ".beam"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "config.ini").write_text(
            f"[default]\ntoken = {a['token']}\ngateway_host = gateway.beam.cloud\ngateway_port = 443\n")
    return accs


def env_for(acc):
    e = os.environ.copy()
    e["HOME"] = acc["home"]
    return e


def beam(acc, *args, capture=True, cwd=None):
    # NOTE: `beam cp beam://... <dest>` requires <dest> to be inside the CWD -> pass cwd=
    return subprocess.run(["beam", *args], env=env_for(acc), text=True,
                          capture_output=capture, timeout=3600, cwd=cwd)


# ---------- volume helpers ----------
def volume_exists(acc):
    r = beam(acc, "volume", "list")
    return VOL in r.stdout


def ensure_volume(acc):
    if not volume_exists(acc):
        print(f"[{acc['name']}] creating volume {VOL}")
        beam(acc, "volume", "create", VOL)


def ls(acc, path):
    r = beam(acc, "ls", f"{VOL}/{path}")
    return r.stdout if r.returncode == 0 else ""


def upload(blend_path, force=False):
    """Upload the .blend to every account's volume. --force re-uploads (after editing the scene!)."""
    blend = Path(blend_path)
    for acc in load_accounts():
        ensure_volume(acc)
        if not force and blend.name in ls(acc, ""):
            print(f"[{acc['name']}] {blend.name} already on volume, skipping")
            continue
        print(f"[{acc['name']}] uploading {blend.name} ({blend.stat().st_size/1e6:.0f} MB) ...")
        r = beam(acc, "cp", str(blend), f"beam://{VOL}/{blend.name}", capture=False)
        print(f"[{acc['name']}] upload rc={r.returncode}")


# ---------- render ----------
def chunk_ranges(start, end, size):
    return [(a, min(a + size - 1, end)) for a in range(start, end + 1, size)]


def start_chunk(acc, blend, a, b, engine, samples):
    env = env_for(acc)
    env.update(BLEND=blend, ENGINE=engine, SAMPLES=str(samples))
    log = open(HERE / f"farm_logs/{acc['name']}_{a:04d}-{b:04d}.log", "w")
    p = subprocess.Popen([sys.executable, str(HERE / "render_beam.py"), "ranges", f"{a}-{b}"],
                         env=env, stdout=log, stderr=subprocess.STDOUT, cwd=HERE)
    return {"proc": p, "log": log, "acc": acc, "range": (a, b), "t0": time.time()}


def chunk_result(run):
    """Parse render_beam.py output -> frames_done (or -1 on failure)."""
    run["log"].close()
    txt = open(run["log"].name).read()
    m = re.findall(r"'frames_done': (\d+)", txt)
    if run["proc"].returncode != 0 or not m:
        return -1, txt[-800:]
    return int(m[-1]), ""


def render(blend, start, end, chunk=90, engine="CYCLES", samples=64, ranges=None):
    accs = load_accounts()
    (HERE / "farm_logs").mkdir(exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    done = {tuple(x) for x in state.get("done", [])} if state.get("blend") == blend else set()
    if ranges:  # explicit re-render list "A-B,C-D" (e.g. from `check` output); ignores done-state
        queue = [c for r in ranges.split(",") for c in chunk_ranges(int(r.split("-")[0]), int(r.split("-")[1]), chunk)]
    else:
        queue = [r for r in chunk_ranges(start, end, chunk) if r not in done]
    print(f"{len(queue)} chunks to render across {len(accs)} accounts "
          f"(max {sum(a['max_parallel'] for a in accs)} parallel GPUs)")
    running, attempts, t0 = [], {}, time.time()
    while queue or running:
        # launch round-robin onto accounts with free slots (spreads cost over all credits)
        launched = True
        while queue and launched:
            launched = False
            for acc in accs:
                busy = sum(1 for r in running if r["acc"] is acc)
                if queue and busy < acc["max_parallel"]:
                    a, b = queue.pop(0)
                    attempts[(a, b)] = attempts.get((a, b), 0) + 1
                    print(f"[{acc['name']}] start {a}-{b} (attempt {attempts[(a, b)]})")
                    running.append(start_chunk(acc, blend, a, b, engine, samples))
                    launched = True
        time.sleep(10)
        for run in list(running):
            if run["proc"].poll() is None:
                continue
            running.remove(run)
            a, b = run["range"]
            frames, err = chunk_result(run)
            if frames >= (b - a + 1):
                done.add((a, b))
                print(f"[{run['acc']['name']}] done {a}-{b}: {frames} frames in "
                      f"{(time.time()-run['t0'])/60:.1f} min")
                STATE.write_text(json.dumps({"blend": blend, "done": sorted(done)}))
            else:
                print(f"[{run['acc']['name']}] FAILED {a}-{b} ({frames} frames)\n{err}")
                if "quota exceeded" in err or "concurrency_limit" in err:
                    # not a render failure: the account has no free GPU slot right now.
                    # don't burn an attempt, back off and requeue (other launchers / accounts may be busy)
                    attempts[(a, b)] -= 1
                    print(f"  -> GPU quota busy on {run['acc']['name']}, waiting 90 s before requeue")
                    time.sleep(90)
                    accs.append(accs.pop(accs.index(run["acc"])))
                    queue.append((a, b))
                elif attempts[(a, b)] < 3 * len(accs):
                    # move the failing account to the back so another one gets the retry
                    accs.append(accs.pop(accs.index(run["acc"])))
                    queue.append((a, b))
                else:
                    print(f"giving up on {a}-{b}")
    print(f"ALL DONE: {len(done)} chunks in {(time.time()-t0)/60:.1f} min")


# ---------- collect / check / assemble ----------
def collect(blend, out_dir, workers=8):
    """Download rendered frames from every account's volume.
    `beam cp` cannot download a directory (404 "Unable to get file size"),
    so we list the folder and fetch files one by one, in parallel."""
    import re
    from concurrent.futures import ThreadPoolExecutor
    name = Path(blend).stem
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    have = {p.name for p in out.glob("frame_*.png")}
    jobs = []
    for acc in load_accounts():
        listing = ls(acc, f"out/{name}")
        files = re.findall(r"(frame_\d+\.png)", listing)
        files = [f for f in files if f not in have]
        print(f"[{acc['name']}] {len(files)} new frames to download")
        jobs += [(acc, f) for f in files]
        have.update(files)

    def fetch(job):
        acc, f = job
        r = beam(acc, "cp", f"beam://{VOL}/out/{name}/{f}", ".", cwd=str(out))
        return f, r.returncode == 0 and (out / f).exists()

    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(fetch, jobs))
    failed = [f for f, ok in results if not ok]
    if failed:
        print(f"FAILED {len(failed)}: {failed[:10]} ... rerun collect to retry")
    print(f"{len(list(out.glob('frame_*.png')))} frames in {out}")


def check(out_dir, start, end):
    have = {int(p.stem[6:]) for p in Path(out_dir).glob("frame_*.png")}
    missing = [f for f in range(start, end + 1) if f not in have]
    rng, prev = [], None
    for f in missing:
        if rng and f == rng[-1][1] + 1: rng[-1][1] = f
        else: rng.append([f, f])
    print("missing:", " ".join(f"{a}-{b}" for a, b in rng) or "none")
    return rng


def assemble(out_dir, mp4, fps=24, audio=None):
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", str(Path(out_dir) / "frame_%04d.png")]
    if audio:
        cmd += ["-i", audio, "-shortest", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", mp4]
    subprocess.run(cmd, check=True)
    print("wrote", mp4)


def opt(flag, default, cast=str):
    return cast(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    mode, args = sys.argv[1], sys.argv[2:]
    if mode == "upload":
        upload(args[0], force="--force" in sys.argv)
    elif mode == "render":
        render(Path(args[0]).name, int(args[1]), int(args[2]), chunk=opt("--chunk", 90, int),
               engine=opt("--engine", "CYCLES"), samples=opt("--samples", 64, int),
               ranges=opt("--ranges", None))
    elif mode == "collect":
        collect(args[0], args[1])
    elif mode == "check":
        check(args[0], int(args[1]), int(args[2]))
    elif mode == "assemble":
        assemble(args[0], args[1], fps=opt("--fps", 24, int), audio=opt("--audio", None))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
