"""Build the 30-second test scene in Blender (run: blender -b -P build_scene.py).

Scene: a man (Mixamo 'James') walks down a dark street at night, stops under a
street lamp and looks around. All assets are downloaded templates (Mixamo,
Poly Haven CC0). Nothing is modelled here; this script only places & wires them.
"""
import bpy, math, os, sys
from mathutils import Vector

ROOT = "/work/assets"
MX = f"{ROOT}/mixamo/James"
PH = f"{ROOT}/polyhaven"
OUT = "/work/projects/animation-film"
FPS = 24
FRAMES = 24 * 30  # 30 s

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = 1
    sc.frame_end = FRAMES
    return sc

def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, ignore_leaf_bones=True, automatic_bone_orientation=False)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    return arm, new

def import_gltf(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    return roots, new

def build_character():
    """Import T-pose (skin) and clips (no skin); move clip actions onto the skinned rig's NLA."""
    james, objs = import_fbx(f"{MX}/James_TPose.fbx")
    james.name = "James"
    james.animation_data_create()
    james.animation_data.action = None  # drop the T-pose action so the NLA is evaluated
    clips = ["Walking", "Stop_Walking", "Look_Around", "Idle"]
    actions = {}
    for c in clips:
        arm, new = import_fbx(f"{MX}/James@{c}.fbx")
        act = arm.animation_data.action
        act.name = c
        actions[c] = act
        for o in new:  # delete the extra rig, keep the action
            bpy.data.objects.remove(o, do_unlink=True)
    for o in objs:
        if o.type == "MESH":
            for slot in o.material_slots:
                m = slot.material
                if m and m.use_nodes and "Principled BSDF" in m.node_tree.nodes:
                    b = m.node_tree.nodes["Principled BSDF"]
                    if not b.inputs["Roughness"].is_linked:
                        b.inputs["Roughness"].default_value = 0.75
                    b.inputs["Specular IOR Level"].default_value = 0.25
    # NLA sequence: Walking (loop) -> Stop_Walking -> Look_Around -> Idle
    track = james.animation_data.nla_tracks.new()
    track.name = "film"
    f = 1
    plan = [("Walking", 4), ("Stop_Walking", 1), ("Look_Around", 1), ("Idle", 1)]
    lengths = {}
    for name, repeat in plan:
        a = actions[name]
        length = a.frame_range[1] - a.frame_range[0]
        strip = track.strips.new(name, int(f), a)
        strip.repeat = repeat
        strip.extrapolation = "HOLD_FORWARD" if name == "Idle" else "NOTHING"
        lengths[name] = strip.frame_end - strip.frame_start
        f = strip.frame_end + 1
    print("NLA end frame", f)
    walk_end = track.strips["Walking"].frame_end
    james.location = (0, -10, 0)
    james.keyframe_insert("location", frame=1)
    james.location = (0, -10 + 1.35 * 4, 0)  # ~1.35 m per cycle
    james.keyframe_insert("location", frame=walk_end)
    for fc in james.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    james.animation_data.action_extrapolation = "HOLD"
    # the object action would override the NLA -> push it onto its own track
    t2 = james.animation_data.nla_tracks.new()
    t2.name = "move"
    t2.strips.new("move", 1, james.animation_data.action)
    james.animation_data.action = None
    t2.strips[0].extrapolation = "HOLD" 
    # Mixamo FBX comes in at 0.01 scale with cm units -> already handled by importer; ensure 1.8m tall
    bpy.context.view_layer.update()
    h = max((james.matrix_world @ Vector(b)).z for o in objs if o.type == "MESH" for b in o.bound_box)
    if h < 0.5 or h > 3:
        s = 1.8 / h
        james.scale = (s, s, s)
    return james, f

def add_ground():
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    g = bpy.context.object
    g.name = "Ground"
    mat = bpy.data.materials.new("Asphalt")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (30, 30, 30)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    for k, sock, cs in [("Diffuse", "Base Color", "sRGB"), ("Rough", "Roughness", "Non-Color")]:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(f"{PH}/asphalt_02_{k}.jpg")
        t.image.colorspace_settings.name = cs
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], bsdf.inputs[sock])
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(f"{PH}/asphalt_02_nor_gl.jpg")
    n.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    nt.links.new(n.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    g.data.materials.append(mat)
    return g

def place(name, loc, rot_z=0, scale=1):
    roots, new = import_gltf(f"{PH}/{name}/{name}.gltf")
    empty = bpy.data.objects.new(name + "_grp", None)
    bpy.context.scene.collection.objects.link(empty)
    for r in roots:
        r.parent = empty
    empty.location = loc
    empty.rotation_euler = (0, 0, math.radians(rot_z))
    empty.scale = (scale, scale, scale)
    return empty

def world_hdri():
    w = bpy.data.worlds.new("Night")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(f"{PH}/cobblestone_street_night_2k.hdr")
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.06
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])

