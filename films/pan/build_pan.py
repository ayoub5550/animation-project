"""PAN — cartoon horror short. Build the Blender scene from templates only.
Run:  blender -b -P build_pan.py -- [--out /path/pan.blend]
Assets: Mixamo (Timmy, Goblin, Amy, Michelle + clips), Poly Haven CC0 models/textures/HDRIs.
Look: Cycles + Toon BSDF on every material + Freestyle black outlines.
Timeline @24 fps (1728 frames = 72 s). Shots 1 and 7 (black/title) are made in post, so
render frames 193-1248 and 1345-1728.
"""
import bpy, math, os, sys, random
from mathutils import Vector

A = "/work/assets"
MX, PH = f"{A}/mixamo", f"{A}/polyhaven"
FPS = 24
S = {  # shot -> (start, end) frames
    2: (193, 432), 3: (433, 624), 4: (625, 864), 5: (865, 1056),
    6: (1057, 1248), 8: (1345, 1584), 9: (1585, 1728)}
END = 1728
BED = Vector((-1.2, 0.9, 0))       # bed group origin
WIN = Vector((0.9, 2.0, 1.7))      # window centre (in back wall y=+2)
MATTRESS_Z = 0.55
ROOF = Vector((100, 0, 0))         # far-away rooftop set for shot 9


# ---------------- helpers ----------------
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = END
    return sc


def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, ignore_leaf_bones=True)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new if o.type == "ARMATURE"), None)
    return arm, new


def import_model(name):
    d = f"{PH}/{name}"
    before = set(bpy.data.objects)
    if os.path.exists(f"{d}/{name}.gltf"):
        bpy.ops.import_scene.gltf(filepath=f"{d}/{name}.gltf")
    else:
        bpy.ops.import_scene.fbx(filepath=f"{d}/{name}.fbx")
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.parent is None], new


def group(objs_roots, name, loc, rot_z=0, scale=1.0, rot_x=0):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    for r in objs_roots:
        r.parent = e
    e.location = loc
    e.rotation_euler = (math.radians(rot_x), 0, math.radians(rot_z))
    e.scale = (scale, scale, scale)
    return e


def place(name, loc, rot_z=0, scale=1.0, rot_x=0):
    roots, _ = import_model(name)
    return group(roots, name + "_grp", loc, rot_z, scale, rot_x)


def key(obj, path, frame, value, interp="BEZIER"):
    setattr(obj, path, value)
    obj.keyframe_insert(path, frame=frame)
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path != path:
            continue
        for kp in fc.keyframe_points:
            if abs(kp.co.x - frame) < 0.5:
                kp.interpolation = interp


def rz(arm, deg):
    """Rotation tuple that keeps the FBX importer's base rotation (Mixamo rigs come in with X=90°)."""
    r = arm.rotation_euler
    return (r.x, r.y, math.radians(deg))


def height_of(objs):
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(b)).z for o in objs if o.type == "MESH" for b in o.bound_box]
    return (max(zs) - min(zs)) if zs else 1.0


# ---------------- characters ----------------
def build_character(name, clips, target_height):
    """Import skinned T-pose + clips; return (armature, {clip: action}, mesh objects)."""
    arm, objs = import_fbx(f"{MX}/{name}/{name}_TPose.fbx")
    arm.name = name
    arm.animation_data_create(); arm.animation_data.action = None
    actions = {}
    for c in clips:
        a2, new = import_fbx(f"{MX}/{name}/{name}@{c}.fbx")
        act = a2.animation_data.action; act.name = f"{name}_{c}"; actions[c] = act
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
    h = height_of(objs)              # world height with the importer's scale applied
    s = target_height / h
    arm.scale = tuple(c * s for c in arm.scale)  # Mixamo rigs import at 0.01 — scale relative, not absolute
    print(f"CHAR {name}: imported height {h:.2f} -> scale {arm.scale[0]:.4f}")
    return arm, actions, [o for o in objs if o.type == "MESH"]


