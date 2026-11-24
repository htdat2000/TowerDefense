extends Node2D
## Monster with 4-direction animations (E, S, W, N). Names: idle_E, walk_S, attack_W, hit_N, death_E ... + spawn.
## Follows a Curve2D by distance. Walk animation speed is matched to ground speed using the stride value.
## VFX: emits vfx_requested (spawn / boss / death / ability particles); status overlays (freeze, slow, stun, burning, poison)
## are looping child sprites driven by data/status_effects.json.
## M3 (all from data/monsters.json):
##   armor                 0..0.9 = fraction of DIRECT damage removed (burning / poison DoT ignores armor).
##   ability.kind "burst"  periodic speed burst (speed_mult for duration s, every cooldown s), plays the attack animation as telegraph.
##   ability.kind "spore"  periodic spore burst: heals other living monsters within radius_cells by heal_frac of their max hp.
##                         Only fires when an injured ally is in range. Emits healed(m, amount) for each healed monster.
##   status_tint_strength  0..1, how strongly status tints show on this monster (default 1).
##   status_tints          optional per-status colour override, e.g. {"poison": [0.85, 1.0, 0.6]}.
## The health bar is a child (health_bar.gd), shown when hurt (always for bosses).

const SFB = preload("res://scripts/sprite_frames_builder.gd")
const Data = preload("res://scripts/data.gd")
const VFX = preload("res://scripts/vfx_library.gd")
const HealthBar = preload("res://scripts/health_bar.gd")
signal died(m)
signal reached_end(m)
signal damaged(m, amount: float, is_crit: bool)
signal healed(m, amount: float)
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
var armor := 0.0
var state := State.SPAWN
var dir := "E"
var sprite: AnimatedSprite2D
var shadow: Sprite2D
var bar                              # HealthBar script instance (dynamic on purpose)
var status_left: Dictionary = {}     # kind -> seconds remaining
var overlays: Dictionary = {}        # kind -> AnimatedSprite2D
var ability: Dictionary = {}
var _ability_kind := ""
var _ability_cd := 0.0
var _burst_left := 0.0
var _burst_mult := 1.0
var _hit_playing := false            # an animation (hit / attack) is locking the walk cycle
var _frame_scale := 1.0              # frame / 64: scales overlays and particles for 80 / 96 px monsters
var _fx_tint := Color.WHITE
var _tint_strength := 1.0
var _status_tints: Dictionary = {}

func setup(id: String, d: Dictionary, c: Curve2D) -> void:
    monster_id = id
    data = d
    curve = c
    speed = float(d["speed"])
    hp = float(d["hp"])
    max_hp = hp
    armor = clampf(float(d.get("armor", 0.0)), 0.0, 0.9)
    _frame_scale = float(d["frame"]) / 64.0
    _fx_tint = _color_from(d.get("tint", [1.0, 1.0, 1.0]))
    _tint_strength = clampf(float(d.get("status_tint_strength", 1.0)), 0.0, 1.0)
    var st: Variant = d.get("status_tints", {})
    if st is Dictionary:
        _status_tints = st
    var ab: Variant = d.get("ability", {})
    if ab is Dictionary:
        ability = ab
    _ability_kind = String(ability.get("kind", ""))
    _ability_cd = float(ability.get("first_delay", ability.get("cooldown", 5.0)))
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
    bar = HealthBar.new()
    bar.name = "HealthBar"
    bar.z_index = 2
    add_child(bar)
    bar.setup(float(d["frame"]) * 0.5, -float(d["frame"]) * 0.5 + 2.0, armor, bool(d.get("boss", false)))
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

func _update_bar() -> void:
    if bar != null:
        bar.set_fraction(hp / max_hp)

# ---------------------------------------------------------------- damage / heal
func take_damage(amount: float, crit: bool = false) -> void:
    if state == State.DYING:
        return
    var dealt := amount * (1.0 - armor)
    damaged.emit(self, dealt, crit)
    _apply_damage(dealt, true)

func _apply_damage(amount: float, show_hit: bool) -> void:
    hp -= amount
    _update_bar()
    if hp <= 0.0:
        _die()
    elif show_hit and state == State.WALK:
        _hit_playing = true
        sprite.speed_scale = 1.0
        sprite.play("hit_" + dir)

