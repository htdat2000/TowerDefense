extends Node2D
## Tower = fixed BASE layer + rotating HEAD layer (+ separate shadow).
## Base frames: build / idle / destroyed. Head frames: idle / attack (head art faces EAST, pivot = centre).
## Towers 'build' first; after that they can fire. upgrade() plays the upgrade VFX and swaps to the next of 5 levels.
## VFX are requested through the vfx_requested signal (the level owner plays them), so this script has no scene dependencies.
## Economy: cost, upgrade_costs and sell_refund come from data/towers.json. `invested` = gold put into this tower;
## main.gd charges GameState, the tower only reports prices (upgrade_cost, sell_value) and tracks `invested`.
## M2: every combat number comes from data/towers.json levels[] (index 0 = Lv1) through stat() / stat_at().
## A key missing in the level entry falls back to the tower's top-level key, then to the given default.

const SFB = preload("res://scripts/sprite_frames_builder.gd")
const Targeting = preload("res://scripts/targeting.gd")
signal fired(tower: Node2D, target: Node2D)
signal destroyed_done(tower: Node2D)
signal vfx_requested(vfx_name: String, pos: Vector2, scale_f: float, tint: Color)
signal state_changed(tower: Node2D)      # build finished or upgrade finished (UI refresh)

const MAX_LEVEL := 5
const UPGRADE_FPS := 14.0          # vfx_tower_upgrade fps
const UPGRADE_SWAP_FRAME := 4      # frame 4 of vfx_tower_upgrade is the white flash that hides the sprite swap

var tower_id := ""
var level := 1
var data: Dictionary = {}
var built := false
var invested := 0
var targeting := "first"
var cell := Vector2i.ZERO             # top-left grid cell, set by main.gd
var footprint := Vector2i(1, 1)       # size in 64 px cells, from data "footprint"
var target: Node2D = null
var base: AnimatedSprite2D
var head: AnimatedSprite2D
var shadow: Sprite2D
var _cooldown_left := 0.0
var _fire_target: Node2D = null
var _event_done := true
var _upgrading := false

static func footprint_of(tower_data: Dictionary) -> Vector2i:
    var fp: Array = tower_data.get("footprint", [1, 1])
    if fp.size() < 2:
        return Vector2i(1, 1)
    return Vector2i(maxi(int(fp[0]), 1), maxi(int(fp[1]), 1))

func setup(id: String, tower_data: Dictionary, start_level := 1) -> void:
    tower_id = id
    data = tower_data
    level = clampi(start_level, 1, max_level())
    footprint = footprint_of(data)
    targeting = String(data.get("targeting", "first"))
    if not Targeting.is_valid_mode(targeting):
        targeting = "first"
    invested = int(data.get("cost", 0))
    var costs: Array = data.get("upgrade_costs", [])
    for i in range(mini(level - 1, costs.size())):
        invested += int(costs[i])
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

# ---- stats (all from data)
func max_level() -> int:
    var levels: Array = data.get("levels", [])
    if levels.is_empty():
        return MAX_LEVEL
    return mini(MAX_LEVEL, levels.size())

func stat_at(lv: int, key: String, fallback: Variant = 0.0) -> Variant:
    var levels: Array = data.get("levels", [])
    if not levels.is_empty():
        var entry: Dictionary = levels[clampi(lv - 1, 0, levels.size() - 1)]
        if entry.has(key):
            return entry[key]
    return data.get(key, fallback)

func stat(key: String, fallback: Variant = 0.0) -> Variant:
    return stat_at(level, key, fallback)

func damage() -> float:
    return float(stat("damage", 1.0))

func range_px() -> float:
    return float(stat("range_cells", 3.0)) * 64.0

func cooldown() -> float:
    return maxf(float(stat("cooldown", 1.0)), 0.05)

func crit_chance() -> float:
    return float(stat("crit_chance", 0.0))

func crit_mult() -> float:
    return float(stat("crit_mult", 2.0))

func statuses() -> Array:
    var s: Variant = stat("statuses", [])
    if s is Array:
        return s as Array
    return []

func splash_radius_px() -> float:
    return float(stat("splash_radius_cells", 0.0)) * 64.0

func splash_mult() -> float:
    return float(stat("splash_mult", 0.5))

func splash_statuses() -> bool:
    return bool(stat("splash_statuses", false))

func cycle_targeting() -> void:
    targeting = Targeting.next_mode(targeting)

# ---- economy (prices come from data, charging is done by main.gd)
func upgrade_cost() -> int:
    var costs: Array = data.get("upgrade_costs", [])
    if level >= max_level() or level - 1 >= costs.size():
        return -1
    return int(costs[level - 1])

func can_upgrade() -> bool:
    return built and not _upgrading and upgrade_cost() >= 0

func can_sell() -> bool:
    return built and not _upgrading

func sell_value() -> int:
    return floori(float(invested) * float(data.get("sell_refund", 0.7)))

# ---- gameplay-facing API
func build() -> void:
    built = false
    head.visible = false
    base.play("build")
    vfx_requested.emit("tower_spawn_particles", global_position, 1.0, Color.WHITE)

func upgrade() -> bool:
    if not can_upgrade():
        return false
    invested += upgrade_cost()
    _upgrading = true
    vfx_requested.emit("tower_upgrade", global_position, 1.0, Color.WHITE)
    get_tree().create_timer(float(UPGRADE_SWAP_FRAME) / UPGRADE_FPS).timeout.connect(_finish_upgrade)
    return true

func _finish_upgrade() -> void:
    level += 1
    _reload_frames()
    base.play("idle")
    head.play("idle")
    _upgrading = false
    state_changed.emit(self)

func destroy() -> void:
    built = false
    head.visible = false
    base.play("destroyed")
    vfx_requested.emit("tower_destruction_particles", global_position, 1.0, Color.WHITE)

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
        state_changed.emit(self)
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
