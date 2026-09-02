extends SceneTree
## Headless tool: builds res://characters/mixamo/<Name>/<Name>.tscn from Mixamo FBX exports.
##   <Name>_TPose.fbx  = skinned character (download "with skin")
##   <Name>@<Anim>.fbx = animation exported for that character ("without skin")
## All animations are merged into one AnimationLibrary on an AnimationPlayer next to the model.
## Run (after the editor/`--import` has imported the FBX files):
##   godot --headless --path . --script tools/build_characters.gd

const ROOT := "res://characters/mixamo"
const LOOPING := ["Idle", "Idle_Twitch", "Walk", "Run", "Crawl", "Pistol_Idle", "Pistol_Walk",
	"Pistol_Walk_Back", "Pistol_Strafe_L", "Pistol_Strafe_R", "Pistol_Run"]

func _init() -> void:
	var root_dir := DirAccess.open(ROOT)
	for cname in root_dir.get_directories():
		var dir := DirAccess.open(ROOT + "/" + cname)
		var tpose := ""
		var anims: Array[String] = []
		for f in dir.get_files():
			if not f.ends_with(".fbx"): continue
			if f.get_basename().ends_with("_TPose"): tpose = ROOT + "/" + cname + "/" + f
			elif "@" in f: anims.append(ROOT + "/" + cname + "/" + f)
		if tpose != "":
			_build(cname, tpose, anims)
	quit()

func _build(name: String, tpose_path: String, anims: Array[String]) -> void:
	var root := Node3D.new()
	root.name = name
	var model: Node3D = (load(tpose_path) as PackedScene).instantiate()
	model.name = "Model"
	root.add_child(model); model.owner = root
	var skel: Skeleton3D = model.find_child("Skeleton3D", true, false)
	var ap := AnimationPlayer.new(); ap.name = "AnimationPlayer"
	root.add_child(ap); ap.owner = root
	ap.root_node = NodePath("..")
	var lib := AnimationLibrary.new()
	var skel_path := String(root.get_path_to(skel))
	for path in anims:
		var anim_name: String = path.get_file().get_basename().split("@")[1]
		var inst: Node = (load(path) as PackedScene).instantiate()
		var aap: AnimationPlayer = inst.find_child("AnimationPlayer", true, false)
		if aap != null:
			for lib_name in aap.get_animation_library_list():
				var l := aap.get_animation_library(lib_name)
				if l.get_animation_list().is_empty(): continue
				var anim: Animation = l.get_animation(l.get_animation_list()[0]).duplicate(true)
				for t in range(anim.get_track_count()):
					var p := anim.track_get_path(t)
					anim.track_set_path(t, NodePath(skel_path + ":" + p.get_concatenated_subnames()))
				anim.loop_mode = Animation.LOOP_LINEAR if anim_name in LOOPING else Animation.LOOP_NONE
				lib.add_animation(anim_name, anim)
				break
		inst.free()
	ap.add_animation_library("", lib)
	var packed := PackedScene.new()
	packed.pack(root)
	var out := ROOT + "/" + name + "/" + name + ".tscn"
	var err := ResourceSaver.save(packed, out)
	print("BUILT ", name, " anims=", lib.get_animation_list().size(), " -> ", out, " err=", err)
	root.free()
