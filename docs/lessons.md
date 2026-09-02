# Lessons (append only)
- 2026‑09‑02 — Character named "Survivor" on Mixamo rendered as a bald, green‑skinned zombie‑like man; the owner spotted it in the final video. **Always render and show a thumbnail of each character before using it.**
- 2026‑09‑02 — First recording was black: the flashlight was toggled off and the aim ray started at the rig origin instead of the camera. Second recording had a frozen ammo HUD: `bake_navigation_mesh(false)` is synchronous and emits `bake_finished` before `await` resumes, so code after the await never ran. Bind UI before/without awaiting.
- 2026‑09‑02 — Godot Forward+ (Vulkan/lavapipe) crashes in Movie Maker mode on a GPU‑less machine; `--rendering-method gl_compatibility` works.
- 2026‑09‑02 — GitHub integration cannot create repos or change visibility (403). The owner must do that; the agent pushes.
- 2026‑09‑02 — Signup CAPTCHAs (Freesound, Pixabay, Zapsplat, Epic) stop automated registration. Agents must not bypass them; ask the owner to click through once. BlenderKit registers with email only (no CAPTCHA). Sketchfab signup = Epic Games SSO.
- 2026‑09‑02 — `zip` is not installed in the sandbox; use Python `zipfile`.
- 2026‑09‑02 — SheepIt gates: ≥10 frames rendered for others + profile image before you may add a project. Start the client early.
- 2026‑09‑02 — Blender/Mixamo: the T‑pose FBX import leaves an action assigned (`animation_data.action`) that overrides the NLA → set it to None. Mixamo clip actions are in cm; the armature is scaled 0.01 so they still match. Use `inplace:true` for Walking and move the object with keyframes (root motion in a repeated strip snaps back each loop). A camera target parented to the 0.01‑scaled rig ends up at the feet — use a Copy Location constraint with world offset instead.
- 2026‑09‑02 — Eevee Next renders headless with `LIBGL_ALWAYS_SOFTWARE=1` (llvmpipe), ~30 s/frame at 480p/8 samples on 1 core. Fine for previews, not for finals.
- 2026‑09‑02 — Owner's VPS 148.100.112.18 is IBM **s390x** (2 CPU, 3 GB, no GPU): Blender has no build for it → SheepIt client refuses ("This Operating System is not supported"). Only x86_64/arm64 machines with ≥8 GB RAM are useful as farm clients. Credentials for the VPS are in the private store.

## 2026-09-02 — Beam.cloud GPU rendering (replaces SheepIt as primary)
- SheepIt on a 2‑vCPU VPS earns ~1 frame per 25–40 min; owner decided GPU cloud instead. SheepIt client stays running on the VPS (harmless), see `docs/sheepit.md`.
- Beam.cloud: serverless GPU functions; RTX 4090 ≈ $0.69/h, billed per second of run time only. Cycles/OptiX 1080p, 64 samples + denoise = **~5 s/frame** on RTX 4090 (~4.5 s on A10G in our test). 720 frames rendered for ≈ $1.1.
- Gotchas hit (all documented in `docs/beam_cloud.md`): GPU concurrency quota ≈5 per account (extra tasks are *rejected*, `.map()` then hangs forever); `beam cp` cannot download a folder (404) — copy file by file; `beam cp` destination must be inside the CWD; Blender download needs `curl -A Mozilla/5.0 --retry 3`; the SDK ignores `BEAM_TOKEN` when `~/.beam/config.ini` exists — use one HOME per account.
- Multi-account farm: `pipeline/beam_farm.py` spreads chunks round‑robin over N accounts (3 × $30/month credit ≈ 130 GPU‑hours ≈ 60k frames ≈ 40 min of finished film per month).
