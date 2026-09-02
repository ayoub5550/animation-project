#!/bin/bash
cd "$(dirname "$0")"
for h in moonlit_golf kloppenheim_07_puresky dikhololo_night; do uv run python polyhaven.py hdri $h 2k; done
for m in old_bed_frame vintage_day_bed Rockingchair_01 vintage_oil_lamp wooden_candlestick vintage_grandfather_clock_01 fancy_picture_frame_01 decorative_book_set_01 wooden_bookshelf_worn painted_wooden_chair_01 rollershutter_window_01 \
         pine_tree_01 fir_tree_01 dead_tree_trunk dead_tree_trunk_02 tree_stump_01 rock_moss_set_01 fern_02 pine_roots boulder_01 wooden_lantern_01 pine_sapling_medium; do uv run python polyhaven.py model $m 2k; done
for t in decrepit_wallpaper wood_floor damaged_plaster brown_mud_leaves_01 dry_decay_leaves weathered_planks; do uv run python polyhaven.py texture $t 2k; done
echo ASSETS_DONE
