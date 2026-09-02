"""Blender-side helpers for the Dark Peter Pan film (run inside blender -b -P).
Everything here only PLACES downloaded assets (Mixamo FBX, Poly Haven glTF/HDR/textures)."""
import bpy, math, random, os
from mathutils import Vector, Euler

MX = "/work/assets/mixamo"
PH = "/work/assets/polyhaven"
FPS = 24


# ---------------- scene basics ----------------
def new_scene(frames, res=(1920, 1080), samples=48):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, frames
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6
    sc.cycles.volume_bounces = 0
    sc.cycles.volume_step_rate = 2.0
    sc.cycles.volume_max_steps = 256
    sc.render.use_motion_blur = False
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = 0.6
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    return sc


def world_hdri(path, strength=0.15, rotation=0.0, tint=(0.6, 0.7, 1.0)):
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); bg = nt.nodes.new("ShaderNodeBackground")
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(path)
    mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord")
    mp.inputs["Rotation"].default_value = (0, 0, rotation)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0; mix.inputs[7].default_value = (*tint, 1)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], mix.inputs[6]); nt.links.new(mix.outputs[2], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def fog_box(center, size, density=0.02, color=(0.55, 0.65, 0.8), anisotropy=0.3):
    """A box of Principled Volume = local fog (cheaper than world volume)."""
    bpy.ops.mesh.primitive_cube_add(location=center); c = bpy.context.object; c.name = "Fog"
    c.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    m = bpy.data.materials.new("FogMat"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = density; vol.inputs["Color"].default_value = (*color, 1)
    vol.inputs["Anisotropy"].default_value = anisotropy
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); nt.links.new(tr.outputs["BSDF"], out.inputs["Surface"])
    c.data.materials.append(m); c.display_type = "WIRE"
    c.visible_camera = True; c.visible_shadow = True
    return c


def sun(direction_from, energy=2.0, color=(0.7, 0.8, 1.0), angle=1.0):
    bpy.ops.object.light_add(type="SUN", location=direction_from); L = bpy.context.object
    L.data.energy = energy; L.data.color = color; L.data.angle = math.radians(angle)
    L.rotation_euler = (Vector((0, 0, 0)) - Vector(direction_from)).to_track_quat("-Z", "Y").to_euler()
    return L


def point(loc, energy=40, color=(1.0, 0.6, 0.3), radius=0.1, name="Point"):
    bpy.ops.object.light_add(type="POINT", location=loc); L = bpy.context.object; L.name = name
    L.data.energy = energy; L.data.color = color; L.data.shadow_soft_size = radius
    return L


def flicker(light, f0, f1, base, amp=0.35, seed=1, step=3):
    """Keyframe a lantern/candle flicker on light energy."""
    random.seed(seed)
    for f in range(f0, f1 + 1, step):
        light.data.energy = base * (1 + amp * random.uniform(-1, 1))
        light.data.keyframe_insert("energy", frame=f)


# ---------------- assets ----------------
def import_gltf(aid, loc=(0, 0, 0), rot_z=0.0, scale=1.0, name=None):
    path = f"{PH}/models/{aid}/{aid}.gltf"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    if len(roots) > 1:
        e = bpy.data.objects.new(name or aid, None); bpy.context.scene.collection.objects.link(e)
        for r in roots: r.parent = e
        root = e
    else:
        root = roots[0]
    root.name = name or aid
    root.location = loc; root.rotation_euler = (0, 0, rot_z); root.scale = (scale, scale, scale)
    for o in new:
        if o.type == "MESH":
            for s in o.material_slots:
                if s.material: s.material.blend_method = "HASHED"
    return root, new


def bbox_dims(objs):
    pts = [o.matrix_world @ Vector(b) for o in objs if o.type == "MESH" for b in o.bound_box]
    if not pts: return Vector((0, 0, 0)), Vector((0, 0, 0))
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def pbr_material(name, tex_id, scale=1.0, rough_default=0.8, tint=None):
    d = f"{PH}/textures/{tex_id}"
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    def tex(suffix, cs):
        for ext in ("jpg", "png"):
            p = f"{d}/{tex_id}_{suffix}.{ext}"
            if os.path.exists(p):
                t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(p)
                t.image.colorspace_settings.name = cs; nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
        return None
    t = tex("Diffuse", "sRGB")
    if t:
        if tint:
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0; mix.inputs[7].default_value = (*tint, 1)
            nt.links.new(t.outputs["Color"], mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs["Base Color"])
        else:
            nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    r = tex("Rough", "Non-Color")
    if r: nt.links.new(r.outputs["Color"], b.inputs["Roughness"])
    else: b.inputs["Roughness"].default_value = rough_default
    n = tex("nor_gl", "Non-Color")
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def plane(name, size, loc, rot=(0, 0, 0), mat=None, uv_scale=1.0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); p = bpy.context.object; p.name = name
    p.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(scale=True)
    if mat: p.data.materials.append(mat)
    return p


def box(name, dims, loc, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); c = bpy.context.object; c.name = name
    c.scale = dims; bpy.ops.object.transform_apply(scale=True)
    if mat: c.data.materials.append(mat)
    return c


# ---------------- characters ----------------
def fix_mixamo_materials(mesh_objs, darken_objs=(), tint=(0.05, 0.07, 0.05)):
    for o in mesh_objs:
        for slot in o.material_slots:
            m = slot.material
            if not (m and m.use_nodes): continue
            nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
            if not b: continue
            for l in [l for l in nt.links if l.to_socket == b.inputs["Roughness"]]: nt.links.remove(l)
            b.inputs["Roughness"].default_value = 0.75
            b.inputs["Specular IOR Level"].default_value = 0.3
            if any(k.lower() in o.name.lower() for k in darken_objs):
                m = m.copy(); slot.material = m; nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
                link = next((l for l in nt.links if l.to_socket == b.inputs["Base Color"]), None)
                mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
                mix.inputs["Factor"].default_value = 1.0; mix.inputs[7].default_value = (*tint, 1)
                if link: nt.links.new(link.from_socket, mix.inputs[6])
                else: mix.inputs[6].default_value = b.inputs["Base Color"].default_value
                nt.links.new(mix.outputs[2], b.inputs["Base Color"])


def _import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, ignore_leaf_bones=True, automatic_bone_orientation=False)
    new = [o for o in bpy.data.objects if o not in before]
    return next(o for o in new if o.type == "ARMATURE"), new


