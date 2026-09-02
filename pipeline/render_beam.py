"""Render a Blender .blend on Beam.cloud GPUs (serverless).

Usage (from this folder, with the beam venv on PATH and BEAM token configured):
  beam cp ../street_night.blend beam://blender-jobs/street_night.blend
  python render_beam.py probe                      # 1 frame, prints engine/device/timing
  python render_beam.py render 1 720 --chunk 90    # parallel containers, one per chunk
  beam cp beam://blender-jobs/out/street_night .   # download frames

Rules: assets come from templates; this script only orchestrates rendering.
"""
import os, sys, subprocess, time, glob, shutil
from beam import function, Image, Volume

VOL = "blender-jobs"
MNT = "/mnt/blender"
BLENDER_URL = "https://download.blender.org/release/Blender4.2/blender-4.2.14-linux-x64.tar.xz"
MIRROR_URL = "https://mirrors.ocf.berkeley.edu/blender/release/Blender4.2/blender-4.2.14-linux-x64.tar.xz"

image = (
    Image(base_image="nvidia/cuda:12.4.1-runtime-ubuntu22.04", python_version="python3.11")
    .add_commands([
        "apt-get update && apt-get install -y --no-install-recommends xz-utils curl ca-certificates "
        "libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libegl1 libxkbcommon0 libsm6 libice6 libgomp1 "
        "libglu1-mesa xvfb && rm -rf /var/lib/apt/lists/*",
        f"(curl -fSL --retry 3 -A Mozilla/5.0 {BLENDER_URL} -o /tmp/b.tar.xz || "
        f"curl -fSL --retry 3 -A Mozilla/5.0 {MIRROR_URL} -o /tmp/b.tar.xz) && ls -la /tmp/b.tar.xz && mkdir -p /opt/blender && "
        "tar -xJf /tmp/b.tar.xz -C /opt/blender --strip-components=1 && rm /tmp/b.tar.xz",
    ])
)

GPU_SETUP = r'''
import bpy, sys
engine = sys.argv[sys.argv.index("--")+1]
samples = int(sys.argv[sys.argv.index("--")+2])
sc = bpy.context.scene
if engine == "CYCLES":
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type != "CPU"
    sc.cycles.device = "GPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX"
    print("DEVICES:", [(d.name, d.type, d.use) for d in prefs.devices])
else:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.taa_render_samples = samples
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
'''


@function(
    gpu=["RTX4090", "A10G", "RTX5090"],
    cpu=4, memory="16Gi", timeout=3600 * 3,
    image=image,
    volumes=[Volume(name=VOL, mount_path=MNT)],
)
def render_chunk(job: dict = None, **kw):
    """Render frames start..end of MNT/blend into MNT/out/<name>/frame_####.png.
    `.map()` passes one positional dict per item; `.remote()` passes kwargs — accept both."""
    p = dict(job or {}); p.update(kw)
    blend, start, end = p["blend"], int(p["start"]), int(p["end"])
    engine, samples, use_xvfb = p.get("engine", "CYCLES"), int(p.get("samples", 64)), bool(p.get("use_xvfb"))
    name = os.path.splitext(os.path.basename(blend))[0]
    out = f"{MNT}/out/{name}"
    os.makedirs(out, exist_ok=True)
    setup = "/tmp/gpu_setup.py"
    open(setup, "w").write(GPU_SETUP)
    cmd = ["/opt/blender/blender", "-b", f"{MNT}/{blend}", "-P", setup,
           "-o", f"{out}/frame_####", "-F", "PNG", "-s", str(start), "-e", str(end), "-a",
           "--", engine, str(samples)]
    if use_xvfb:
        cmd = ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24"] + cmd
    t0 = time.time()
    pr = subprocess.run(cmd, capture_output=True, text=True)
    log = pr.stdout[-6000:] + pr.stderr[-3000:]
    done = [f for f in sorted(glob.glob(f"{out}/frame_*.png"))
            if start <= int(os.path.basename(f)[6:10]) <= end]
    nv = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    return {"start": start, "end": end, "frames_done": len(done), "seconds": round(time.time() - t0, 1),
            "gpu": nv, "rc": pr.returncode, "log": log}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    blend = os.environ.get("BLEND", "street_night.blend")
    engine = os.environ.get("ENGINE", "CYCLES")
    samples = int(os.environ.get("SAMPLES", "64"))
    if mode == "probe":
        f = int(sys.argv[2]) if len(sys.argv) > 2 else 250
        r = render_chunk.remote(blend=blend, start=f, end=f, engine=engine, samples=samples,
                                use_xvfb=os.environ.get("XVFB") == "1")
        if not r: print("remote call failed (see build log above)"); return
        print({k: v for k, v in r.items() if k != "log"}); print(r["log"][-3000:])
    elif mode in ("render", "ranges"):
        if mode == "render":
            s, e = int(sys.argv[2]), int(sys.argv[3])
            chunk = int(sys.argv[sys.argv.index("--chunk") + 1]) if "--chunk" in sys.argv else 90
            rngs = [(a, min(a + chunk - 1, e)) for a in range(s, e + 1, chunk)]
        else:  # python render_beam.py ranges 181-270 541-630   (re-run missing chunks)
            rngs = [tuple(int(x) for x in a.split("-")) for a in sys.argv[2:]]
        jobs = [dict(blend=blend, start=a, end=b, engine=engine, samples=samples) for a, b in rngs]
        print(f"{len(jobs)} containers"); t0 = time.time()
        total = 0
        for r in render_chunk.map(jobs):
            total += r["frames_done"]
            print({k: v for k, v in r.items() if k != "log"})
            if r["rc"] != 0: print(r["log"][-1500:])
        print(f"TOTAL frames {total} in {round((time.time()-t0)/60,1)} min")


if __name__ == "__main__":
    main()
