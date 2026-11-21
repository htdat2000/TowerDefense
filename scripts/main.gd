extends Node2D
## Playable art prototype: Grassland map + 3 towers (5 levels) + 5 monsters + Phase 5 VFX.
## Controls: pick a tower button -> hover map (green = valid, red = invalid) -> left click places it.
## Left click on a placed tower (when no tower is selected) upgrades it (Lv1 -> Lv5). Right click cancels.
## Debug keys: F1 freeze, F2 slow, F3 burning, F4 poison, F5 stun (all monsters, 4 s), F6 spawn a boss Treant.
## All gameplay numbers (damage, hp, speed, range, crit, status) are PLACEHOLDERS from data/*.json.

const Data = preload("res://scripts/data.gd")
const LevelScript = preload("res://scripts/level.gd")
const TowerScript = preload("res://scripts/tower.gd")
const MonsterScript = preload("res://scripts/monster.gd")
const ProjectileScript = preload("res://scripts/projectile.gd")
const VFX = preload("res://scripts/vfx_library.gd")
const DamageNumber = preload("res://scripts/damage_number.gd")

const DEBUG_STATUS_KEYS := {KEY_F1: "freeze", KEY_F2: "slow", KEY_F3: "burning", KEY_F4: "poison", KEY_F5: "stun"}

var level
var towers_data: Dictionary
var monsters_data: Dictionary
var towers: Array = []
var monsters: Array = []
var selected_id := ""
var hint: Label

func _ready() -> void:
    towers_data = Data.load_json("res://data/towers.json")
    monsters_data = Data.load_json("res://data/monsters.json")
    level = LevelScript.new()
    add_child(level)
    level.build()
    _build_ui()
    _place_tower("archer", Vector2i(5, 3), 3)
    _place_tower("stone", Vector2i(10, 6), 4)
    _place_tower("frost", Vector2i(13, 4), 5)

func _build_ui() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var bar := HBoxContainer.new()
    bar.position = Vector2(12, 8)
    layer.add_child(bar)
    for id in ["stone", "archer", "frost"]:
        var b := Button.new()
        b.text = String(towers_data[id]["name"])
        b.pressed.connect(_select_tower.bind(id))
        bar.add_child(b)
    var wave := Button.new()
    wave.text = "Send wave"
    wave.pressed.connect(_send_wave)
    bar.add_child(wave)
    var gb := Button.new()
    gb.text = "Toggle grid"
    gb.pressed.connect(func(): level.grid_renderer.grid_visible = not level.grid_renderer.grid_visible)
    bar.add_child(gb)
    hint = Label.new()
    hint.position = Vector2(12, 716)
    hint.text = "Pick a tower, click a green cell to build. Click a tower to upgrade (Lv 1-5). Right click cancels.\nDebug: F1 freeze  F2 slow  F3 burning  F4 poison  F5 stun  F6 boss"
    layer.add_child(hint)

# ---------------------------------------------------------------- VFX entry point (towers and monsters emit vfx_requested)
func _play_vfx(vfx_name: String, pos: Vector2, scale_f: float = 1.0, tint: Color = Color.WHITE) -> void:
    VFX.play_once(level.vfx, vfx_name, pos, scale_f, tint)

func _select_tower(id: String) -> void:
    selected_id = "" if selected_id == id else id
    _update_preview()

func _tower_cell_size() -> Vector2i:
    return Vector2i(1, 1)

func _update_preview() -> void:
    var pl = level.placement
    if selected_id == "":
        pl.clear()
        return
    var td: Dictionary = towers_data[selected_id]
    var cell: Vector2i = level.grid.world_to_cell(get_global_mouse_position())
    pl.available = level.available_cells()
    pl.occupied = level.grid.occupancy.keys()
    pl.preview_active = level.grid.in_bounds(cell)
    pl.preview_cell = cell
    pl.preview_size = _tower_cell_size()
    pl.preview_valid = level.grid.can_place(cell, pl.preview_size)
    pl.range_px = float(td["range_cells"]) * 64.0
    var base_tex := load("res://assets/Towers/%s/tower_%s_level_01_base.png" % [td["folder"], selected_id]) as Texture2D
    var head_tex := load("res://assets/Towers/%s/tower_%s_level_01_head_static.png" % [td["folder"], selected_id]) as Texture2D
    pl.ghost_textures = [base_tex, head_tex]
    pl.queue_redraw()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseMotion:
        _update_preview()
    elif event is InputEventMouseButton:
        var mb := event as InputEventMouseButton
        if not mb.pressed:
            return
        if mb.button_index == MOUSE_BUTTON_LEFT:
            _on_left_click()
        elif mb.button_index == MOUSE_BUTTON_RIGHT:
            selected_id = ""
            level.placement.clear()

