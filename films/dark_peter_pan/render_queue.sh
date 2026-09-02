#!/bin/bash
# Local CPU render queue: rebuild each shot's .blend, then render all frames to render/<shot>/####.png
# Usage: nohup bash render_queue.sh > ../render/queue.log 2>&1 &
# Env: SAMPLES (default 32), RES_X/RES_Y (default 1920x1080). Skips frames already on disk.
set -u
cd "$(dirname "$0")"
P=/work/projects/dark_peter_pan
BL="env LIBGL_ALWAYS_SOFTWARE=1 /work/tools/blender/blender -b"
SAMPLES=${SAMPLES:-32}; RES_X=${RES_X:-1920}; RES_Y=${RES_Y:-1080}
SHOTS=${SHOTS:-"s1_window s2_forest s3_graves s4a_run s4b_walk s5_wendy s6_bed"}
for s in $SHOTS; do
  echo "=== $(date -u +%FT%TZ) BUILD $s"
  $BL -P build_shot.py -- $s > $P/render/build_$s.log 2>&1 || { echo "BUILD FAILED $s"; continue; }
  mkdir -p $P/render/$s
  echo "=== $(date -u +%FT%TZ) RENDER $s"
  $BL $P/blend/$s.blend --python-expr "
import bpy; sc=bpy.context.scene
sc.render.resolution_x,sc.render.resolution_y=$RES_X,$RES_Y; sc.cycles.samples=$SAMPLES
sc.render.use_overwrite=False; sc.render.use_placeholder=True
sc.render.filepath='$P/render/$s/'" -a 2>&1 | grep -E "^Saved|Time:|Error|error" 
  echo "=== $(date -u +%FT%TZ) DONE $s ($(ls $P/render/$s | wc -l) frames)"
done
echo "=== ALL DONE $(date -u +%FT%TZ)"