def nla(arm, plan):
    """plan: list of (clip_action, start_frame, end_frame or None, repeat). Strips are scaled to fit."""
    tr = arm.animation_data.nla_tracks.new(); tr.name = "film"
    for act, start, end, repeat in plan:
        st = tr.strips.new(act.name, int(start), act)
        st.repeat = repeat
        if end:
            st.frame_end = end
        st.extrapolation = "NOTHING"
        st.blend_in = 4; st.blend_out = 4
    tr.strips[-1].extrapolation = "HOLD_FORWARD"
    return tr


def visible(obj, ranges):
    """hide_render/hide_viewport keyframes: visible only inside ranges [(s,e),...]."""
    for o in [obj] + list(obj.children_recursive):
        for prop in ("hide_render", "hide_viewport"):
            setattr(o, prop, True); o.keyframe_insert(prop, frame=1)
            for s, e in ranges:
                setattr(o, prop, True); o.keyframe_insert(prop, frame=s - 1)
                setattr(o, prop, False); o.keyframe_insert(prop, frame=s)
                setattr(o, prop, True); o.keyframe_insert(prop, frame=e + 1)


# ---------------- materials / look ----------------
def toonify(mat, tint=None, desat=0.0):
    """Replace the Principled shading with a Toon BSDF fed by the same base colour."""
    if not mat or not mat.use_nodes:
        return
    nt = mat.node_tree
    p = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    if not p or not out:
        return
    toon = nt.nodes.new("ShaderNodeBsdfToon")
    toon.component = "DIFFUSE"; toon.inputs["Size"].default_value = 0.6; toon.inputs["Smooth"].default_value = 0.08
    src = p.inputs["Base Color"]
    if src.is_linked:
        from_sock = src.links[0].from_socket
        hs = nt.nodes.new("ShaderNodeHueSaturation")
        hs.inputs["Saturation"].default_value = 1.0 - desat
        nt.links.new(from_sock, hs.inputs["Color"])
        col_out = hs.outputs["Color"]
        if tint:
            mix = nt.nodes.new("ShaderNodeMixRGB"); mix.blend_type = "MULTIPLY"; mix.inputs["Fac"].default_value = 0.6
            mix.inputs["Color2"].default_value = (*tint, 1)
            nt.links.new(col_out, mix.inputs["Color1"]); col_out = mix.outputs["Color"]
        nt.links.new(col_out, toon.inputs["Color"])
    else:
        c = list(src.default_value)
        if tint:
            c = [c[i] * (0.4 + 0.6 * tint[i]) for i in range(3)] + [1]
        toon.inputs["Color"].default_value = c
    # alpha (leaves, hair cards): keep transparency
    if p.inputs["Alpha"].is_linked:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(p.inputs["Alpha"].links[0].from_socket, mx.inputs["Fac"])
        nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(toon.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        mat.blend_method = "HASHED"
    else:
        nt.links.new(toon.outputs[0], out.inputs["Surface"])
    p.mute = True


def toonify_all(exclude=()):
    for m in bpy.data.materials:
        if m.name not in exclude and "TOONED" not in m:
            toonify(m); m["TOONED"] = 1


def camera_only(objs):
    """Object is seen by camera rays only (no reflection in the mirror, no glossy bounces)."""
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            if not m: continue
            nt = m.node_tree
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            surf = out.inputs["Surface"].links[0].from_socket
            lp = nt.nodes.new("ShaderNodeLightPath"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs["Fac"])
            nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(surf, mx.inputs[2])
            nt.links.new(mx.outputs[0], out.inputs["Surface"])
        o.visible_glossy = False


def tex_material(name, tex, scale=2.0, tint=None):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(f"{PH}/{tex}_Diffuse.jpg")
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    if tint:
        mix = nt.nodes.new("ShaderNodeMixRGB"); mix.blend_type = "MULTIPLY"; mix.inputs["Fac"].default_value = 0.7
        mix.inputs["Color2"].default_value = (*tint, 1)
        nt.links.new(t.outputs["Color"], mix.inputs["Color1"]); nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def quad(name, verts, mat):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], [(0, 1, 2, 3)]); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat)
    # simple planar UVs
    uv = me.uv_layers.new()
    vs = [Vector(v) for v in verts]
    ax = [i for i in range(3) if max(v[i] for v in vs) - min(v[i] for v in vs) > 1e-4][:2]
    for li, l in enumerate(me.loops):
        v = vs[l.vertex_index]; uv.data[li].uv = (v[ax[0]], v[ax[1]])
    return o