func _unhandled_key_input(event: InputEvent) -> void:
    var k := event as InputEventKey
    if k == null or not k.pressed or k.echo:
        return
    if DEBUG_STATUS_KEYS.has(k.keycode):
        for m in monsters:
            if is_instance_valid(m) and m.is_alive():
                m.apply_status(String(DEBUG_STATUS_KEYS[k.keycode]), 4.0)
    elif k.keycode == KEY_F6:
        _spawn_monster("treant", true)

func _on_left_click() -> void:
    var cell: Vector2i = level.grid.world_to_cell(get_global_mouse_position())
    if selected_id != "":
        if level.grid.can_place(cell, _tower_cell_size()):
            _place_tower(selected_id, cell, 1)
            selected_id = ""
            level.placement.clear()
    else:
        var t = level.grid.occupancy.get(cell)
        if t != null and is_instance_valid(t):
            t.upgrade()

func _place_tower(id: String, cell: Vector2i, start_level: int) -> void:
    var t = TowerScript.new()
    level.actors.add_child(t)
    t.setup(id, towers_data[id], start_level)
    t.position = level.grid.footprint_center(cell, _tower_cell_size())
    t.fired.connect(_on_tower_fired)
    t.vfx_requested.connect(_play_vfx)
    level.grid.place(cell, _tower_cell_size(), t)
    towers.append(t)
    t.build()

func _spawn_monster(id: String, as_boss := false) -> void:
    var m = MonsterScript.new()
    level.actors.add_child(m)
    m.vfx_requested.connect(_play_vfx)
    m.damaged.connect(_on_monster_damaged)
    var d: Dictionary = monsters_data[id].duplicate()
    if as_boss:
        d["boss"] = true
    m.setup(id, d, level.path_curve)
    monsters.append(m)

func _send_wave() -> void:
    _play_vfx("wave_transition", level.path_curve.get_point_position(1), 1.0)
    for id in ["slime", "goblin", "boar", "mushroom", "treant"]:
        _spawn_monster(id)
        await get_tree().create_timer(1.2).timeout

func _on_monster_damaged(m, amount: float, is_crit: bool) -> void:
    if not is_instance_valid(m):
        return
    var top: float = float(m.data["frame"]) * 0.4
    var n = DamageNumber.new()
    level.vfx.add_child(n)
    n.position = m.global_position + Vector2(0.0, -top)
    n.setup(maxi(int(round(amount)), 1), "crit" if is_crit else "normal")
    if is_crit:
        _play_vfx("critical_hit", m.global_position, float(m.data["frame"]) / 64.0)

func _on_tower_fired(tower, tgt) -> void:
    if not is_instance_valid(tgt):
        return
    var td: Dictionary = tower.data
    var crit: bool = randf() < float(td.get("crit_chance", 0.0))
    var dmg: float = tower.damage() * (float(td.get("crit_mult", 2.0)) if crit else 1.0)
    var p = ProjectileScript.new()
    level.projectiles.add_child(p)
    p.setup(load(String(td["projectile"])) as Texture2D, tower.muzzle_position(), tgt,
        float(td["projectile_speed"]), dmg, td["impact"], crit, td.get("statuses", []))

func _process(_delta: float) -> void:
    monsters = monsters.filter(func(m): return is_instance_valid(m))
    for t in towers:
        if not is_instance_valid(t) or not t.built:
            continue
        var best = null
        var best_d: float = t.range_px()
        for m in monsters:
            if not m.is_alive():
                continue
            var d: float = t.global_position.distance_to(m.global_position)
            if d <= best_d:
                best = m
                best_d = d
        t.target = best
        if best != null:
            t.try_fire(best)
