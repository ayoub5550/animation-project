# SheepIt render farm — how we use it (verified 2026-09-02)

**What it is:** free, volunteer-powered distributed render farm for Blender (since 2007). The server splits an animation into single frames, sends each frame to a volunteer's machine, collects the results. Account: see `ACCOUNTS.md` (username `ayoub5550`; the login box in the page header takes the *username*, not the email).

## Rules of the farm (gates we hit)
1. **Points** — rendering frames for others earns points; your own frames cost points. Queue priority follows points. A new account (0 points) still renders, but last in the queue.
2. **You must have rendered ≥ 10 frames for others before you may add a project** ("Get started" page shows the block). A **profile image** is also required (uploaded 2026-09-02).
3. Project = one packed `.blend` (File → External Data → Pack Resources; in Python `bpy.ops.file.pack_all()`), ≤ ~500 MB, no external add-ons, no linked libraries. Eevee and Cycles are both accepted (Eevee frames only go to GPU clients with a display).
4. Everything you upload is rendered on strangers' machines — nothing confidential. Fine for us: all assets are free templates.

## Running the client (earn points / meet the 10-frame gate)
- Download: `https://www.sheepit-renderfarm.com/media/applet/client-latest.php` (Java jar). Portable JRE 17 from Adoptium works if `java` is missing.
- Headless text UI:
  `java -jar sheepit-client.jar -ui text -login ayoub5550 -password '<pw>' -cache-dir ./cache -compute-method CPU -cores N -hostname viktor-agent --no-gpu --no-systray --headless`
- On the agent sandbox (1 CPU core) one frame takes ~25 min → 10 frames ≈ 4 h. **Much faster: the owner runs the client on his own PC/GPU for 30 min** (download the launcher from the Get Started page, log in, click Start). His GPU renders a frame in seconds → gate passed and hundreds of points.

## Submitting a project (via the website, logged in)
Get started → "Add your project" → upload the packed `.blend` → choose scene/camera, frame range, output format (PNG), engine → Submit. Track under Projects; download frames as zip when finished, then `ffmpeg -framerate 24 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p film.mp4` and mix sound.

## Test project prepared
`street_night.blend` (208 MB packed): Mixamo "James" walks down a Poly Haven night street, stops under a street lamp, looks around. 720 frames @ 24 fps, Eevee, 1080p. Built entirely by script (`pipeline/blender_build_scene.py`) from downloaded templates. Local software-GL preview: ~30 s/frame at 480p.

## Permanent client on the owner's x86 VPS (set up 2026-09-02)
- Host `185.114.48.164` (Ubuntu 26.04, 2 vCPU, 3.9 GB RAM, no GPU; also runs the owner's production Node/Python apps — do not starve them). Credentials in the private store.
- Service: `/etc/systemd/system/sheepit.service` → `systemctl status sheepit`, log `/opt/sheepit/client.log` (lines use `\r`; read with `tr '\r' '\n'`). Flags: `-cores 1 -memory 1800M -priority 19 --headless --no-gpu`, cgroup `MemoryMax=2300M`, `CPUWeight=20`, `Restart=always`, enabled at boot.
- Added a 4 GB swapfile (`/swapfile`, in fstab) — without it the first project failed with "Project tried to use too much memory". Small-memory projects only; expect "No job available" pauses (retries every 5 min). First frames uploaded 08:35 UTC.
- Hostname shown on SheepIt: `ayoub-vps-srv8394`.
