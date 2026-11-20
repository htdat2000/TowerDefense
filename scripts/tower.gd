extends Node2D
## Tower = fixed BASE layer + rotating HEAD layer (+ separate shadow).
## Base frames: build / idle / destroyed. Head frames: idle / attack (head art faces EAST, pivot = centre).
## Towers 'build' first; after that they can fire. upgrade() swaps to the next of 5 levels.

const SFB = preload("res://scripts/sprite_frames_builder.gd")
signal fired(tower: Node2D, target: Node2D)
signal destroyed_done(tower: Node2D)

var tower_id := ""
var level := 1
var data: Dictionary = {}
var built := false
var target: Node2D = null
var base: AnimatedSprite2D
var head: AnimatedSprite2D
var shadow: Sprite2D
var _cooldown_left := 0.0
var _fire_target: Node2D = null
var _event_done := true

func setup(id: String, tower_data: Dictionary, start_level := 1) -> void:
    tower_id = id
    data = tower_data
    level = start_level
    shadow = Sprite2D.new()
    shadow.texture = load(_path("shadow")) as Texture2D
    add_child(shadow)
    base = AnimatedSprite2D.new()
    add_child(base)
    head = AnimatedSprite2D.new()
    add_child(head)
    head.visible = false
    base.animation_finished.connect(_on_base_finished)
    head.animation_finished.connect(_on_head_finished)
    head.frame_changed.connect(_on_head_frame)
    _reload_frames()

func _path(suffix: String) -> String:
    if suffix == "shadow":
        return "res://assets/Towers/%s/tower_%s_shadow.png" % [data["folder"], tower_id]
    return "res://assets/Towers/%s/tower_%s_level_%02d_%s.png" % [data["folder"], tower_id, level, suffix]

func _reload_frames() -> void:
    var fs := Vector2i(int(data["frame"]), int(data["frame"]))
    var bf := SFB.new_frames()
    SFB.add_strip(bf, "build", _path("spawn"), fs, 14.0, false)
    SFB.add_strip(bf, "idle", _path("base_idle"), fs, 8.0, true)
    SFB.add_strip(bf, "destroyed", _path("destroyed"), fs, 12.0, false)
    base.sprite_frames = bf
    var hf := SFB.new_frames()
    SFB.add_strip(hf, "idle", _path("head_idle"), fs, 8.0, true)
    SFB.add_strip(hf, "attack", _path("head_attack"), fs, 16.0, false)
    head.sprite_frames = hf

# ---- gameplay-facing API
func build() -> void:
    built = false
    head.visible = false
    base.play("build")

func upgrade() -> bool:
    if level >= 5 or not built:
        return false
    level += 1
    _reload_frames()
    base.play("idle")
    head.play("idle")
    var tw := create_tween()
    tw.tween_property(self, "modulate", Color(1.7, 1.7, 1.7), 0.10)
    tw.tween_property(self, "modulate", Color(1, 1, 1), 0.25)
    return true

func destroy() -> void:
    built = false
    head.visible = false
    base.play("destroyed")

func damage() -> float:
    return float(data["damage"]) * (1.0 + 0.6 * (level - 1))      # PLACEHOLDER scaling

func range_px() -> float:
    return float(data["range_cells"]) * 64.0 * (1.0 + 0.08 * (level - 1))   # PLACEHOLDER

func cooldown() -> float:
    return float(data["cooldown"]) * (1.0 - 0.08 * (level - 1))   # PLACEHOLDER

func muzzle_position() -> Vector2:
    return global_position + Vector2.from_angle(head.rotation) * float(data["muzzle"])

func try_fire(t: Node2D) -> bool:
    if not built or _cooldown_left > 0.0 or head.animation == "attack":
        return false
    _fire_target = t
    _event_done = false
    _cooldown_left = cooldown()
    head.play("attack")
    return true

# ---- internals
func _process(delta: float) -> void:
    _cooldown_left = maxf(0.0, _cooldown_left - delta)
    if not built or not bool(data["head_rotates"]):
        return
    var aim := head.rotation
    if is_instance_valid(target):
        aim = (target.global_position - global_position).angle()
    elif bool(data.get("idle_sweep", false)):
        aim = sin(Time.get_ticks_msec() / 700.0) * 0.25
    head.rotation = lerp_angle(head.rotation, aim, clampf(delta * 12.0, 0.0, 1.0))

func _on_base_finished() -> void:
    if base.animation == "build":
        built = true
        base.play("idle")
        head.visible = true
        head.play("idle")
    elif base.animation == "destroyed":
        destroyed_done.emit(self)

func _on_head_finished() -> void:
    if head.animation == "attack":
        head.play("idle")

func _on_head_frame() -> void:
    if head.animation == "attack" and not _event_done and head.frame >= int(data["event_frame"]):
        _event_done = true
        if is_instance_valid(_fire_target):
            fired.emit(self, _fire_target)
