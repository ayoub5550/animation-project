# Free asset sources for game / animation-film assembly (curated 2026-09-02)

Rule: prefer CC0 → then CC-BY (auto-write CREDITS.md) → read each file's license before download. Always render a thumbnail of a character before using it (asset names lie — "Survivor" on Mixamo looked like a zombie).

| Category | Sources | License notes |
|---|---|---|
| Realistic characters + motion | Mixamo (best free), Sketchfab (filter Downloadable + CC), CGTrader/TurboSquid free, Ready Player Me | Mixamo: use in projects only, no redistribution. Sketchfab per-file CC0/CC-BY |
| Extra mocap | Rokoko Motion Library (partial free), CMU Mocap (2500 clips, unrestricted, needs retarget), ActorCore samples | |
| Environments / props | Poly Haven (CC0 models+HDRI+textures), Sketchfab, BlenderKit free tier, Fab/Quixel Megascans (free, Fab standard license), Godot Asset Library, itch.io, OpenGameArt | Poly Haven safest |
| Textures | ambientCG (CC0), Poly Haven (CC0), 3dtextures.me | |
| SFX | Freesound (CC0/CC-BY), Pixabay SFX, Sonniss GDC bundles (royalty-free), Zapsplat, Mixkit | BBC Sound Effects = personal/educational only — avoid for commercial |
| Music | Pixabay Music, Free Music Archive, Incompetech (CC-BY), YouTube Audio Library, Mixkit | |
| VFX overlays | ProductionCrate free tier, Pixabay/Pexels/Mixkit videos, Kenney Particle Pack (CC0), engine particles | composite with ffmpeg or in-engine |
| Stock footage | Pexels, Pixabay, Mixkit, Videvo | commercial OK |
| Voice | Viktor TTS tool (general_tools); lip sync via Rhubarb Lip Sync (needs face blend shapes — Mixamo models have none) | |
| Fonts | Google Fonts (good Arabic) | OFL |
| Tools | Godot (scenes + `--write-movie`), Blender (better lighting/compositing), ffmpeg | OSS |

## GPU rendering services (researched 2026-09-02)
Agent needs API/SSH control, not a click UI.
| Service | Cost | Automatable | Note |
|---|---|---|---|
| Vast.ai | RTX 3090 ≈ $0.20/h, RTX 4090 ≈ $0.29/h | ✅ CLI + SSH | cheapest; prepaid; owner gives API key |
| RunPod | RTX 3090 $0.22, RTX 4090 $0.34 (Community) | ✅ API + SSH | more stable |
| Kaggle | free ~30 GPU h/week (T4/P100), 12 h sessions | ✅ Kaggle API (`kaggle kernels push`) | best free option; owner provides kaggle.json |
| Lightning AI | free 15 credits/mo (≈22–80 GPU h) | ✅ SSH | phone verification → owner signs up |
| SheepIt | free volunteer farm | ✅ | Blender only |
| Google Colab | free, unpublished limits | ⚠️ forbids non-interactive use | avoid |
On GPU: Godot Forward+ works (fog/GI/shadows), 10–20× faster; 5-min film ≈ 10 min render.

## GPU rendering (decided 2026-09-02)
| Service | Use | Notes |
|---|---|---|
| **Beam.cloud** | primary — serverless RTX 4090, ~$0.69/h, per-second billing | `docs/beam_cloud.md`, `pipeline/beam_farm.py` |
| SheepIt | free fallback, permanent client on VPS | `docs/sheepit.md` |

## Sound sources actually used in the test film
| Asset | Source | Licence |
|---|---|---|
| Night crickets ambience (sfx 1783) | https://mixkit.co/free-sound-effects/night/ | Mixkit Free License (no account) |
| Footsteps on pavement (sfx 537) | https://mixkit.co/free-sound-effects/footsteps/ | Mixkit Free License |
Mixkit preview MP3s are downloadable directly: `https://assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3` (ids are in the page HTML as `data-audio-player-item-id-value`).

## Sound sources used in "PAN" (2026-09-02)
Mixkit, all no-account: music `https://assets.mixkit.co/music/671/671.mp3` ("Piano Horror"); SFX ids 2484, 1143, 561 (horror), 2658 (wind), 337 (creak), 1059 (clock), 492 (heartbeat), 2472 (birds), 1489 (whoosh) via the preview-MP3 URL pattern above. Narration: ElevenLabs multilingual v2 (Arabic).
Characters: Mixamo stylized set (Timmy, Goblin, Amy, Michelle) — ids in `films/pan/STORYBOARD.md`. Props/HDRIs: Poly Haven via `pipeline/polyhaven_download.py`.
