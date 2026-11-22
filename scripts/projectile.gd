extends Node2D
## Homing projectile. Projectile art faces EAST, so rotation = travel direction.
## On hit: damage (with crit flag), optional status effects (tower level data "statuses"), optional splash, impact strip.
## Splash (M2): splash = {"radius_px": float, "mult": float, "statuses": bool}. Every other living monster in the group
## "monsters" within radius_px of the impact takes damage * mult (no crit); statuses are applied to them only if
## splash["statuses"] is true. The primary target always takes full damage and its statuses.
const VFX = preload("res://scripts/vfx_one_shot.gd")

var speed := 500.0
var damage := 1.0
var is_crit := false
var statuses: Array = []
var splash: Dictionary = {}
var target: Node2D
var target_pos := Vector2.ZERO
var impact: Dictionary = {}
var sprite: Sprite2D

func setup(tex: Texture2D, from: Vector2, tgt: Node2D, spd: float, dmg: float, impact_data: Dictionary,
        crit: bool = false, status_list: Array = [], splash_data: Dictionary = {}) -> void:
    sprite = Sprite2D.new()
    sprite.texture = tex
    add_child(sprite)
    global_position = from
    target = tgt
    target_pos = tgt.global_position
    speed = spd
    damage = dmg
    impact = impact_data
    is_crit = crit
    statuses = status_list
    splash = splash_data

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
    var primary: Node2D = null
    if is_instance_valid(target):
        primary = target
        _damage_one(target, damage, is_crit, true)
    _apply_splash(primary)
    if not impact.is_empty():
        VFX.play(get_parent().get_parent().get_node("Vfx"), String(impact["path"]), int(impact["frame"]), float(impact["fps"]), global_position)
    queue_free()

func _damage_one(m: Node, dmg: float, crit: bool, with_statuses: bool) -> void:
    if dmg > 0.0 and m.has_method("take_damage"):
        m.call("take_damage", dmg, crit)
    if with_statuses and m.has_method("apply_status"):
        for s in statuses:
            if randf() <= float(s.get("chance", 1.0)):
                m.call("apply_status", String(s["kind"]), float(s["duration"]))

func _apply_splash(primary: Node2D) -> void:
    var radius := float(splash.get("radius_px", 0.0))
    if radius <= 0.0:
        return
    var mult := float(splash.get("mult", 0.5))
    var with_statuses := bool(splash.get("statuses", false))
    for n in get_tree().get_nodes_in_group("monsters"):
        if not is_instance_valid(n) or n == primary:
            continue
        var m := n as Node2D
        if m == null:
            continue
        if m.has_method("is_alive") and not bool(m.call("is_alive")):
            continue
        if m.global_position.distance_to(global_position) <= radius:
            _damage_one(m, damage * mult, false, with_statuses)
