"""Build one shot of the Dark Peter Pan film and save a packed .blend (+ optional preview frame).
usage: blender -b -P build_shot.py -- <shot> [preview_frame]
shots: s1_window s2_forest s3_graves s4a_run s4b_walk s5_wendy s6_bed"""
import bpy, sys, math, random, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import film_lib as L
from mathutils import Vector

OUT = "/work/projects/dark_peter_pan/blend"
PREV = "/work/projects/dark_peter_pan/preview"
args = sys.argv[sys.argv.index("--") + 1:]
SHOT = args[0]; PREVIEW = int(args[1]) if len(args) > 1 else None
FRAMES = {"s1_window": 216, "s2_forest": 264, "s3_graves": 264, "s4a_run": 144, "s4b_walk": 120, "s5_wendy": 240, "s6_bed": 192}


def ground_obj(root, objs, z=0.0):
    lo, hi = L.bbox_dims(objs); root.location.z += z - lo.z; return hi - lo


# ============================ NURSERY SET ============================
def nursery():
    """Victorian nursery 5x4x3 m. Window in the +Y wall. Returns dict of key objects."""
    wallp = L.pbr_material("Wallpaper", "decrepit_wallpaper", scale=2.0, tint=(0.55, 0.5, 0.45))
    floor = L.pbr_material("Floor", "wood_floor", scale=3.0, tint=(0.6, 0.55, 0.5))
    plaster = L.pbr_material("Ceiling", "damaged_plaster", scale=2.0, tint=(0.5, 0.5, 0.5))
    wood = L.pbr_material("FrameWood", "wood_floor", scale=1.0, tint=(0.25, 0.2, 0.15))
    W, D, H = 5.0, 4.0, 3.0
    L.plane("Floor", (W, D), (0, 0, 0), mat=floor)
    L.plane("Ceiling", (W, D), (0, 0, H), rot=(math.pi, 0, 0), mat=plaster)
    L.plane("Wall_-Y", (W, H), (0, -D / 2, H / 2), rot=(math.pi / 2, 0, 0), mat=wallp)
    L.plane("Wall_-X", (D, H), (-W / 2, 0, H / 2), rot=(math.pi / 2, 0, math.pi / 2), mat=wallp)
    L.plane("Wall_+X", (D, H), (W / 2, 0, H / 2), rot=(math.pi / 2, 0, -math.pi / 2), mat=wallp)
    # +Y wall with window hole x[-0.6,0.6] z[0.9,2.3]
    y = D / 2; wx0, wx1, wz0, wz1 = -0.6, 0.6, 0.9, 2.3
    L.box("WallY_L", ((W / 2 + wx0), 0.12, H), ((-W / 2 + wx0) / 2, y + 0.06, H / 2), mat=wallp)
    L.box("WallY_R", ((W / 2 - wx1), 0.12, H), ((W / 2 + wx1) / 2, y + 0.06, H / 2), mat=wallp)
    L.box("WallY_B", (wx1 - wx0, 0.12, wz0), (0, y + 0.06, wz0 / 2), mat=wallp)
    L.box("WallY_T", (wx1 - wx0, 0.12, H - wz1), (0, y + 0.06, (H + wz1) / 2), mat=wallp)
    # frame + sill
    t = 0.06
    L.box("Sill", (wx1 - wx0 + 0.3, 0.25, 0.05), (0, y - 0.02, wz0 - 0.025), mat=wood)
    for x in (wx0 - t / 2, wx1 + t / 2): L.box("Jamb", (t, 0.14, wz1 - wz0), (x, y + 0.06, (wz0 + wz1) / 2), mat=wood)
    L.box("Head", (wx1 - wx0 + 2 * t, 0.14, t), (0, y + 0.06, wz1 + t / 2), mat=wood)
    # two casement sashes hinged at the jambs, opening outward (+Y)
    glass = bpy.data.materials.new("Glass"); glass.use_nodes = True
    g = glass.node_tree.nodes["Principled BSDF"]; g.inputs["Transmission Weight"].default_value = 1.0
    g.inputs["Roughness"].default_value = 0.05; g.inputs["Base Color"].default_value = (0.8, 0.9, 1, 1)
    # let the moon pass: transparent for shadow rays (no fake caustic shadows)
    gnt = glass.node_tree; gout = gnt.nodes["Material Output"]; lp = gnt.nodes.new("ShaderNodeLightPath")
    tr = gnt.nodes.new("ShaderNodeBsdfTransparent"); mx = gnt.nodes.new("ShaderNodeMixShader")
    gnt.links.new(g.outputs["BSDF"], mx.inputs[1]); gnt.links.new(tr.outputs["BSDF"], mx.inputs[2])
    gnt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs["Fac"]); gnt.links.new(mx.outputs["Shader"], gout.inputs["Surface"])
    sashes = []
    for side, hx in (("L", wx0), ("R", wx1)):
        piv = bpy.data.objects.new(f"Sash_{side}", None); bpy.context.scene.collection.objects.link(piv)
        piv.location = (hx, y + 0.1, (wz0 + wz1) / 2)
        sgn = 1 if side == "L" else -1
        w = (wx1 - wx0) / 2
        hh = wz1 - wz0
        parts = [L.box(f"SashV_{side}a", (0.05, 0.04, hh), (sgn * 0.025, 0, 0), mat=wood),
                 L.box(f"SashV_{side}b", (0.05, 0.04, hh), (sgn * (w - 0.025), 0, 0), mat=wood),
                 L.box(f"SashH_{side}a", (w, 0.04, 0.05), (sgn * w / 2, 0, hh / 2 - 0.025), mat=wood),
                 L.box(f"SashH_{side}b", (w, 0.04, 0.05), (sgn * w / 2, 0, -hh / 2 + 0.025), mat=wood),
                 L.box(f"Bar_{side}", (w, 0.045, 0.03), (sgn * w / 2, 0, 0), mat=wood),
                 L.plane(f"Glass_{side}", (w - 0.08, hh - 0.08), (sgn * w / 2, 0, 0), rot=(math.pi / 2, 0, 0), mat=glass)]
        for o in parts: o.parent = piv
        sashes.append(piv)
    # curtains: two planes with Wave modifier
    cloth = bpy.data.materials.new("Curtain"); cloth.use_nodes = True
    cb = cloth.node_tree.nodes["Principled BSDF"]; cb.inputs["Base Color"].default_value = (0.75, 0.7, 0.6, 1)
    cb.inputs["Roughness"].default_value = 0.9; cb.inputs["Sheen Weight"].default_value = 0.5
    cnt = cloth.node_tree; cout = cnt.nodes["Material Output"]; tl = cnt.nodes.new("ShaderNodeBsdfTranslucent")
    tl.inputs["Color"].default_value = (0.75, 0.7, 0.6, 1); cmx = cnt.nodes.new("ShaderNodeMixShader"); cmx.inputs["Fac"].default_value = 0.45
    cnt.links.new(cb.outputs["BSDF"], cmx.inputs[1]); cnt.links.new(tl.outputs["BSDF"], cmx.inputs[2]); cnt.links.new(cmx.outputs["Shader"], cout.inputs["Surface"])
    curtains = []
    for side, cx in (("L", wx0 - 0.15), ("R", wx1 + 0.15)):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=12, y_subdivisions=40, size=1, location=(cx, y - 0.25, (wz1 + 0.15 + 0.5) / 2))
        c = bpy.context.object; c.name = f"Curtain_{side}"; c.rotation_euler = (math.pi / 2, 0, 0)
        c.scale = (0.7, wz1 + 0.15 - 0.5, 1); bpy.ops.object.transform_apply(scale=True, rotation=True)
        c.data.materials.append(cloth)
        wv = c.modifiers.new("Wave", "WAVE"); wv.use_normal = False; wv.height = 0.12; wv.width = 0.8; wv.narrowness = 1.2
        wv.speed = 0.25; wv.start_position_x = cx; wv.use_x = True; wv.use_y = False
        wv.time_offset = random.uniform(0, 40)
        curtains.append(c)
    L.box("Rod", (wx1 - wx0 + 0.8, 0.03, 0.03), (0, y - 0.25, wz1 + 0.2), mat=wood)
    # props (Poly Haven CC0)
    r, o = L.import_gltf("old_bed_frame", (0.35, -0.5, 0), rot_z=0); dims = ground_obj(r, o)
    bed = r
    r, o = L.import_gltf("Rockingchair_01", (-1.7, 1.3, 0), rot_z=math.radians(150)); ground_obj(r, o)
    r, o = L.import_gltf("vintage_grandfather_clock_01", (-2.2, 1.75, 0), rot_z=0); ground_obj(r, o)
    r, o = L.import_gltf("wooden_bookshelf_worn", (-2.32, -0.8, 0), rot_z=math.pi / 2); ground_obj(r, o)
    r, o = L.import_gltf("painted_wooden_chair_01", (2.1, -0.2, 0), rot_z=math.radians(-70)); cdims = ground_obj(r, o)
    r, o = L.import_gltf("vintage_oil_lamp", (2.1, -0.2, cdims.z), rot_z=0); ground_obj(r, o, cdims.z); lamp = r
    r, o = L.import_gltf("wooden_candlestick", (2.2, -1.5, 0), rot_z=0); ground_obj(r, o)
        # lights: moon through the window (sun from +Y, high), faint lamp glow
    L.world_hdri(f"{L.PH}/hdris/dikhololo_night_2k.hdr", strength=1.0, rotation=math.radians(90), tint=(0.5, 0.6, 0.9))
    L.sun((1.0, 12, 4.5), energy=9.0, color=(0.55, 0.68, 1.0), angle=0.8)
    lampL = L.point((2.1, -0.2, cdims.z + 0.25), energy=3, color=(1.0, 0.55, 0.25), radius=0.05, name="LampLight")
    L.fog_box((0, 0.5, 1.5), (5, 4, 3), density=0.04, color=(0.6, 0.7, 0.9))
    return {"sashes": sashes, "curtains": curtains, "bed": bed, "lamp": lampL, "win": Vector((0, y, (wz0 + wz1) / 2))}