def lights(lamp_pos):
    bpy.ops.object.light_add(type="POINT", location=(lamp_pos[0], lamp_pos[1], 4.2))
    l = bpy.context.object
    l.name = "LampLight"
    l.data.energy = 900
    l.data.color = (1.0, 0.75, 0.45)
    l.data.shadow_soft_size = 0.4
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10))
    s = bpy.context.object
    s.name = "Moon"
    s.data.energy = 0.08
    s.data.color = (0.6, 0.7, 1.0)
    s.rotation_euler = (math.radians(55), 0, math.radians(140))

def camera(james, stop_frame):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 35
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    # Shot 1 (1..stop): low tracking shot from the side/front while he walks toward the lamp
    # Shot 2 (stop..end): slow push-in on him under the lamp
    tgt = bpy.data.objects.new("CamTarget", None)
    bpy.context.scene.collection.objects.link(tgt)
    cl = tgt.constraints.new("COPY_LOCATION")
    cl.target = james
    cl.use_offset = True
    tgt.location = (0, 0, 1.3)  # chest height, world space
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    keys = [(1, (4.5, -15.5, 1.3)), (stop_frame, (3.6, -8.2, 1.5)), (FRAMES, (2.0, -6.6, 1.55))]
    for f, loc in keys:
        cam.location = loc
        cam.keyframe_insert("location", frame=f)
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
    return cam

def render_settings(preview=True):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types, "SceneEEVEE") and bpy.app.version >= (4, 2) else "BLENDER_EEVEE"
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    sc.render.resolution_percentage = 25 if preview else 100
    sc.eevee.taa_render_samples = 8 if preview else 48
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = f"{OUT}/out/frame_"
    sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    sc.view_settings.exposure = -0.8
    sc.view_settings.look = "AgX - Medium High Contrast" if sc.view_settings.view_transform == "AgX" else "None"

def main():
    sc = clear()
    james, nla_end = build_character()
    # James walks along +Y toward the lamp; Walking clip carries root motion in the FBX
    ground = add_ground()
    lamp = place("street_lamp_01", (1.4, -3.6, 0), rot_z=90)
    place("concrete_road_barrier", (-3.0, 4.0, 0), rot_z=15)
    place("metal_trash_can", (2.3, 2.6, 0))
    place("trashbag", (2.0, 3.2, 0), rot_z=40)
    place("old_military_crate", (-2.4, -1.0, 0), rot_z=-20)
    place("barrel_03", (-2.8, 6.5, 0))
    for i in range(-3, 4):
        place("modular_chainlink_fence", (-4.5, i * 2.0, 0), rot_z=90)
    world_hdri()
    lights((1.4, -3.6))
    stop_frame = int(nla_end * 0.33)
    camera(james, stop_frame)
    render_settings(preview="--final" not in sys.argv)
    os.makedirs(f"{OUT}/out", exist_ok=True)
    bpy.ops.file.pack_all()  # embed textures so the .blend is self-contained (SheepIt needs this)
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/street_night.blend")
    print("SAVED", nla_end)

main()