def wall_with_hole(name, y, x0, x1, z0, z1, hole, mat):
    """Wall in plane y=const spanning x0..x1, z0..z1 with rectangular hole (hx0,hx1,hz0,hz1)."""
    hx0, hx1, hz0, hz1 = hole
    parts = [(x0, hx0, z0, z1), (hx1, x1, z0, z1), (hx0, hx1, z0, hz0), (hx0, hx1, hz1, z1)]
    objs = []
    for i, (a, b, c, d) in enumerate(parts):
        if abs(b - a) < 1e-4 or abs(d - c) < 1e-4:
            continue  # zero-size part (e.g. door reaches the floor)
        objs.append(quad(f"{name}_{i}", [(a, y, c), (b, y, c), (b, y, d), (a, y, d)], mat))
    return objs


# ---------------- set ----------------
def build_room():
    wallpaper = tex_material("Wallpaper", "decrepit_wallpaper", 1.0, tint=(0.55, 0.62, 0.75))
    floor = tex_material("Floor", "old_wood_floor", 1.5)
    ceil = tex_material("Ceiling", "damaged_plaster", 1.0)
    quad("Floor", [(-2.5, -2, 0), (2.5, -2, 0), (2.5, 2, 0), (-2.5, 2, 0)], floor)
    quad("Ceil", [(-2.5, -2, 3), (-2.5, 2, 3), (2.5, 2, 3), (2.5, -2, 3)], ceil)
    # back wall with window hole
    wall_with_hole("WallBack", 2.0, -2.5, 2.5, 0, 3, (WIN.x - 0.5, WIN.x + 0.5, WIN.z - 0.7, WIN.z + 0.7), wallpaper)
    # front wall with door hole (mother enters here) at x=1.6
    wall_with_hole("WallFront", -2.0, -2.5, 2.5, 0, 3, (1.2, 2.1, 0, 2.1), wallpaper)
    quad("WallL", [(-2.5, -2, 0), (-2.5, 2, 0), (-2.5, 2, 3), (-2.5, -2, 3)], wallpaper)
    quad("WallR", [(2.5, -2, 0), (2.5, -2, 3), (2.5, 2, 3), (2.5, 2, 0)], wallpaper)
    # window frame: 4 thin dark boxes
    frame = bpy.data.materials.new("Frame"); frame.use_nodes = True
    frame.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.06, 0.05, 1)
    for dx, dz, sx, sz in [(-0.52, 0, 0.04, 1.48), (0.52, 0, 0.04, 1.48), (0, -0.72, 1.08, 0.04), (0, 0.72, 1.08, 0.04), (0, 0, 1.0, 0.03)]:
        bpy.ops.mesh.primitive_cube_add(location=(WIN.x + dx, WIN.y, WIN.z + dz))
        c = bpy.context.object; c.scale = (sx / 2, 0.04, sz / 2); c.data.materials.append(frame); c.name = "WinFrame"
    # curtain: subdivided plane with animated wave, hangs left of the window, lifts in shot 3
    bpy.ops.mesh.primitive_plane_add(size=1, location=(WIN.x - 0.35, WIN.y - 0.12, WIN.z + 0.05))
    cur = bpy.context.object; cur.name = "Curtain"; cur.scale = (0.38, 1, 1.5)
    cur.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=20); bpy.ops.object.mode_set(mode="OBJECT")
    w = cur.modifiers.new("Wave", "WAVE"); w.height = 0.12; w.width = 0.5; w.speed = 0.15; w.use_normal = True
    cm = bpy.data.materials.new("Curtain"); cm.use_nodes = True
    cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.7, 0.6, 1)
    cur.data.materials.append(cm)
    key(cur, "rotation_euler", S[3][0], (math.radians(90), 0, 0))
    key(cur, "rotation_euler", S[3][0] + 70, (math.radians(90), math.radians(-9), 0))
    key(cur, "rotation_euler", S[3][1], (math.radians(90), math.radians(-4), 0))
    # props (Poly Haven)
    place("GothicBed_01", BED, rot_z=90)
    place("throw_pillows_01", BED + Vector((0, 0.7, MATTRESS_Z)), rot_z=90, scale=0.8)
    place("wooden_table_02", (1.8, 1.4, 0), rot_z=0)
    place("brass_candleholders", (1.7, 1.4, 0.78), rot_z=20, scale=0.8)
    place("mantel_clock_01", (2.0, 1.6, 0.78), rot_z=-95, scale=0.8)
    place("WoodenChair_01", (1.6, 0.6, 0), rot_z=150)
    place("Rockingchair_01", (-1.9, -1.4, 0), rot_z=40)
    place("ornate_mirror_01", (2.47, -0.2, 1.5), rot_z=-90)
    place("Chandelier_02", (0.3, 0, 2.95), scale=0.7)
    place("rubber_duck_toy", (0.2, -0.6, 0), rot_z=30, scale=0.8)
    place("vintage_oil_lamp", (-2.2, 1.7, 0), scale=0.9)
    place("decorative_book_set_01", (-2.0, -1.0, 0), rot_z=15, scale=0.8)
    boots = place("rubber_boots", (-0.35, 0.3, 0), rot_z=100, scale=0.55)  # small shoes by the bed
    # green leaf on the pillow (shot 8 only)
    bpy.ops.mesh.primitive_plane_add(size=0.12, location=BED + Vector((0.1, 0.75, MATTRESS_Z + 0.12)))
    leaf = bpy.context.object; leaf.name = "Leaf"; leaf.scale = (0.5, 1, 1); leaf.rotation_euler = (0, 0, 0.6)
    lm = bpy.data.materials.new("Leaf"); lm.use_nodes = True
    lm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.45, 0.12, 1)
    leaf.data.materials.append(lm)
    visible(leaf, [S[8]])
    return boots