def character(cname, clips, plan, loc=(0, 0, 0), rot_z=0.0, darken=(), name=None):
    """Import <cname>_TPose.fbx + clips; build one NLA track from plan=[(clip, repeat, start_frame or None)].
    Returns (armature, meshes, end_frame). Movement: keyframe the armature object afterwards, then call push_motion()."""
    arm, objs = _import_fbx(f"{MX}/{cname}/{cname}_TPose.fbx")
    arm.name = name or cname
    arm.animation_data_create(); arm.animation_data.action = None
    meshes = [o for o in objs if o.type == "MESH"]
    fix_mixamo_materials(meshes, darken)
    actions = {}
    for c in clips:
        a2, n2 = _import_fbx(f"{MX}/{cname}/{cname}@{c}.fbx")
        act = a2.animation_data.action; act.name = f"{arm.name}_{c}"; actions[c] = act
        for o in n2: bpy.data.objects.remove(o, do_unlink=True)
    track = arm.animation_data.nla_tracks.new(); track.name = "clips"
    f = 1
    for item in plan:
        cname_, repeat = item[0], item[1]
        start = item[2] if len(item) > 2 and item[2] else f
        a = actions[cname_]
        if track.strips and start <= track.strips[-1].frame_end:
            track.strips[-1].frame_end_ui = start - 1  # trim previous clip so the next one can start here
        strip = track.strips.new(cname_, int(start), a); strip.repeat = repeat
        strip.blend_in = 6 if start > 1 else 0
        strip.extrapolation = "HOLD_FORWARD"
        f = int(strip.frame_end) + 1
    for s in track.strips: s.blend_type = "REPLACE"
    # Mixamo FBX arrives with a 90deg X rotation (Y-up) -> keep it, only set the Z heading
    arm.location = loc; arm.rotation_euler = (math.pi / 2, 0, rot_z)
    return arm, meshes, f


def push_motion(arm):
    """Move the object-level action (location/rotation keys) onto its own NLA track so clips still play."""
    ad = arm.animation_data
    if not ad.action: return
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
    t = ad.nla_tracks.new(); t.name = "move"
    s = t.strips.new("move", int(ad.action.frame_range[0]), ad.action); s.extrapolation = "HOLD"
    ad.action = None


def move_linear(arm, f0, p0, f1, p1, rot_z=None):
    arm.location = p0; arm.keyframe_insert("location", frame=f0)
    arm.location = p1; arm.keyframe_insert("location", frame=f1)
    if rot_z is not None:
        arm.rotation_euler = (math.pi / 2, 0, rot_z); arm.keyframe_insert("rotation_euler", frame=f0)


# ---------------- camera ----------------
def camera(loc, look_at, lens=35, fstop=None, focus_obj=None, name="Cam"):
    cam = bpy.data.cameras.new(name); co = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(co); bpy.context.scene.camera = co
    cam.lens = lens; cam.sensor_width = 36
    tgt = bpy.data.objects.new(name + "_target", None); bpy.context.scene.collection.objects.link(tgt)
    tgt.location = look_at
    con = co.constraints.new("TRACK_TO"); con.target = tgt; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    co.location = loc
    if fstop:
        cam.dof.use_dof = True; cam.dof.aperture_fstop = fstop
        cam.dof.focus_object = focus_obj or tgt
    return co, tgt


def key(obj, frame, loc=None, attr="location"):
    if loc is not None: setattr(obj, attr, loc)
    obj.keyframe_insert(attr, frame=frame)


def smooth_keys(obj):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "EASE_IN_OUT"


def save(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("SAVED", path)
