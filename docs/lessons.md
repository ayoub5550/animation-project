# Lessons (append only)
- 2026‑09‑02 — Character named "Survivor" on Mixamo rendered as a bald, green‑skinned zombie‑like man; the owner spotted it in the final video. **Always render and show a thumbnail of each character before using it.**
- 2026‑09‑02 — First recording was black: the flashlight was toggled off and the aim ray started at the rig origin instead of the camera. Second recording had a frozen ammo HUD: `bake_navigation_mesh(false)` is synchronous and emits `bake_finished` before `await` resumes, so code after the await never ran. Bind UI before/without awaiting.
- 2026‑09‑02 — Godot Forward+ (Vulkan/lavapipe) crashes in Movie Maker mode on a GPU‑less machine; `--rendering-method gl_compatibility` works.
- 2026‑09‑02 — GitHub integration cannot create repos or change visibility (403). The owner must do that; the agent pushes.
- 2026‑09‑02 — Signup CAPTCHAs (Freesound, Pixabay, Zapsplat, Epic) stop automated registration. Agents must not bypass them; ask the owner to click through once. BlenderKit registers with email only (no CAPTCHA). Sketchfab signup = Epic Games SSO.
- 2026‑09‑02 — `zip` is not installed in the sandbox; use Python `zipfile`.