def open_sashes(sashes, f0, f1, deg=(55, 40)):
    for piv, d, sgn in zip(sashes, deg, (1, -1)):
        piv.rotation_euler = (0, 0, 0); piv.keyframe_insert("rotation_euler", frame=f0)
        piv.rotation_euler = (0, 0, sgn * math.radians(d)); piv.keyframe_insert("rotation_euler", frame=f1)
        L.smooth_keys(piv)


# ============================ FOREST SET ============================
def forest(seed=7, radius=30, n_trees=55, clearing=4.0):
    random.seed(seed)
    ground = L.pbr_material("ForestGround", "brown_mud_leaves_01", scale=12.0, tint=(0.5, 0.5, 0.45))
    L.plane("Ground", (2 * radius + 20, 2 * radius + 20), (0, 0, 0), mat=ground)
    # Poly Haven tree assets are SETS of several trees (parts a/b/c offset from origin) -> use each part as its own tree
    parts = []
    for aid in ("pine_tree_01", "fir_tree_01"):
        r, o = L.import_gltf(aid, (0, 0, -50))
        for m in [m for m in o if m.type == "MESH"]:
            bb = [m.matrix_world @ Vector(c) for c in m.bound_box]
            cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2; cy = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
            parts.append((m, cx, cy))
    placed = 0; tries = 0
    while placed < n_trees and tries < 2000:
        tries += 1
        x, y = random.uniform(-radius, radius), random.uniform(-radius, radius)
        if math.hypot(x, y) < clearing or abs(x) < 3.2:  # keep a corridor along the Y axis free (camera/character path)
            continue
        m, cx, cy = random.choice(parts)
        e = bpy.data.objects.new(f"Tree_{placed}", None); bpy.context.scene.collection.objects.link(e)
        inst = bpy.data.objects.new(m.name + f"_{placed}", m.data); bpy.context.scene.collection.objects.link(inst)
        inst.parent = e; inst.location = (-cx, -cy, 0)
        e.location = (x, y, 0); e.rotation_euler = (0, 0, random.uniform(0, 6.28)); s = random.uniform(0.8, 1.35); e.scale = (s, s, s)
        placed += 1
    for aid, n in (("dead_tree_trunk", 3), ("dead_tree_trunk_02", 3), ("tree_stump_01", 4), ("rock_moss_set_01", 1), ("fern_02", 14), ("boulder_01", 2), ("pine_roots", 3)):
        for i in range(n):
            minx = 7.0 if aid in ("rock_moss_set_01", "boulder_01") else 3.0  # keep the path along Y free of props
            while True:
                ang = random.uniform(0, 6.28); d = random.uniform(2.5, 14)
                if abs(d * math.cos(ang)) >= minx: break
            r, o = L.import_gltf(aid, (d * math.cos(ang), d * math.sin(ang), 0), rot_z=random.uniform(0, 6.28), name=f"{aid}_{i}")
            ground_obj(r, o)
    L.world_hdri(f"{L.PH}/hdris/kloppenheim_07_puresky_2k.hdr", strength=0.5, tint=(0.45, 0.55, 0.85))
    L.sun((-6, -10, 9), energy=1.2, color=(0.6, 0.72, 1.0), angle=1.5)
    L.fog_box((0, 0, 4), (2 * radius + 20, 2 * radius + 20, 9), density=0.045, color=(0.5, 0.6, 0.75), anisotropy=0.5)


