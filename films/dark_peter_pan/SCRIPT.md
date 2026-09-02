# «الطفل الذي لا يكبر» — Dark Peter Pan (working title)
Short horror film, ~60 s, 1920×1080, 24 fps, Cycles (CPU, local). Arabic narration (fusha), no dialogue (Mixamo has no faces).
Based only on J.M. Barrie's public-domain texts (The Little White Bird 1902, Peter and Wendy 1911). No Disney designs, no green tunic/feather cap.

## Story spine (from Barrie, all verifiable)
- Peter escaped as a 7-day-old baby through a window; "Lock-out time": when he came back the bars were up and his mother held another boy.
- Peter buries children who die in Kensington Gardens in a hidden graveyard (Little White Bird).
- Mrs Darling says Peter goes "part of the way" with dead children so they are not afraid → psychopomp.
- "When they seem to be growing up, which is against the rules, Peter thins them out." (Peter and Wendy, ch. 5)
- Peter forgets everything — Tinker Bell, Hook, Wendy. Ending: he returns for Jane, then Margaret, "so long as children are gay and innocent and heartless."

## Scenes
| # | s | Location / asset | Characters (Mixamo) | Action / camera | Sound | Narration (AR) |
|---|---|---|---|---|---|---|
| 1 | 0–9 | Victorian nursery at night: room built from Poly Haven wood/plaster textures + window; bed + props (Poly Haven / BlenderKit free) | none (empty bed) | Slow push-in on an open window, curtains moving (cloth sim or keyframed), moonlight shaft, empty bed | wind, creaking window, distant clock | «كل ليلة، تُفتح نافذةٌ ما في لندن… ولا يعود الطفل.» |
| 2 | 9–20 | Foggy night forest (Poly Haven HDRI moonlit night + pine/tree models CC0, volumetric fog) | PETER (slim youth) back to camera, motionless | Camera creeps behind him; at 17 s his head turns slowly toward us (Mixamo "Look Over Shoulder" / "Idle") | crickets, low drone | «في الجزيرة التي لا تكبر فيها الأشياء… كان هناك ولد. اسمه بيتر.» |
| 3 | 20–31 | Hidden graveyard: clearing with small wooden crosses / stones (Poly Haven rocks + planks), lantern | PETER kneeling (Mixamo "Kneeling" / "Praying") | Wide → slow tilt down to small graves; lantern flickers | shovel scrape, wind | «الأطفال الذين يسقطون من عرباتهم… كان يدفنهم بيده. قال بارّي: كان يرافق الموتى الصغار جزءاً من الطريق كي لا يخافوا.» |
| 4 | 31–44 | Forest path | LOST BOY (taller adolescent) running; PETER walking calmly behind (Mixamo "Running", "Walking" inplace) | Two shots: boy runs toward camera looking back; cut to Peter walking slowly, blade catching moonlight; cut to black on a single footstep | running footsteps, breath, one sharp sound, silence | «كان للجزيرة قانون واحد: لا أحد يكبر. ومن بدا عليه أنه يكبر…» (pause) «… كان بيتر "يُقلّل عددهم".» |
| 5 | 44–54 | Nursery again, years later | WENDY (adult woman, Mixamo) at window | Adult Wendy looks out; reflection/figure of PETER outside in fog, head tilted; he does not react — he doesn't remember her | glass tap, heartbeat | «وعندما عادت ويندي إليه كبيرة… لم يعرفها. بيتر لا يتذكر أحداً. لا الأصدقاء، ولا الأعداء، ولا من دفنهم.» |
| 6 | 54–62 | Nursery, new child's bed | none | Small bed, a child's shoes; the window unlatches by itself; curtains blow; fade to black, title card | window latch, wind, silence | «وهكذا سيستمر الأمر… ما دام الأطفال مرحين، وأبرياء، وبلا قلب.» — then title: «الطفل الذي لا يكبر» |

## Asset list (all free, licence logged in CREDITS.md)
- Mixamo: PETER (slim youth, realistic — candidates to thumbnail: search "boy", "teen", "kid"), LOST BOY (adolescent), WENDY (adult woman). Clips: Idle, Look Around/Over Shoulder, Kneeling Idle, Running (inplace), Walking (inplace), Standing Idle Looking.
- Poly Haven CC0: HDRI moonlit night (e.g. `moonless_golf`/`kloppenheim_06` night variants), textures wood_floor, plaster, tree/pine models, rocks, planks, lantern, bed if available.
- BlenderKit free (account exists): bed / nursery props if Poly Haven lacks them.
- Mixkit: wind, crickets, footsteps, heartbeat, creaking door; music: low drone (Mixkit / Pixabay).
- Narration: ElevenLabs TTS Arabic (eleven_multilingual_v2), deep male voice.

## Render budget (local, 17 CPU cores)
1488 frames × ~30–60 s ≈ 12–24 h at 1080p / 48 samples + denoise. Alternative 720p ≈ 6–9 h. Scenes 1 & 6 share one set; 2/3/4 share the forest set → 3 .blend files.
