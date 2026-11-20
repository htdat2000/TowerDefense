extends Node2D
## Monster with 4-direction animations (E, S, W, N). Names: idle_E, walk_S, attack_W, hit_N, death_E ... + spawn.
## Follows a Curve2D by distance. Walk animation speed is matched to ground speed using the stride value.

const SFB = preload("res://scripts/sprite_frames_builder.gd")
signal died(m)
signal reached_end(m)
enum State { SPAWN, WALK, DYING }

const DIRS := ["E", "S", "W", "N"]
const ANIMS := {"idle": [8.0, true], "walk": [12.0, true], "attack": [14.0, false], "hit": [12.0, false], "death": [12.0, false]}

var monster_id := ""
var data: Dictionary = {}
var curve: Curve2D
var dist := 0.0
var speed := 60.0
var hp := 10.0
var max_hp := 10.0
var state := State.SPAWN
var dir := "E"
var sprite: AnimatedSprite2D
var shadow: Sprite2D
var _hit_playing := false

func setup(id: String, d: Dictionary, c: Curve2D) -> void:
    monster_id = id
    data = d
    curve = c
    speed = float(d["speed"])
    hp = float(d["hp"])
    max_hp = hp
    var folder := "res://assets/Monsters/Grassland/%s/" % d["folder"]
    shadow = Sprite2D.new()
    shadow.texture = load(folder + "monster_%s_shadow.png" % id) as Texture2D
    add_child(shadow)
    sprite = AnimatedSprite2D.new()
    add_child(sprite)
    sprite.sprite_frames = _build_frames(folder)
    sprite.animation_finished.connect(_on_anim_finished)
    global_position = curve.sample_baked(0.0)
    sprite.play("spawn")

func _build_frames(folder: String) -> SpriteFrames:
    var fs := Vector2i(int(data["frame"]), int(data["frame"]))
    var f := SFB.new_frames()
    SFB.add_strip(f, "spawn", folder + "Strips/monster_%s_spawn_E.png" % monster_id, fs, 12.0, false)
    for anim in ANIMS.keys():
        for dn in DIRS:
            SFB.add_strip(f, "%s_%s" % [anim, dn], folder + "Strips/monster_%s_%s_%s.png" % [monster_id, anim, dn],
                fs, float(ANIMS[anim][0]), bool(ANIMS[anim][1]))
    return f

func is_alive() -> bool:
    return state != State.DYING

func take_damage(amount: float) -> void:
    if state == State.DYING:
        return
    hp -= amount
    queue_redraw()
    if hp <= 0.0:
        _die()
    elif state == State.WALK:
        _hit_playing = true
        sprite.speed_scale = 1.0
        sprite.play("hit_" + dir)

func _die() -> void:
    state = State.DYING
    _hit_playing = false
    sprite.speed_scale = 1.0
    sprite.play("death_" + dir)
    died.emit(self)

func _process(delta: float) -> void:
    if state != State.WALK:
        return
    dist += speed * delta
    var length := curve.get_baked_length()
    if dist >= length:
        reached_end.emit(self)
        queue_free()
        return
    var p := curve.sample_baked(dist)
    var ahead := curve.sample_baked(minf(dist + 4.0, length))
    global_position = p
    var v := ahead - p
    var nd := dir
    if absf(v.x) >= absf(v.y):
        nd = "E" if v.x >= 0.0 else "W"
    else:
        nd = "S" if v.y >= 0.0 else "N"
    if nd != dir:
        dir = nd
        if not _hit_playing:
            _play_walk(true)

func _play_walk(keep_frame: bool) -> void:
    var fr := sprite.frame
    sprite.speed_scale = speed / (float(data["stride"]) * 12.0 / 8.0)   # feet match ground speed
    sprite.play("walk_" + dir)
    if keep_frame:
        sprite.frame = fr

func _on_anim_finished() -> void:
    var a := String(sprite.animation)
    if a == "spawn":
        state = State.WALK
        _play_walk(false)
    elif a.begins_with("hit_"):
        _hit_playing = false
        _play_walk(false)
    elif a.begins_with("death_"):
        queue_free()

func _draw() -> void:
    if hp >= max_hp or state == State.DYING:
        return
    var y := -float(data["frame"]) * 0.5 + 2.0
    draw_rect(Rect2(-14, y, 28, 4), Color(0, 0, 0, 0.6))
    draw_rect(Rect2(-13, y + 1, 26.0 * clampf(hp / max_hp, 0.0, 1.0), 2), Color(0.35, 0.9, 0.35))