# ============================ SHOTS ============================
def s1_window(sc):
    N = nursery()
    open_sashes(N["sashes"], 1, 1, deg=(60, 45))
    L.flicker(N["lamp"], 1, sc.frame_end, 6, amp=0.4)
    cam, tgt = L.camera((-1.7, -1.7, 1.6), (0.2, 0.9, 0.8), lens=28, fstop=5.6)
    L.key(cam, 1, (-1.8, -1.75, 1.65)); L.key(cam, sc.frame_end, (-0.9, -0.6, 1.35)); L.key(tgt, 1, (0.2, 0.9, 0.7)); L.key(tgt, sc.frame_end, (0, 2.0, 1.3)); L.smooth_keys(tgt); L.smooth_keys(cam)


def s6_bed(sc):
    N = nursery()
    open_sashes(N["sashes"], 90, 170, deg=(60, 45))
    L.flicker(N["lamp"], 1, sc.frame_end, 4, amp=0.5)
    cam, tgt = L.camera((1.2, -1.6, 0.9), (1.4, 0.4, 0.5), lens=40, fstop=2.0)
    L.key(tgt, 1, (1.4, 0.4, 0.5)); L.key(tgt, 80, (1.4, 0.4, 0.5)); L.key(tgt, 150, N["win"] + Vector((0, -0.3, -0.1)))
    L.key(cam, 1, (1.2, -1.6, 0.9)); L.key(cam, 80, (1.0, -1.7, 1.0)); L.key(cam, sc.frame_end, (0.2, -1.9, 1.3))
    L.smooth_keys(cam); L.smooth_keys(tgt)