func heal(amount: float) -> void:
    if state == State.DYING or amount <= 0.0 or hp >= max_hp:
        return
    var gained := minf(amount, max_hp - hp)
    hp += gained
    _update_bar()
    healed.emit(self, gained)

func _die() -> void:
    state = State.DYING
    _hit_playing = false
    _burst_left = 0.0
    _clear_status()
    if bar != null:
        bar.visible = false
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

func _status_mult() -> float:
    var m := 1.0
    for k in status_left.keys():
        m *= float(_status_defs[k].get("speed_mult", 1.0))
    return m

func _speed_now() -> float:
    var m := _status_mult()
    if _burst_left > 0.0:
        m *= _burst_mult
    return speed * m

func _status_tint(kind: String) -> Color:
    var t: Variant = _status_tints.get(kind, _status_defs[kind].get("tint", null))
    if t == null:
        return Color.WHITE
    return Color.WHITE.lerp(_color_from(t), _tint_strength)

func _refresh_status() -> void:
    var tint := Color.WHITE
    for k in status_left.keys():
        tint *= _status_tint(String(k))
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
        _apply_damage(dps * delta, false)     # DoT ignores armor

# ---------------------------------------------------------------- abilities (data "ability")
func _tick_ability(delta: float) -> void:
    if _ability_kind == "" or _status_mult() <= 0.0:     # frozen / stunned: ability timers wait
        return
    if _burst_left > 0.0:
        _burst_left -= delta
        if _burst_left <= 0.0:
            _burst_left = 0.0
            _refresh_status()
    _ability_cd -= delta
    if _ability_cd > 0.0:
        return
    match _ability_kind:
        "burst":
            _start_burst()
        "spore":
            _try_spore()
        _:
            _ability_cd = 999.0

func _play_ability_anim() -> void:
    _hit_playing = true
    sprite.speed_scale = 1.0
    sprite.play("attack_" + dir)

func _emit_ability_vfx() -> void:
    var vname := String(ability.get("vfx", ""))
    if vname == "":
        return
    vfx_requested.emit(vname, global_position, float(ability.get("vfx_scale", 1.0)),
        _color_from(ability.get("vfx_tint", [1.0, 1.0, 1.0])))

func _start_burst() -> void:
    _burst_left = float(ability.get("duration", 1.2))
    _burst_mult = float(ability.get("speed_mult", 1.5))
    _ability_cd = float(ability.get("cooldown", 4.5))
    _emit_ability_vfx()
    _play_ability_anim()
    _refresh_status()

func _spore_radius() -> float:
    return float(ability.get("radius_cells", 1.5)) * 64.0

func _try_spore() -> void:
    if not _injured_ally_near(_spore_radius()):
        _ability_cd = 0.4                 # nothing to heal: look again shortly
        return
    _ability_cd = float(ability.get("cooldown", 5.0))
    _play_ability_anim()
    get_tree().create_timer(float(ability.get("windup", 0.3))).timeout.connect(_release_spores)

func _injured_ally_near(r: float) -> bool:
    for n in get_tree().get_nodes_in_group("monsters"):
        if not is_instance_valid(n):
            continue
        var m := n as Node2D
        if m == null or m == self or not m.has_method("is_alive") or not bool(m.call("is_alive")):
            continue
        if float(m.get("hp")) < float(m.get("max_hp")) and m.global_position.distance_to(global_position) <= r:
            return true
    return false

func _release_spores() -> void:
    if state == State.DYING:
        return
    var r := _spore_radius()
    var frac := float(ability.get("heal_frac", 0.2))
    _emit_ability_vfx()
    for n in get_tree().get_nodes_in_group("monsters"):
        if not is_instance_valid(n):
            continue
        var m := n as Node2D
        if m == null or m == self or not m.has_method("heal"):
            continue
        if m.global_position.distance_to(global_position) <= r:
            m.call("heal", float(m.get("max_hp")) * frac)

# ---------------------------------------------------------------- movement
func _process(delta: float) -> void:
    if state == State.DYING:
        return
    _tick_status(delta)
    if state != State.WALK:
        return
    _tick_ability(delta)
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
    elif a.begins_with("hit_") or a.begins_with("attack_"):
        _hit_playing = false
        if state == State.WALK:
            _play_walk(false)
    elif a.begins_with("death_"):
        queue_free()