def build_rooftop():
    roof = tex_material("Roof", "asphalt_02", 6.0, tint=(0.4, 0.45, 0.6))
    quad("RoofPlane", [(ROOF.x - 8, -8, 0), (ROOF.x + 8, -8, 0), (ROOF.x + 8, 8, 0), (ROOF.x - 8, 8, 0)], roof)
    place("dead_tree_trunk_02", ROOF + Vector((3.5, 4, 0)), rot_z=30, scale=1.6)
    # a chimney block
    bpy.ops.mesh.primitive_cube_add(location=ROOF + Vector((-4.5, 5, 0.9)))
    ch = bpy.context.object; ch.scale = (0.5, 0.5, 0.9); ch.name = "Chimney"
    cm = bpy.data.materials.new("Chimney"); cm.use_nodes = True
    cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.18, 0.16, 1)
    ch.data.materials.append(cm)


# ---------------- world / lights ----------------
def world():
    w = bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]
    envs = {}
    for k, f in [("night", "rogland_moonlit_night_2k.hdr"), ("day", "kloppenheim_06_2k.hdr"), ("roof", "rooftop_night_2k.hdr")]:
        e = nt.nodes.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(f"{PH}/{f}"); envs[k] = e
    m1 = nt.nodes.new("ShaderNodeMixRGB"); m2 = nt.nodes.new("ShaderNodeMixRGB")
    nt.links.new(envs["night"].outputs[0], m1.inputs[1]); nt.links.new(envs["day"].outputs[0], m1.inputs[2])
    nt.links.new(m1.outputs[0], m2.inputs[1]); nt.links.new(envs["roof"].outputs[0], m2.inputs[2])
    nt.links.new(m2.outputs[0], bg.inputs["Color"])
    # fac keyframes: night until shot 8, day in shot 8, roof in shot 9
    def k(node, frame, val):
        node.inputs["Fac"].default_value = val; node.inputs["Fac"].keyframe_insert("default_value", frame=frame)
    k(m1, 1, 0); k(m1, S[8][0] - 1, 0); k(m1, S[8][0], 1); k(m1, S[9][0] - 1, 1); k(m1, S[9][0], 0)
    k(m2, 1, 0); k(m2, S[9][0] - 1, 0); k(m2, S[9][0], 1)
    bg.inputs["Strength"].default_value = 0.8
    bg.inputs["Strength"].keyframe_insert("default_value", frame=1)
    bg.inputs["Strength"].keyframe_insert("default_value", frame=S[8][0] - 1)
    bg.inputs["Strength"].default_value = 1.5; bg.inputs["Strength"].keyframe_insert("default_value", frame=S[8][0])
    bg.inputs["Strength"].keyframe_insert("default_value", frame=S[9][0] - 1)
    bg.inputs["Strength"].default_value = 0.6; bg.inputs["Strength"].keyframe_insert("default_value", frame=S[9][0])
    for fc in nt.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"