def s5_wendy(sc):
    N = nursery()
    open_sashes(N["sashes"], 1, 1, deg=(60, 45))
    L.flicker(N["lamp"], 1, sc.frame_end, 8, amp=0.3)
    # Wendy stands at the window looking out; Peter outside in the fog, motionless, head slightly turning
    L.character("Kate", ["Standing_Idle", "Look_Around_Nerv"], [("Standing_Idle", 1), ("Look_Around_Nerv", 1)], loc=(-0.15, 1.35, 0), rot_z=math.radians(5), name="Wendy")
    L.character("Bryce", ["Breathing_Idle", "Looking_Behind"], [("Breathing_Idle", 2), ("Looking_Behind", 1)], loc=(0.25, 4.6, 0), rot_z=math.radians(200), darken=("Shirt", "Shorts", "Sneakers"), name="Peter")
    # a ground outside the window + denser fog outside
    L.plane("Outside", (30, 30), (0, 15, 0), mat=bpy.data.materials["Floor"])
    L.fog_box((0, 8, 2), (30, 12, 5), density=0.09, color=(0.5, 0.6, 0.8))
    L.point((0.35, 5.4, 1.7), energy=25, color=(0.6, 0.7, 1.0), radius=0.35, name="PeterRim")
    cam, tgt = L.camera((0.9, -1.4, 1.5), (-0.1, 1.6, 1.4), lens=45, fstop=2.2)
    L.key(cam, 1, (1.1, -1.6, 1.5)); L.key(cam, sc.frame_end, (0.4, -0.3, 1.45)); L.smooth_keys(cam)


def s2_forest(sc):
    forest()
    # Peter stands with his back to camera; at ~17 s (frame 190) he looks behind
    arm, meshes, _ = L.character("Bryce", ["Breathing_Idle", "Looking_Behind"], [("Breathing_Idle", 3, 1), ("Looking_Behind", 1, 175)], loc=(0, 2.0, 0), rot_z=math.radians(180 + 15), darken=("Shirt", "Shorts", "Sneakers"), name="Peter")
    r, o = L.import_gltf("wooden_lantern_01", (0.6, 1.6, 0)); ground_obj(r, o)
    lan = L.point((0.6, 1.6, 0.35), energy=30, color=(1.0, 0.6, 0.3), radius=0.08, name="Lantern"); L.flicker(lan, 1, sc.frame_end, 30, amp=0.35)
    cam, tgt = L.camera((0.4, -6.5, 1.1), (0, 2.0, 1.2), lens=50, fstop=2.8, focus_obj=arm)
    L.key(cam, 1, (0.6, -7.5, 0.9)); L.key(cam, sc.frame_end, (0.2, -3.6, 1.25)); L.smooth_keys(cam)


