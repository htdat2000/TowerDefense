extends Node2D
## Homing projectile. Projectile art faces EAST, so rotation = travel direction.
const VFX = preload("res://scripts/vfx_one_shot.gd")

var speed := 500.0
var damage := 1.0
var target: Node2D
var target_pos := Vector2.ZERO
var impact: Dictionary = {}
var sprite: Sprite2D

func setup(tex: Texture2D, from: Vector2, tgt: Node2D, spd: float, dmg: float, impact_data: Dictionary) -> void:
    sprite = Sprite2D.new()
    sprite.texture = tex
    add_child(sprite)
    global_position = from
    target = tgt
    target_pos = tgt.global_position
    speed = spd
    damage = dmg
    impact = impact_data

func _process(delta: float) -> void:
    if is_instance_valid(target):
        target_pos = target.global_position
    var to := target_pos - global_position
    var step := speed * delta
    if to.length() <= step:
        _hit()
        return
    rotation = to.angle()
    global_position += to.normalized() * step

func _hit() -> void:
    if is_instance_valid(target) and target.has_method("take_damage"):
        target.call("take_damage", damage)
    if not impact.is_empty():
        VFX.play(get_parent().get_parent().get_node("Vfx"), String(impact["path"]), int(impact["frame"]), float(impact["fps"]), global_position)
    queue_free()