def lights():
    # moon through the window (cool spot from outside)
    bpy.ops.object.light_add(type="SPOT", location=(WIN.x + 1.5, WIN.y + 4.0, 4.5))
    moon = bpy.context.object; moon.name = "Moon"; moon.data.energy = 40000; moon.data.color = (0.55, 0.65, 1.0)
    moon.data.spot_size = math.radians(40); moon.data.shadow_soft_size = 0.15
    tgt = bpy.data.objects.new("MoonTgt", None); bpy.context.scene.collection.objects.link(tgt); tgt.location = (WIN.x - 0.3, 0.0, 0.6)
    c = moon.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    # candle on the table: warm flicker, dies in shot 3
    bpy.ops.object.light_add(type="POINT", location=(1.7, 1.4, 1.05))
    cd = bpy.context.object; cd.name = "Candle"; cd.data.color = (1.0, 0.55, 0.2); cd.data.shadow_soft_size = 0.05
    random.seed(7)
    off = S[3][0] + 110
    for f in range(1, off, 6):
        cd.data.energy = random.uniform(70, 110); cd.data.keyframe_insert("energy", frame=f)
    cd.data.energy = 0; cd.data.keyframe_insert("energy", frame=off + 8)
    # cool fill so the cartoon shading reads
    bpy.ops.object.light_add(type="AREA", location=(0, -1.5, 2.9)); fill = bpy.context.object
    fill.name = "Fill"; fill.data.energy = 450; fill.data.color = (0.5, 0.6, 0.9); fill.data.size = 3
    fill.rotation_euler = (math.radians(20), 0, 0)
    # morning sun (shot 8 only) & rooftop moon (shot 9 only)
    bpy.ops.object.light_add(type="SUN", location=(0, 5, 6)); sun = bpy.context.object; sun.name = "Sun"
    sun.data.energy = 3.0; sun.data.color = (0.9, 0.9, 1.0); sun.rotation_euler = (math.radians(50), 0, math.radians(200))
    bpy.ops.object.light_add(type="SUN", location=ROOF + Vector((0, 0, 10))); rm = bpy.context.object; rm.name = "RoofMoon"
    rm.data.energy = 1.2; rm.data.color = (0.6, 0.7, 1.0); rm.rotation_euler = (math.radians(60), 0, math.radians(20))
    visible(sun, [S[8]]); visible(rm, [S[9]])
    visible(moon, [(1, S[8][0] - 1)]); visible(cd, [(1, S[8][0] - 1)]); visible(fill, [(1, S[8][1])])
    # shot 8: the room fill becomes greyish daylight
    bpy.ops.object.light_add(type="AREA", location=(WIN.x, WIN.y - 0.3, WIN.z)); day = bpy.context.object
    day.name = "DayWindow"; day.data.energy = 250; day.data.color = (0.8, 0.85, 1.0); day.data.size = 1.0; day.data.size_y = 1.4
    day.rotation_euler = (math.radians(90), 0, 0); day.data.shape = "RECTANGLE"
    visible(day, [S[8]])


