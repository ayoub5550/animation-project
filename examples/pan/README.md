# Example: "PAN" — cartoon horror short (2026-09-02)

`pan.mp4` — 76 s, 1824 frames @ 24 fps, 1920×1080. Cycles 64 samples + OpenImageDenoise, Toon BSDF materials + Freestyle outlines (thickness 2.5), AgX High Contrast. Story: a dark cartoon retelling of Peter Pan (public‑domain Barrie 1911) — implied, non‑graphic horror.

**Why it is here:** first *story‑driven* film of the pipeline. Storyboard first (`films/pan/STORYBOARD.md`), then templates chosen to fit the shots — the lesson from `../street_night`. Zero hand‑made assets: Mixamo characters (Timmy, Goblin, Amy, Michelle) + animations, Poly Haven CC0 props/HDRI, Mixkit SFX/music, ElevenLabs narration. Built by `films/pan/build_pan.py`, assembled with `pipeline/beam_farm.py assemble`.

**Rendering notes (important):**
- Frames 1–1624 were rendered on the Beam.cloud GPU farm (3 accounts in parallel, `pipeline/beam_farm.py`).
- Mid‑render all Beam accounts were disabled by the provider (see `docs/beam_cloud.md`, `docs/lessons.md`). Frames 1625–1728 (shot 9) were rendered as a **local CPU fallback** (`blender -b pan.blend -o //frames/frame_#### -s 1625 -e 1728 -a`, ~88 s/frame on 1 core). No visible quality difference — same samples/denoiser.
- Title (1–192), black cut (1249–1344) and credits (1729–1824) are generated in post (PIL), not rendered.

**Owner's review of the shots‑1–8 preview:** accepted; final assembled after shot 9. Any weaknesses noted later go here.

Credits: `../../CREDITS.md`. Sounds: `../../SOURCES.md`. Contact sheet: `contact_sheet.jpg` (one frame every 152).
