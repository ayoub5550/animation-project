# Example: "Street Night" test film (2026-09-02)

`street_night_test.mp4` — 30 s, 720 frames @ 24 fps, 1920×1080, Cycles/OptiX 64 samples + denoise, rendered on Beam.cloud (≈ 60 GPU‑minutes, ≈ $1). Stereo audio mixed with ffmpeg.

**Why it is here:** proof that the pipeline works end to end with *zero hand‑made assets* — a rigged Mixamo character and its animations, Poly Haven CC0 environment, Mixkit sound, assembled by scripts only (`pipeline/blender_build_scene.py` → `pipeline/beam_farm.py`). It is also the **quality floor**: any new film must look at least this good (realistic character, physically based lighting, denoised, no flicker, sound synced to motion).

**Known weaknesses (owner's review):** scene composition is somewhat random and the shots are not driven by a story. Future films must start from a script/storyboard (`docs/pipeline.md`), then pick templates to fit the shots — not the other way round.

Credits: see `../../CREDITS.md`. Contact sheet: `contact_sheet.jpg` (one frame every 60).
