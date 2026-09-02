# "PAN" — cartoon horror short (v2 final, 2026-09-02) — APPROVED & rendered

> v1 was a realistic-cast draft; the owner asked "اجعله كرتونيا" → cartoon look: Cycles + **Toon BSDF** on every material + **Freestyle outlines** (thickness 2.5) + AgX High Contrast. Final: 76 s = 1824 frames (72 s film + 4 s credits). Rendered on the Beam farm (3 accounts), last ~105 frames of shot 9 rendered locally on CPU because all Beam tokens became invalid mid-job (see `docs/beam_cloud.md`).

Premise: the boy who never grows up never grew up because he feeds on children. Public‑domain source (J. M. Barrie, 1911); no Disney names, designs or music. Non‑graphic: everything is implied (shadows, sound, empty bed).
Target: 72 s + 4 s credits = 1824 frames @ 24 fps, 1920×1080, Cycles/OptiX 64 spp, Toon shading. Actual: build → 480p preview stills (approved) → farm render → CPU fill-in → mix.

## Cast (Mixamo stylized characters — cartoon version, per owner)
| Role | Asset | Mixamo id | Why |
|---|---|---|---|
| Pan | **Timmy** | `2312e946-b71e-4b25-b61e-4f51803aa884` | cartoon boy; re‑materialed pale skin, dark‑green ragged clothes, black eyes |
| Pan — true face (2‑frame flash, frames 1000–1001) | **Goblin** | `130a335c-bbdb-492f-971f-8faab0616b6e` | free monster template |
| The child (Wendy‑type) | **Amy** | `24c3eeb4-6c47-419d-a593-f7b2948b74c7` | under the "Blanket" object until shot 6 |
| Mother (final shot) | **Michelle** | `7f3f4e32-2b70-4c69-9a3d-0bdac6188241` | Walking clip has root motion — compensate |

Full animation list with ids: `/assets manifest` produced by `download_mixamo.py` (`pan_manifest.json`).

## Frame plan (24 fps)
S1 1–192 title (post) · S2 193–432 · S3 433–624 · S4 625–864 · S5 865–1056 (flash 1000–1001) · S6 1057–1248 · S7 1249–1344 black (post) · S8 1345–1584 · S9 1585–1728 · credits 1729–1824 (post).

Animations (Mixamo): Sneak Walk, Crouch Idle, Crouched Walk, Head Turn/Look Around, Reaching, Sitting Up / Waking Up, Standing Idle, Kneeling, Scream (mother), Standing Up.

## Set (Poly Haven, CC0)
Victorian child's bedroom: `GothicBed_01`, `WoodenChair_01`, `wooden_table_02`, `Rockingchair_01`, `brass_candleholders`, `vintage_oil_lamp`, `ornate_mirror_01`, `mantel_clock_01`, `decorative_book_set_01`, `rubber_duck_toy`, `throw_pillows_01`, `Chandelier_02`. Textures `old_wood_floor`, `decrepit_wallpaper`, `damaged_plaster`. Window = framed opening in the wall (Poly Haven has no curtains → simple animated cloth plane with `denim_fabric` swapped for a light fabric). HDRI outside: `rogland_moonlit_night` / `moonlit_golf`. Final exterior: `rooftop_night` + `dead_tree_trunk_02`.

## Shots
| # | Time | Picture | Sound / narration (Arabic VO, ElevenLabs multilingual) |
|---|---|---|---|
| 1 | 0–8 s | Black. Title "PAN" fades in as thin white text, flickers, fades. | Low drone. VO: "كل ما قرأتموه عن الصبي الذي لا يكبر… كان كذبة." |
| 2 | 8–18 | Slow push‑in on moonlit bedroom. Lump under the blanket (child). Clock ticks. Candle burning. | Clock, wind. VO: "الأمهات كنّ يقلن إنه يأخذ الأطفال إلى أرضٍ لا يكبر فيها أحد." |
| 3 | 18–26 | Window latch clicks open by itself; curtain lifts; candle flame leans and dies. Shadow of a small figure grows on the wallpaper. | Latch click, wind gust, whisper‑like breath. |
| 4 | 26–36 | Pan crouched on the sill, silhouetted against the moon. Head tilts slowly. Drops in without sound. Sneak‑walk toward bed. | Floor creak ×2. VO: "لم يكن يطير. كان يتسلّق." |
| 5 | 36–44 | Close‑up: pale face, black eyes catch moonlight, slow smile. **2‑frame flash** of the true face (Goblin) on a thunder‑less light pulse. | Sub‑bass hit on flash. VO: "ولم يكن صبيًا." |
| 6 | 44–52 | Child sits up in silhouette. Pan kneels, extends hand. Camera drifts behind him. Mirror in background shows **no reflection of Pan**. | Music swells then cuts. VO: "أرض الأحلام كانت جوعه." |
| 7 | 52–56 | Hard cut to black. | Only sound: a small gasp, fabric, then silence. |
| 8 | 56–66 | Morning. Same room, grey daylight. Bed empty, blanket on floor, window open, small shoes by the bed, one green leaf on the pillow. Mother enters, stops, kneels. | Birds far away. VO: "وفي الصباح، لا يبقى إلا سرير فارغ… وورقة خضراء." |
| 9 | 66–72 | Exterior night rooftop, Pan silhouette against the moon, turns to camera. Cut. Title "PAN" + credits card. | Wind; single child‑laugh (pitched down). VO whisper: "وما زال… لا يكبر." |

## Sound sources
Mixkit (no account): horror/creepy ambiences, wind, door latch, floor creak, clock tick, heartbeat, sub‑hit. Music: Incompetech (Kevin MacLeod, CC‑BY) dark ambient track, or Mixkit free music. VO: ElevenLabs via agent tooling (`eleven_multilingual_v2`, Arabic).

## Gates
1. Owner approves this storyboard → 2. Build scene, render 6 key stills at 480p for approval → 3. Farm render on Beam (3 accounts, ~1700 frames) → 4. Mix, deliver, commit to `examples/pan/`.