# ---------------- cast ----------------
def build_cast():
    sc = bpy.context.scene
    # PAN (Timmy)
    pan, pa, pan_meshes = build_character("Timmy", ["Crouch_Idle", "Crouch_To_Stand", "Sneak_Walk", "Standing_Idle", "Head_Turn", "Kneel_Down", "Kneel_Reach"], 1.25)
    for o in pan_meshes:
        for s in o.material_slots:
            toonify(s.material, tint=(0.55, 0.9, 0.5), desat=0.3); s.material["TOONED"] = 1
    camera_only(pan_meshes)  # no reflection in the mirror
    # shot 4: on the window sill (crouch), stands, sneaks to the bed
    s4 = S[4][0]
    nla(pan, [(pa["Crouch_Idle"], s4, s4 + 80, 2), (pa["Crouch_To_Stand"], s4 + 81, s4 + 130, 1),
              (pa["Sneak_Walk"], s4 + 131, S[4][1], 3),
              (pa["Head_Turn"], S[5][0], S[5][1], 1),
              (pa["Kneel_Down"], S[6][0], S[6][0] + 70, 1), (pa["Kneel_Reach"], S[6][0] + 71, S[6][1], 1),
              (pa["Standing_Idle"], S[9][0], S[9][0] + 80, 1), (pa["Head_Turn"], S[9][0] + 81, S[9][1], 1)])
    sill = (WIN.x, WIN.y - 0.15, WIN.z - 0.7)
    key(pan, "location", s4, sill); key(pan, "rotation_euler", s4, rz(pan, 0))  # rz 0 = faces -Y (into the room)
    key(pan, "location", s4 + 130, sill)
    key(pan, "location", s4 + 150, (WIN.x - 0.1, 1.5, 0))          # drops to the floor
    key(pan, "location", S[4][1], (BED.x + 0.9, 0.9, 0))             # beside the bed
    key(pan, "rotation_euler", S[4][1], rz(pan, 90))
    key(pan, "rotation_euler", S[5][0] - 1, rz(pan, 90), "CONSTANT"); key(pan, "rotation_euler", S[5][0], rz(pan, 0), "CONSTANT")
    key(pan, "rotation_euler", S[6][0], rz(pan, 90), "CONSTANT")
    key(pan, "location", S[6][0] - 1, (BED.x + 0.9, 0.9, 0), "CONSTANT"); key(pan, "location", S[6][0], (BED.x + 0.8, 1.35, 0), "CONSTANT")
    key(pan, "location", S[6][1], (BED.x + 0.8, 1.35, 0))
    key(pan, "location", S[9][0], ROOF + Vector((0, 0, 0))); key(pan, "rotation_euler", S[9][0], rz(pan, 0))
    visible(pan, [(S[3][0] + 120, S[6][1]), S[9]])
    # true face (Goblin) — 2 frame flash in shot 5
    gob, ga, gob_meshes = build_character("Goblin", ["Standing_Idle"], 1.25)
    for o in gob_meshes:
        for s in o.material_slots: toonify(s.material, tint=(0.7, 0.8, 0.6)); s.material["TOONED"] = 1
    nla(gob, [(ga["Standing_Idle"], S[5][0], S[5][1], 1)])
    gob.location = (BED.x + 0.9, 0.9, 0); gob.rotation_euler = rz(gob, 0)
    flash = S[5][0] + 135
    visible(gob, [(flash, flash + 1)])
    visible(pan, [(S[3][0] + 120, flash - 1), (flash + 2, S[6][1]), S[9]])
    # child (Amy): under a blanket until shot 6 (Mixamo has no lying-in-bed clip that reads well), then sits up
    amy, aa, amy_meshes = build_character("Amy", ["Waking"], 1.15)
    for o in amy_meshes:
        for s in o.material_slots: toonify(s.material); s.material["TOONED"] = 1
    nla(amy, [(aa["Waking"], S[6][0], S[6][1], 1)])
    amy.location = BED + Vector((0.1, 0.3, MATTRESS_Z)); amy.rotation_euler = rz(amy, 90)
    visible(amy, [S[6]])
    bpy.ops.mesh.primitive_cube_add(location=BED + Vector((0.05, 0.1, MATTRESS_Z + 0.12)))
    bl = bpy.context.object; bl.name = "Blanket"; bl.scale = (0.55, 0.95, 0.11)
    bv = bl.modifiers.new("Bevel", "BEVEL"); bv.width = 0.35; bv.segments = 6
    bm = bpy.data.materials.new("Blanket"); bm.use_nodes = True
    bm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.22, 0.45, 1)
    bl.data.materials.append(bm)
    visible(bl, [(1, S[6][0] + 10)])
    # slow breathing of the blanket
    key(bl, "scale", 1, (0.55, 0.95, 0.11)); key(bl, "scale", 36, (0.55, 0.95, 0.13)); key(bl, "scale", 72, (0.55, 0.95, 0.11))
    bl.animation_data.action.fcurves[2].modifiers.new("CYCLES")
    # mother (Michelle) — shot 8: walks toward the bed (clip has root motion, ~1.8 m along local -Y), kneels, cries
    mom, ma, mom_meshes = build_character("Michelle", ["Walking", "Kneel_Down", "Crying"], 1.7)
    for o in mom_meshes:
        for s in o.material_slots: toonify(s.material, desat=0.3); s.material["TOONED"] = 1
    s8 = S[8][0]
    nla(mom, [(ma["Walking"], s8, s8 + 95, 1), (ma["Crying"], s8 + 96, s8 + 150, 1), (ma["Kneel_Down"], s8 + 151, S[8][1], 1)])
    key(mom, "location", s8, (0.9, -1.5, 0)); key(mom, "rotation_euler", s8, rz(mom, -148))
    key(mom, "location", s8 + 95, (0.9, -1.5, 0), "CONSTANT")
    key(mom, "location", s8 + 96, (-0.05, 0.02, 0), "CONSTANT"); key(mom, "rotation_euler", s8 + 96, rz(mom, -165))
    visible(mom, [S[8]])
    return pan, amy, mom


