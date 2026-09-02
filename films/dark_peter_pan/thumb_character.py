"""blender -b -P thumb_character.py -- <TPose.fbx> [<clip.fbx>] <out.png>  : render a lit turntable-style thumbnail."""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index("--")+1:]
tpose, out = args[0], args[-1]
clip = args[1] if len(args) == 3 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=tpose, ignore_leaf_bones=True)
new = [o for o in bpy.data.objects if o not in before]
arm = next(o for o in new if o.type == "ARMATURE")
if clip:
    arm.animation_data_create(); arm.animation_data.action = None
    b2 = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=clip, ignore_leaf_bones=True)
    n2 = [o for o in bpy.data.objects if o not in b2]
    a2 = next(o for o in n2 if o.type == "ARMATURE")
    arm.animation_data.action = a2.animation_data.action
    for o in n2: bpy.data.objects.remove(o, do_unlink=True)
    sc.frame_set(20)
# Mixamo materials come in glossy: fix roughness/specular, optionally darken clothes
import os
DARKEN = os.environ.get("DARKEN_MATS", "")  # comma list of OBJECT-name substrings (materials are shared atlases) to tint dark
for o in [o for o in new if o.type == "MESH"]:
    for slot in o.material_slots:
        m = slot.material
        if not (m and m.use_nodes): continue
        nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
        if not b: continue
        for l in [l for l in nt.links if l.to_socket == b.inputs["Roughness"]]: nt.links.remove(l)
        b.inputs["Roughness"].default_value = 0.75
        b.inputs["Specular IOR Level"].default_value = 0.3
        if DARKEN and any(k.lower() in o.name.lower() for k in DARKEN.split(",")):
            m = m.copy(); slot.material = m; nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
            link = next((l for l in nt.links if l.to_socket == b.inputs["Base Color"]), None)
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1.0
            mix.inputs[7].default_value = (0.10, 0.16, 0.08, 1)  # dark mossy green
            if link: nt.links.new(link.from_socket, mix.inputs[6])
            else: mix.inputs[6].default_value = b.inputs["Base Color"].default_value
            nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    print("MATS", o.name, [s.material.name for s in o.material_slots if s.material])
bpy.context.view_layer.update()
meshes = [o for o in new if o.type == "MESH"]
zs = [(o.matrix_world @ Vector(b)).z for o in meshes for b in o.bound_box]
h = max(zs) - min(zs); z0 = min(zs)
# ground + world
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,z0))
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.12,0.12,0.14,1)
def light(t, loc, e, size=2):
    bpy.ops.object.light_add(type=t, location=loc); L = bpy.context.object; L.data.energy = e
    if t == "AREA": L.data.size = size
    L.rotation_euler = (Vector(loc) - Vector((0,0,z0+h*0.5))).to_track_quat('Z','Y').to_euler()
    return L
light("AREA", (2.5,-3,z0+h*1.2), 400, 3); light("AREA", (-3,-2,z0+h*0.9), 150, 3); light("AREA", (0,4,z0+h*1.5), 200, 3)
cam = bpy.data.cameras.new("C"); co = bpy.data.objects.new("Cam", cam); sc.collection.objects.link(co); sc.camera = co
co.location = (0.6*h, -2.6*h, z0 + h*0.55); co.rotation_euler = (Vector(co.location) - Vector((0,0,z0+h*0.5))).to_track_quat('Z','Y').to_euler()
cam.lens = 50
sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.use_denoising = True; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = 600, 900
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("THUMB", out, "height", round(h,2))
