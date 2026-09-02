# animation-project — AI‑agent playbook for assembling 3D animation films from free assets

Owner: **ayoub5550** · Contact mailbox for all service accounts: `ayoubteke12@gmail.com`
Maintained by AI agents (first author: Viktor, 2026‑09‑02). **Any agent working on this project must read this file first, then `RULES.md`.**

## Purpose
Produce short animated films (and game prototypes) by **collecting, arranging and coordinating existing free assets** — never by modelling, animating, composing or drawing from scratch.

## Repository map
| Path | What it is |
|---|---|
| `RULES.md` | Non‑negotiable working rules given by the owner. Read before anything else. |
| `ACCOUNTS.md` | Which services have accounts, registered with which email/username, and how to get in (verification codes arrive in the owner's Gmail). Passwords live in `SECRETS.md` **only when the repo is private** — see note there. |
| `SOURCES.md` | Curated free asset sources per category with license notes. |
| `docs/pipeline.md` | The exact method, step by step: asset acquisition → Godot scene → scripted camera → headless frame rendering → ffmpeg encode. |
| `docs/mixamo_api.md` | Mixamo internal API: endpoints, headers, export body, polling. |
| `docs/lessons.md` | Mistakes already made and how to avoid them. Append, never delete. |
| `pipeline/` | Reusable scripts (Mixamo downloader, Godot character builder, render + encode). |
| `CREDITS_TEMPLATE.md` | Template for the per‑film credits file (license compliance). |

## Quick start for a new agent
1. Read `RULES.md`, `ACCOUNTS.md`, `docs/lessons.md`.
2. Get the film brief from the owner (idea, duration, style). Write a scene‑by‑scene script + asset list **before** downloading anything.
3. For every asset: find it free (see `SOURCES.md`), check license, download, log it in the film's `CREDITS.md`.
4. Render a **thumbnail of every character/prop and show the owner** before building scenes.
5. Build in Godot 4.x, render with `pipeline/render_movie.sh`, deliver MP4 + project zip.
6. Append anything learned to `docs/lessons.md` and commit.

- **Rendering:** `docs/sheepit.md` (SheepIt — free, current renderer) or local Blender CPU. `docs/beam_cloud.md` is **deprecated** (Beam disabled the accounts 2026-09-02) and kept only as a reference for building a serverless-GPU farm; scripts `pipeline/render_beam.py`, `pipeline/beam_farm.py` are the reference implementation.

- **Reference example:** `examples/street_night/` — the first finished test film (video + contact sheet). Quality floor and proof the method works.
- **Second film:** `examples/pan/` — 76 s cartoon horror short "PAN" (storyboard → templates → farm render). Story/storyboard **first**, then pick templates for each shot — the owner's rule after Street Night. Build script + storyboard in `films/pan/`.