# ---------------- cameras ----------------
def cam(name, lens=35):
    d = bpy.data.cameras.new(name); d.lens = lens
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o)
    return o


def aim(c, target_loc):
    t = bpy.data.objects.new(c.name + "_tgt", None); bpy.context.scene.collection.objects.link(t); t.location = target_loc
    con = c.constraints.new("TRACK_TO"); con.target = t; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    return t


def cameras(pan):
    sc = bpy.context.scene
    def bind(c, frame):
        m = sc.timeline_markers.new(c.name, frame=frame); m.camera = c
    # shot 2: slow push-in from the door toward the bed
    c2 = cam("Cam2", 32); aim(c2, BED + Vector((0, 0.3, 0.7)))
    key(c2, "location", S[2][0], (1.3, -1.7, 1.5)); key(c2, "location", S[2][1], (0.6, -0.9, 1.3)); bind(c2, 1)
    # shot 3: window & wall, low angle, curtain and growing shadow
    c3 = cam("Cam3", 28); aim(c3, (WIN.x - 0.6, 1.8, 1.4))
    key(c3, "location", S[3][0], (-0.4, -0.6, 0.7)); key(c3, "location", S[3][1], (-0.2, -0.3, 0.75)); bind(c3, S[3][0])
    # shot 4: Pan silhouetted on the sill against the moon, then follows him
    c4 = cam("Cam4", 30); t4 = aim(c4, (WIN.x, 1.7, 1.2))
    key(c4, "location", S[4][0], (0.2, -1.8, 0.8)); key(c4, "location", S[4][0] + 150, (0.0, -1.6, 0.85))
    key(c4, "location", S[4][1], (1.3, -1.9, 1.1))
    key(t4, "location", S[4][0] + 130, (WIN.x, 1.7, 1.2)); key(t4, "location", S[4][1], (BED.x + 0.9, 0.9, 0.7))
    bind(c4, S[4][0])
    # shot 5: close-up on the face
    c5 = cam("Cam5", 50); aim(c5, (BED.x + 0.9, 0.9, 1.02))
    key(c5, "location", S[5][0], (0.5, -1.1, 1.0)); key(c5, "location", S[5][1], (0.3, -0.6, 1.0)); bind(c5, S[5][0])
    # shot 6: from behind Pan toward the bed; mirror on the right wall in frame
    c6 = cam("Cam6", 30); aim(c6, BED + Vector((0.2, 0.4, 0.7)))
    key(c6, "location", S[6][0], (1.9, -1.7, 1.5)); key(c6, "location", S[6][1], (2.1, -1.2, 1.4)); bind(c6, S[6][0])
    # shot 8: morning wide, then tilt down toward the boots/leaf
    c8 = cam("Cam8", 28); t8 = aim(c8, BED + Vector((0.3, 0.3, 0.8)))
    key(c8, "location", S[8][0], (1.9, -1.7, 1.6)); key(c8, "location", S[8][1], (1.0, -1.3, 1.2))
    key(t8, "location", S[8][0] + 120, BED + Vector((0.3, 0.3, 0.8))); key(t8, "location", S[8][1], BED + Vector((0.6, 0.3, 0.45)))
    bind(c8, S[8][0])
    # shot 9: rooftop, Pan silhouette against the moon
    c9 = cam("Cam9", 40); aim(c9, ROOF + Vector((0, 0, 0.8)))
    key(c9, "location", S[9][0], ROOF + Vector((0.5, -5.5, 0.6))); key(c9, "location", S[9][1], ROOF + Vector((0.2, -3.2, 0.8))); bind(c9, S[9][0])
    sc.camera = c2


# ---------------- render ----------------
def render_settings():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64; sc.cycles.use_denoising = True
    sc.render.resolution_x = 1920; sc.render.resolution_y = 1080; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.use_freestyle = True; sc.render.line_thickness = 2.5
    vl = bpy.context.view_layer
    vl.use_freestyle = True
    ls = vl.freestyle_settings.linesets.new("Ink") if not vl.freestyle_settings.linesets else vl.freestyle_settings.linesets[0]
    ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True; ls.select_edge_mark = False
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("Ink")
    ls.linestyle.color = (0.02, 0.02, 0.03); ls.linestyle.thickness = 2.5
    vl.freestyle_settings.crease_angle = math.radians(140)
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - High Contrast"
    sc.view_settings.exposure = -0.3
    sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 8
    sc.render.film_transparent = False


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[argv.index("--out") + 1] if "--out" in argv else "/work/projects/pan/pan.blend"
    clear()
    build_room()
    build_rooftop()
    world(); lights()
    toonify_all()                       # props + room
    pan, amy, mom = build_cast()
    cameras(pan)
    render_settings()
    bpy.ops.file.pack_all()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("SAVED", out)


main()
