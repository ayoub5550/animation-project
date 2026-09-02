extends Node
## Scripted gameplay demo for recording (Movie Maker mode). Drives the real player via Input actions:
## turns on the flashlight, walks in, then auto-aims at the nearest zombie, shoots, reloads and backs off.

const LEVEL := preload("res://levels/test_level.tscn")

var t := 0.0
var level: Node3D
var player: CharacterBody3D
var rig: Node3D
var _fire_timer := 0.0


func _ready() -> void:
	level = LEVEL.instantiate()
	add_child(level)
	player = level.get_node("Player")
	rig = player.get_node("CameraRig")
	Input.mouse_mode = Input.MOUSE_MODE_HIDDEN
	_stage_scene()


## Re-stage the test level for the camera: keep the fight in the open half of the room
## (the bed block occupies roughly x 1.5..9.7, z -1.7..0) and brighten it for the
## Compatibility renderer used when recording without a GPU.
func _stage_scene() -> void:
	player.global_position = Vector3(-2.0, 0.1, 6.0)
	player.flashlight.visible = true
	player.flashlight.light_energy = 6.0
	var zs := level.get_node("Zombies")
	var spots := {
		"Zombie1": [Vector3(-4.0, 0.0, -6.0), 14.0],   # Romero, walks in from the door side
		"Zombie2": [Vector3(-7.0, 0.0, -3.0), 12.0],   # Copzombie, lying, rises
		"Zombie3": [Vector3(6.5, 0.0, 4.0), 6.0],      # Zombiegirl runner, joins mid-fight
		"Zombie4": [Vector3(-8.5, 0.0, 2.0), 7.0],     # Warzombie from the left
	}
	for n in spots:
		var z: Node3D = zs.get_node(n)
		z.global_position = spots[n][0]
		z.detect_range = spots[n][1]
		z.look_at(player.global_position, Vector3.UP)
	var lamp: OmniLight3D = level.get_node("Lamp")
	lamp.global_position = Vector3(-2.0, 2.8, 0.0)
	lamp.light_energy = 5.0
	lamp.omni_range = 14.0
	var env: Environment = level.get_node("WorldEnvironment").environment
	env.ambient_light_energy = 0.7
	env.fog_density = 0.006
	level.get_node("Moonlight").light_energy = 0.6


func _physics_process(delta: float) -> void:
	t += delta
	if t < 0.6:
		return
	# Intro: slow look around, walk into the room
	if t < 3.5:
		rig._yaw = lerpf(0.35, -0.35, (t - 0.6) / 2.9)
		rig._pitch = -6.0
		if t > 1.5:
			Input.action_press("move_forward")
		return
	Input.action_release("move_forward")
	# Combat: lock onto the nearest live zombie, aim, fire, back away when it gets close
	var target := _nearest_zombie()
	if target == null:
		Input.action_release("aim"); Input.action_release("shoot"); Input.action_release("move_back")
		rig._yaw += 0.3 * delta  # victory pan
		return
	var head: Vector3 = target.global_position + Vector3(0, 1.35, 0)
	var eye: Vector3 = rig.camera.global_position
	var to := head - eye
	rig._yaw = lerp_angle(rig._yaw, atan2(-to.x, -to.z), 6.0 * delta)
	var flat := Vector2(to.x, to.z).length()
	rig._pitch = lerpf(rig._pitch, rad_to_deg(atan2(to.y, flat)), 6.0 * delta)
	Input.action_press("aim")
	var dist := player.global_position.distance_to(target.global_position)
	if dist < 3.5:
		Input.action_press("move_back")
	else:
		Input.action_release("move_back")
	_fire_timer -= delta
	if dist < 14.0 and _fire_timer <= 0.0 and not player.reloading:
		Input.action_press("shoot")
		_fire_timer = 0.8
	else:
		Input.action_release("shoot")
	if player.ammo_in_mag == 0 and not player.reloading:
		Input.action_press("reload")
	else:
		Input.action_release("reload")


func _nearest_zombie() -> Node3D:
	var best: Node3D = null
	var best_d := INF
	for z in get_tree().get_nodes_in_group("zombie"):
		if z.state == z.State.DEAD:
			continue
		var d: float = z.global_position.distance_to(player.global_position)
		if d < best_d:
			best_d = d; best = z
	return best
