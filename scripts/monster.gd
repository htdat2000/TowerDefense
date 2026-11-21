extends Node2D
## Monster with 4-direction animations (E, S, W, N). Names: idle_E, walk_S, attack_W, hit_N, death_E ... + spawn.
## Follows a Curve2D by distance. Walk animation speed is matched to ground speed using the stride value.
## VFX: emits vfx_requested (spawn / boss / death particles); status overlays (freeze, slow, stun, burning, poison)
## are looping child sprites driven by data/status_effects.json.

const SFB = preload("res://scripts/sprite_frames_builder.gd")
const Data = preload("res://scripts/data.gd")
const VFX = preload("res://scripts/vfx_library.gd")
signal died(m)
signal reached_end(m)
signal damaged(m, amount: float, is_crit: bool)
signal vfx_requested(vfx_name: String, pos: Vector2, scale_f: float, tint: Color)
enum State { SPAWN, WALK, DYING }

const DIRS := ["E", "S", "W", "N"]
const ANIMS := {"idle": [8.0, true], "walk": [12.0, true], "attack": [14.0, false], "hit": [12.0, false], "death": [12.0, false]}
const STATUS_PATH := "res://data/status_effects.json"
static var _status_defs: Dictionary = {}

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
var status_left: Dictionary = {}     # kind -> seconds remaining
var overlays: Dictionary = {}        # kind -> AnimatedSprite2D
var _hit_playing := false
var _frame_scale := 1.0              # frame / 64: scales overlays and particles for 80 / 96 px monsters
var _fx_tint := Color.WHITE

func setup(id: String, d: Dictionary, c: Curve2D) -> void:
    monster_id = id
    data = d
    curve = c
    speed = float(d["speed"])
    hp = float(d["hp"])
    max_hp = hp
    _frame_scale = float(d["frame"]) / 64.0
    _fx_tint = _color_from(d.get("tint", [1.0, 1.0, 1.0]))
    if _status_defs.is_empty():
        var sd = Data.load_json(STATUS_PATH)
        if sd is Dictionary:
            _status_defs = sd
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
    vfx_requested.emit("enemy_spawn_particles", global_position, _frame_scale, _fx_tint)
    if bool(d.get("boss", false)):
        vfx_requested.emit("boss_appearance", global_position, 1.0, Color.WHITE)

func _color_from(a: Array) -> Color:
    return Color(float(a[0]), float(a[1]), float(a[2]))

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

# ---------------------------------------------------------------- damage
func take_damage(amount: float, crit: bool = false) -> void:
    if state == State.DYING:
        return
    damaged.emit(self, amount, crit)
    _apply_damage(amount, true)

func _apply_damage(amount: float, show_hit: bool) -> void:
    hp -= amount
    queue_redraw()
    if hp <= 0.0:
        _die()
    elif show_hit and state == State.WALK:
        _hit_playing = true
        sprite.speed_scale = 1.0
        sprite.play("hit_" + dir)

func _die() -> void:
    state = State.DYING
    _hit_playing = false
    _clear_status()
    sprite.speed_scale = 1.0
    sprite.modulate = Color.WHITE
    sprite.play("death_" + dir)
    vfx_requested.emit("enemy_death_particles", global_position, _frame_scale, _fx_tint)
    died.emit(self)

# ---------------------------------------------------------------- status effects
func apply_status(kind: String, duration: float) -> void:
    if state == State.DYING or not _status_defs.has(kind):
        return
    status_left[kind] = maxf(float(status_left.get(kind, 0.0)), duration)
    if not overlays.has(kind):
        var o := VFX.make_loop("status_" + kind, _frame_scale)
        if o != null:
            add_child(o)
            overlays[kind] = o
    _refresh_status()

func _speed_mult() -> float:
    var m := 1.0
    for k in status_left.keys():
        m *= float(_status_defs[k].get("speed_mult", 1.0))
    return m

func _speed_now() -> float:
    return speed * _speed_mult()

func _refresh_status() -> void:
    var tint := Color.WHITE
    for k in status_left.keys():
        var t = _status_defs[k].get("tint", null)
        if t != null:
            tint *= _color_from(t)
    sprite.modulate = tint
    if state == State.WALK and not _hit_playing:
        sprite.speed_scale = _speed_now() / (float(data["stride"]) * 12.0 / 8.0)

func _clear_status() -> void:
    status_left.clear()
    for k in overlays.keys():
        (overlays[k] as Node).queue_free()
    overlays.clear()

func _tick_status(delta: float) -> void:
    if status_left.is_empty():
        return
    var dps := 0.0
    var expired: Array = []
    for k in status_left.keys():
        status_left[k] = float(status_left[k]) - delta
        dps += float(_status_defs[k].get("dps", 0.0))
        if float(status_left[k]) <= 0.0:
            expired.append(k)
    for k in expired:
        status_left.erase(k)
        if overlays.has(k):
            (overlays[k] as Node).queue_free()
            overlays.erase(k)
    if not expired.is_empty():
        _refresh_status()
    if dps > 0.0:
        _apply_damage(dps * delta, false)

# ---------------------------------------------------------------- movement
func _process(delta: float) -> void:
    if state == State.DYING:
        return
    _tick_status(delta)
    if state != State.WALK:
        return
    dist += _speed_now() * delta
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
    sprite.speed_scale = _speed_now() / (float(data["stride"]) * 12.0 / 8.0)   # feet match ground speed
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
