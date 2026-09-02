# Beam.cloud GPU render farm — how we use it (verified 2026-09-02)

**What it is:** serverless GPU cloud (https://beam.cloud). You write a Python function, decorate it, and Beam runs it in a container on a rented GPU, billed **per second of run time** (not for image pull or queue waiting). This is our primary renderer for Blender. SheepIt (`docs/sheepit.md`) is the free fallback.

Docs: https://docs.beam.cloud/llms.txt (index; append `.md` to any docs URL to get raw markdown). Dashboard: https://platform.beam.cloud

## Accounts
Three workspaces, each with a **$30/month credit** (promo the owner got). Tokens are **not in this public repo** — see `ACCOUNTS.md`; they live in the agent's private store / owner's DM. Template: `pipeline/beam_accounts.example.json`.

| Name | Workspace id | Workspace name | Notes |
|---|---|---|---|
| beam1 | `8073c185-0aee-444d-ba0a-bb59df4a39c7` | `ac778e` | volume `blender-jobs` created, image cached |
| beam2 | `5e7a7bf3-1ee7-454a-acbf-176280416e30` | `c7886d` | volume + blend uploaded |
| beam3 | (not given) | `7252d3` | volume + blend uploaded |

Each account is independent: its own volume, its own GPU quota, its own credit. That is why the farm script exists.

## Setup (once per machine)
```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install beam-client            # tested 0.2.207; do NOT install into a shared site-packages (broke pydantic once)
beam configure default --token <TOKEN1>
beam configure beam2   --token <TOKEN2>   # optional named contexts: beam --context beam2 <cmd>
beam volume create blender-jobs
beam cp street_night.blend beam://blender-jobs/street_night.blend
beam ls blender-jobs
```
Config lands in `~/.beam/config.ini`. **The Python SDK always reads `[default]` from that file; `BEAM_TOKEN` env is ignored once the file exists.** `beam_farm.py` therefore gives every account its own `HOME` (`/tmp/beam_farm_homes/<name>`).

## Pricing (2026-09-02, from docs)
RTX 4090 $0.000191667/s (≈$0.69/h) · RTX 5090 $0.000303/s · A10G, T4 cheaper · CPU $0.0000125/s/core · RAM $0.0000021/s/GiB · volumes free ≤1 TB. Task default timeout 20 min if it never starts.

## Rendering: `pipeline/render_beam.py`
Image = `nvidia/cuda:12.4.1-runtime-ubuntu22.04` + python 3.11 + Blender 4.2.14 (tar.xz from download.blender.org, mirror mirrors.ocf.berkeley.edu; must use `curl -fSL --retry 3 -A Mozilla/5.0`, plain `wget` gets blocked). Function `render_chunk` → `gpu=["RTX4090","A10G","RTX5090"]` (first available), 4 CPU, 16 GiB, 3 h timeout, volume `blender-jobs` mounted at `/mnt/blender`. Output `/mnt/blender/out/<blend-name>/frame_####.png`.
```bash
python render_beam.py probe 250                 # one frame, prints GPU + seconds
python render_beam.py render 1 720 --chunk 90   # parallel chunks (≤5 per account!)
python render_beam.py ranges 181-270 541-630    # rerun specific ranges
ENGINE=CYCLES SAMPLES=64 BLEND=street_night.blend XVFB=1 ...   # env knobs
```
Measured: Cycles + OptiX, 1080p, 64 samples, OptiX denoise → **~4.7 s/frame** (90 frames ≈ 7 min incl. Blender start) on RTX 4090 *and* A10G. Eevee headless untested (needs `XVFB=1`).

## Farm over several accounts: `pipeline/beam_farm.py`
```bash
export BEAM_ACCOUNTS=~/.beam/accounts.json      # list of {name, workspace, token, max_parallel}
python beam_farm.py upload  street_night.blend  # create volume + upload on every account (skips existing)
python beam_farm.py render  street_night.blend 1 720 --chunk 90 [--samples 64] [--engine CYCLES]
python beam_farm.py collect street_night.blend frames/      # download frames from all accounts (parallel)
python beam_farm.py check   frames/ 1 720                   # prints missing ranges
python beam_farm.py assemble frames/ film.mp4 --fps 24 --audio mix.wav
```
Behaviour: chunks are launched **round-robin**, ≤ `max_parallel` (5) running per account, so 3 accounts = 15 GPUs at once. A failed/rejected chunk is re-queued on another account (3 attempts). State in `farm_state.json`, per-chunk logs in `farm_logs/`. Tested 2026-09-02 on beam2+beam3 (4 frames) and 720 frames on beam1.

## Gotchas (each cost us time)
1. **GPU quota ≈ 5 concurrent tasks per workspace.** Extra tasks are rejected with `concurrency_limit_reached: gpu quota exceeded` and show as CANCELLED in `beam task list`. `.map()` on the SDK then **hangs forever** waiting for them — never launch >5 at once per account; the farm script enforces this.
2. `.map(list)` passes exactly one positional argument per item; pack parameters in a dict.
3. `beam cp beam://vol/folder .` **cannot download a folder** (404 "Unable to get file size"). List with `beam ls` and copy files one by one (collect does this with 8 threads; ~2.7 MB PNG each).
4. `beam cp` destination must be inside the current working directory, otherwise "is not in the subpath".
5. First run per account builds the image (~5–10 min); afterwards it's cached and containers start in seconds. Not billed.
6. Frames land on the volume, not your disk — always `collect` and `check` before `assemble`.

## Costs seen
- Test film 720 frames @1080p Cycles: ≈ 60 GPU-min ≈ **$0.7–1.1** total.
- Estimate: 5‑minute film (7200 frames) ≈ $8–12; the three $30 credits ≈ 130 GPU-hours/month ≈ 60k frames ≈ 40 min of finished 24 fps film.

## Owner's VPS bridge
`185.114.48.164` runs `gpu-bridge.service` (`/opt/beam-bridge/bridge_app.py`, env `/etc/beam-bridge/.env`, uvicorn :8600) which already offloads GPU work to Beam for his other apps — do not touch it; the render farm is independent.
