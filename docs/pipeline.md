# The method, step by step (verified on the zombie prototype, 2026‑09‑02)

## 0. Tools
- Godot 4.7.2 stable Linux x86_64 (`Godot_v4.7.2-stable_linux.x86_64.zip` from GitHub releases). Headless works for import/scripts; rendering needs Xvfb + software GL.
- `ffmpeg`, `xvfb` (`apt-get install xvfb`), Python 3 + `httpx` for the Mixamo API.
- Blender (optional, for better lighting / compositing / retargeting CMU mocap).

## 1. Brief → script → asset list
Write `films/<title>/SCRIPT.md`: one table per scene: duration, location (which environment asset), characters (which Mixamo character), actions (which Mixamo clips), camera move, sound (which SFX/music), narration text. Nothing is downloaded before the list exists — it prevents random asset hoarding.

## 2. Characters + animations (Mixamo)
1. Log in to mixamo.com in a browser with the Adobe ID → copy `localStorage.access_token` (valid ~24 h).
2. `pipeline/mixamo_api.py` — search, export, monitor, download. Convention: `<Name>_TPose.fbx` (skin) + `<Name>@<Clip>.fbx` (no skin, `inplace:true` for locomotion). See `pipeline/batch_download_example.py` (70 files ≈ 6 min).
3. **Render a thumbnail of each character and show the owner** before continuing (see lessons).

## 3. Godot project
- `godot --headless --path . --import` imports the FBX (ufbx) and extracts embedded textures.
- `pipeline/godot_build_characters.gd` (`godot --headless --path . --script tools/build_characters.gd`) wraps every T‑pose into a scene with an `AnimationPlayer` containing all `@Clip`s; bone names match, no retargeting.
- Environments: glTF/GLB from Poly Haven / Sketchfab / BlenderKit dropped into `levels/`; add `create_trimesh_collision()` if characters must walk on them.
- Use a template for the camera rig and player/NPC controller (e.g. MIT repos `godotengine/tps-demo`, `selgesel/godot4-third-person-controller`, `lillianhidet/godot-survival-horror`). Glue code only.

## 4. Scene direction = a script, not a player
`pipeline/demo_autopilot_example.gd`: a `Node` script that positions actors, plays clips, moves the camera along keyframes, and advances scene by scene using `await get_tree().create_timer(t).timeout`. For a film, one such script per scene; a master scene loads them in order.

## 5. Rendering (no GPU)
```bash
export LIBGL_ALWAYS_SOFTWARE=1
xvfb-run -a -s "-screen 0 1280x720x24" ./Godot_v4.7.2-stable_linux.x86_64 --path . \
  --rendering-driver opengl3 --rendering-method gl_compatibility \
  --write-movie out/frame.png --fixed-fps 30 --quit-after 720 res://scenes/film.tscn
ffmpeg -framerate 30 -i out/frame%08d.png -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart film.mp4
```
- Forward+/Vulkan through lavapipe crashes (signal 11) in Movie Maker mode → always `gl_compatibility`. Volumetric fog is unavailable there; say so to the owner (real render on a GPU looks better).
- Cost: ~0.2 s/frame render + ~0.45 s/frame PNG write at 1600×900 → 24 s of film ≈ 8 min; 5 min of film ≈ 1.5–2 h. Run under `nohup`, wait for `Done recording` in the log.
- Check thumbnails of frames (`ffmpeg -i frame.png -vf scale=640:-1 s.jpg`) before encoding.

## 6. Sound
- Narration: text‑to‑speech (agent tool) → `narration.wav`. SFX/music from `SOURCES.md`. Mix: `ffmpeg -i film.mp4 -i mix.wav -c:v copy -c:a aac -shortest final.mp4` (build `mix.wav` with `ffmpeg -filter_complex amix`/`adelay`).
- Mixamo has no facial rig → no lip sync; shoot dialogue from medium/far or use narration.

## 7. Deliver
MP4 + project zip (exclude `.godot/`) + `CREDITS.md`. State clearly: scripted autopilot, renderer used, missing audio, known glitches.