def s3_graves(sc):
    forest(seed=11)
    planks = L.pbr_material("Planks", "weathered_planks", scale=1.0, tint=(0.5, 0.45, 0.4))
    random.seed(3)
    for i in range(9):
        x, y = -2.2 + (i % 5) * 1.05 + random.uniform(-0.15, 0.15), 3.0 + (i // 5) * 1.3 + random.uniform(-0.2, 0.2)
        tilt = random.uniform(-0.12, 0.12); h = random.uniform(0.45, 0.65)
        L.box(f"CrossV_{i}", (0.06, 0.04, h), (x, y, h / 2), rot=(tilt, random.uniform(-0.1, 0.1), 0), mat=planks)
        L.box(f"CrossH_{i}", (0.3, 0.04, 0.05), (x, y, h * 0.72), rot=(tilt, random.uniform(-0.1, 0.1), 0), mat=planks)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y - 0.35, 0.04)); m = bpy.context.object; m.scale = (0.45, 0.9, 0.08); m.name = f"Mound_{i}"
        m.data.materials.append(bpy.data.materials["ForestGround"])
    arm, meshes, _ = L.character("Bryce", ["Kneeling_Prayer"], [("Kneeling_Prayer", 3)], loc=(-1.1, 1.9, 0), rot_z=math.radians(160), darken=("Shirt", "Shorts", "Sneakers"), name="Peter")
    r, o = L.import_gltf("wooden_lantern_01", (-0.4, 2.2, 0)); ground_obj(r, o)
    lan = L.point((-0.4, 2.2, 0.35), energy=35, color=(1.0, 0.6, 0.3), radius=0.08, name="Lantern"); L.flicker(lan, 1, sc.frame_end, 35, amp=0.4)
    cam, tgt = L.camera((2.5, -3.5, 1.7), (-0.5, 2.8, 0.8), lens=35, fstop=4)
    L.key(tgt, 1, (-0.5, 2.6, 1.0)); L.key(tgt, sc.frame_end, (-0.3, 3.4, 0.3))
    L.key(cam, 1, (2.6, -3.8, 1.8)); L.key(cam, sc.frame_end, (1.6, -2.2, 1.1)); L.smooth_keys(cam); L.smooth_keys(tgt)


def s4a_run(sc):
    forest(seed=5, clearing=2.0)
    # Lost boy runs toward the camera along -Y, looking back; camera retreats slightly
    arm, meshes, _ = L.character("Lewis", ["Run_Look_Back"], [("Run_Look_Back", 6)], loc=(0, 12, 0), rot_z=math.radians(180), name="LostBoy")
    L.move_linear(arm, 1, (0, 14, 0), sc.frame_end, (0, -2.5, 0)); L.push_motion(arm)
    L.point((0, 15, 3), energy=400, color=(0.6, 0.7, 1.0), radius=1.0, name="BackLight")
    cam, tgt = L.camera((0.7, -3.5, 1.2), (0, 6, 1.0), lens=50, fstop=2.8, focus_obj=arm)
    L.key(cam, 1, (0.7, -3.5, 1.2)); L.key(cam, sc.frame_end, (0.9, -4.6, 1.1))
    L.key(tgt, 1, (0, 10, 1.0)); L.key(tgt, sc.frame_end, (0, -1.5, 1.0)); L.smooth_keys(cam); L.smooth_keys(tgt)


def s4b_walk(sc):
    forest(seed=9, clearing=2.0)
    arm, meshes, _ = L.character("Bryce", ["Careful_Walk"], [("Careful_Walk", 4)], loc=(0, 6, 0), rot_z=math.radians(180), darken=("Shirt", "Shorts", "Sneakers"), name="Peter")
    L.move_linear(arm, 1, (0, 7.0, 0), sc.frame_end, (0, 2.2, 0)); L.push_motion(arm)
    L.point((0, 9, 3), energy=350, color=(0.6, 0.7, 1.0), radius=1.0, name="BackLight")
    cam, tgt = L.camera((0.5, -1.5, 0.7), (0, 4, 1.0), lens=50, fstop=2.0, focus_obj=arm)
    L.key(tgt, 1, (0, 6, 1.1)); L.key(tgt, sc.frame_end, (0, 2.2, 1.0)); L.smooth_keys(tgt)


def main():
    sc = L.new_scene(FRAMES[SHOT])
    globals()[SHOT](sc)
    L.save(f"{OUT}/{SHOT}.blend")
    if PREVIEW is not None:
        sc.render.resolution_x, sc.render.resolution_y = 960, 540
        sc.cycles.samples = 24
        sc.frame_set(PREVIEW)
        os.makedirs(PREV, exist_ok=True)
        sc.render.filepath = f"{PREV}/{SHOT}_f{PREVIEW:04d}.png"
        import time; t = time.time()
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", sc.render.filepath, f"{time.time() - t:.1f}s")


main()
