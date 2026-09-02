# ACCOUNTS — service accounts for this project

All accounts use the owner's mailbox **`ayoubteke12@gmail.com`**. Verification codes / activation links arrive there; an agent with the owner's Gmail integration reads them with a search like `from:<service> newer_than:1d`.

## Where are the passwords?
This repository is **PUBLIC**. Passwords are therefore **not** committed here — a public repo is indexed by bots within minutes and the accounts would be hijacked. They are kept by the agent in a private store (`credentials.json`, outside git). **As soon as the owner switches the repo to Private (Settings → General → Danger Zone → Change visibility), the agent commits `SECRETS.md` with the full plaintext list**, as the owner requested. Until then, ask the agent (Viktor) in Slack for a password if you need one.

## Status (2026-09-02)
| Service | Purpose | Login | Status | Notes |
|---|---|---|---|---|
| Adobe / Mixamo | realistic rigged characters + animations | Adobe ID, email above | ✅ active | Owner's own Adobe account (password shared in Slack DM; owner asked to rotate it). Internal API documented in `docs/mixamo_api.md`. |
| CGTrader | free 3D models | email above, **passwordless** (6‑digit code to Gmail) | ✅ active | Registered by owner. Free-item download buttons don't fire in headless Playwright — download manually or via `curl` with session cookies. |
| BlenderKit (blendkit.com) | free models/materials/HDRIs inside Blender | email above + password | ✅ active | Created by agent, email verified, ToS accepted. Free tier. |
| SheepIt (sheepit-renderfarm.com) | free distributed Blender render farm | username `ayoub5550` + password (login form in page header uses **username**, not email) | ✅ active | Created by agent 2026-09-02, email confirmed. Blender `.blend` projects only. Priority follows *points*: run the SheepIt client (Java, CPU is fine) to render others' frames and earn points before submitting big jobs.  See `docs/sheepit.md`. |
| Beam.cloud (beam.cloud) | **GPU render farm** (RTX 4090 serverless) | 3 workspaces, API tokens (see `docs/beam_cloud.md`) | ❌ **disabled by Beam 2026-09-02** | All 3 workspaces disabled at once ("Your account has been disabled"), owner changed nothing. Do not use; `docs/beam_cloud.md` kept as reference only. |
| Freesound | CC0/CC‑BY sound effects | username `ayoub5550`, email above | ⛔ blocked | Registration form filled, but reCAPTCHA image challenge appeared. Agents do not solve CAPTCHAs — the owner must click through once (30 s), then the agent uses the account. |
| Sketchfab | downloadable CC 3D models | — | ⛔ not created | Email signup redirects to Epic Games SSO (Sketchfab is owned by Epic). Needs Epic account below. |
| Epic Games (Fab, Sketchfab, Megascans) | Fab marketplace free assets, Megascans, Sketchfab | — | ⛔ not created | Registration asks for **date of birth** (agent will not invent identity data) and uses hCaptcha. Owner: create it once at epicgames.com with the email above; agent then logs in. |
| Poly Haven, ambientCG, Mixkit, Pexels, Sonniss, Incompetech, CMU Mocap, OpenGameArt | models/HDRI/textures/SFX/music/footage/mocap | none needed | ✅ no account required | Direct download. |
| Pixabay | SFX/music/footage | — | ⏸ optional | Registration has reCAPTCHA + Turnstile; downloads work without account for most files. |
| Zapsplat, ProductionCrate, Rokoko, ActorCore, Ready Player Me, Videvo | secondary sources | — | ⏸ not attempted | All use CAPTCHA at signup; owner can create in 1 minute each if needed. |

## Procedure for a new agent registering somewhere
1. Check the table above first. 2. Use the email above; generate a unique strong password; store it in the private credentials store (not chat). 3. Poll Gmail for the verification mail, click the link/enter the code. 4. Add a row here and commit. 5. If a CAPTCHA appears, stop and ask the owner to complete it — do not try to bypass it.
