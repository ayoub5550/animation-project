# «الطفل الذي لا يكبر» — realistic dark Peter Pan short (2026-09-02)

Second Pan film, **realistic style** (the first, `films/pan`, is the cartoon version). Script: `SCRIPT.md` (62 s, 6 scenes, Arabic VO). Cast approved by the owner from `casting_sheet.jpg`; shot previews in `frame_board.jpg`.

## Pipeline (all scripted, no hand work)
| Step | Script | Notes |
|---|---|---|
| Cast + clips | `download_cast.py` + `mixamo_api.py` | Mixamo token from browser session (`MIXAMO_TOKEN_FILE`). Bryce / Lewis / Kate. |
| Assets | `fetch_assets.sh` → `polyhaven.py` | CC0 HDRIs, GLTF props, PBR textures |
| Thumbnails | `thumb_character.py` | RULES §6 — show the cast before rendering |
| Narration | ElevenLabs TTS (agent tooling), verified back with STT | `audio/narr_1..6.mp3` |
| Sound mix | `mix_audio.py` | 22 cues (Mixkit ids in `sfx_list.tsv`) → `audio/mix.wav`, −24 dB mean / −6 dB peak |
| Shots | `build_shot.py <shot> [preview_frame]` + `film_lib.py` | 7 blends: s1_window 216f · s2_forest 264 · s3_graves 264 · s4a_run 144 · s4b_walk 120 · s5_wendy 240 · s6_bed 192 |
| Render | `render_queue.sh` | local CPU queue, skips existing frames; `SAMPLES`/`RES_X`/`RES_Y` env |

Beam.cloud is gone (see `docs/lessons.md`). Renderers now: local CPU (sandbox), SheepIt (client earning points in the background), owner's AMD Developer Cloud credit when he provides access.
