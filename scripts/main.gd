extends Node2D
## Playable prototype: Grassland map + data-driven waves + economy (M1).
## Controls: pick a tower button -> hover map (green = valid and affordable, red = not) -> left click places it.
## Left click a placed tower (nothing selected) upgrades it (costs gold). Right click: cancel selection, or sell the
## tower under the cursor when nothing is selected. "Start wave" sends the next wave from data/waves_*.json.
## Debug keys: F1 freeze, F2 slow, F3 burning, F4 poison, F5 stun (all monsters, 4 s), F6 spawn a boss Treant.
## All gameplay numbers (costs, rewards, waves, hp, damage) come from data/*.json and are PLACEHOLDERS.
## Run state (gold, lives, wave, speed) lives in the GameState autoload; wave timing in wave_manager.gd.

const Data = preload("res://scripts/data.gd")
const LevelScript = preload("res://scripts/level.gd")
const TowerScript = preload("res://scripts/tower.gd")
const MonsterScript = preload("res://scripts/monster.gd")
const ProjectileScript = preload("res://scripts/projectile.gd")
const VFX = preload("res://scripts/vfx_library.gd")
const DamageNumber = preload("res://scripts/damage_number.gd")
const WaveManager = preload("res://scripts/wave_manager.gd")

const LEVEL_DATA := "res://data/waves_grassland_01.json"
const DEBUG_STATUS_KEYS := {KEY_F1: "freeze", KEY_F2: "slow", KEY_F3: "burning", KEY_F4: "poison", KEY_F5: "stun"}

var level
var wave_manager
var towers_data: Dictionary
var monsters_data: Dictionary
var towers: Array = []
var monsters: Array = []
var selected_id := ""
var hint: Label
var msg: Label
var status: Label
var next_btn: Button
var speed_btn: Button
var overlay: Control
var result_title: Label
var result_detail: Label

func _ready() -> void:
    towers_data = Data.load_json("res://data/towers.json")
    monsters_data = Data.load_json("res://data/monsters.json")
    level = LevelScript.new()
    add_child(level)
    level.build()
    wave_manager = WaveManager.new()
    wave_manager.name = "WaveManager"
    add_child(wave_manager)
    wave_manager.load_level(LEVEL_DATA)
    get_tree().paused = false
    GameState.reset(wave_manager.start_gold(), wave_manager.start_lives(), wave_manager.total())
    _build_ui()
    wave_manager.spawn_requested.connect(_on_spawn_requested)
    wave_manager.wave_started.connect(_on_wave_started)
    wave_manager.wave_cleared.connect(_on_wave_cleared)
    wave_manager.all_waves_cleared.connect(_on_all_waves_cleared)
    GameState.gold_changed.connect(_on_gold_changed)
    GameState.lives_changed.connect(_on_lives_changed)
    GameState.wave_changed.connect(_on_wave_changed)
    GameState.speed_changed.connect(_on_speed_changed)
    GameState.game_over.connect(_on_game_over)
    for st in wave_manager.start_towers():
        var sd: Dictionary = st
        var c: Array = sd["cell"]
        _place_tower(String(sd["id"]), Vector2i(int(c[0]), int(c[1])), int(sd.get("level", 1)))
    _refresh_hud()

func _build_ui() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var bar := HBoxContainer.new()
    bar.position = Vector2(12, 8)
    layer.add_child(bar)
    for id in ["stone", "archer", "frost"]:
        var b := Button.new()
        b.text = "%s  %dg" % [towers_data[id]["name"], int(towers_data[id].get("cost", 0))]
        b.pressed.connect(_select_tower.bind(id))
        bar.add_child(b)
    next_btn = Button.new()
    next_btn.pressed.connect(_on_next_wave_pressed)
    bar.add_child(next_btn)
    speed_btn = Button.new()
    speed_btn.text = "Speed x1"
    speed_btn.pressed.connect(_on_speed_pressed)
    bar.add_child(speed_btn)
    var gb := Button.new()
    gb.text = "Toggle grid"
    gb.pressed.connect(func(): level.grid_renderer.grid_visible = not level.grid_renderer.grid_visible)
    bar.add_child(gb)
    status = Label.new()
    status.position = Vector2(12, 44)
    layer.add_child(status)
    msg = Label.new()
    msg.position = Vector2(12, 684)
    layer.add_child(msg)
    hint = Label.new()
    hint.position = Vector2(12, 716)
    hint.text = "Pick a tower, click a green cell to build. Click a tower to upgrade. Right click: cancel, or sell the tower under the cursor.\nDebug: F1 freeze  F2 slow  F3 burning  F4 poison  F5 stun  F6 boss"
    layer.add_child(hint)
    _build_overlay()

func _build_overlay() -> void:
    var ol := CanvasLayer.new()
    ol.layer = 10
    ol.process_mode = Node.PROCESS_MODE_ALWAYS     # keeps the Restart button alive while the tree is paused
    add_child(ol)
    var dim := ColorRect.new()
    dim.color = Color(0, 0, 0, 0.6)
    dim.set_anchors_preset(Control.PRESET_FULL_RECT)
    dim.visible = false
    ol.add_child(dim)
    overlay = dim
    var center := CenterContainer.new()
    center.set_anchors_preset(Control.PRESET_FULL_RECT)
    dim.add_child(center)
    var box := VBoxContainer.new()
    center.add_child(box)
    result_title = Label.new()
    result_title.add_theme_font_size_override("font_size", 48)
    result_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    box.add_child(result_title)
    result_detail = Label.new()
    result_detail.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    box.add_child(result_detail)
    var rb := Button.new()
    rb.text = "Restart"
    rb.pressed.connect(_on_restart_pressed)
    box.add_child(rb)

# ---------------------------------------------------------------- HUD / messages
func _refresh_hud() -> void:
    status.text = "Gold: %d    Lives: %d    Wave: %d / %d" % [GameState.gold, GameState.lives, GameState.wave, GameState.total_waves]
    var can: bool = wave_manager.can_start() and not GameState.finished
    next_btn.disabled = not can
    if wave_manager.running:
        next_btn.text = "Wave in progress"
    elif wave_manager.can_start():
        next_btn.text = "Start wave %d" % (wave_manager.next_index + 1)
    else:
        next_btn.text = "No more waves"

func _say(text: String) -> void:
    msg.text = text
    get_tree().create_timer(2.5).timeout.connect(_clear_msg.bind(text))

func _clear_msg(text: String) -> void:
    if is_instance_valid(msg) and msg.text == text:
        msg.text = ""

func _on_gold_changed(_gold: int) -> void:
    _refresh_hud()
    if selected_id != "":
        _update_preview()

func _on_lives_changed(_lives: int) -> void:
    _refresh_hud()

func _on_wave_changed(_wave: int, _total: int) -> void:
    _refresh_hud()

func _on_speed_changed(s: float) -> void:
    speed_btn.text = "Speed x%d" % int(s)

func _on_speed_pressed() -> void:
    GameState.cycle_speed()

func _on_restart_pressed() -> void:
    get_tree().paused = false
    get_tree().reload_current_scene()

# ---------------------------------------------------------------- waves / win / lose
func _on_next_wave_pressed() -> void:
    if GameState.finished:
        return
    wave_manager.start_next()

func _on_wave_started(index: int, _total: int) -> void:
    GameState.set_wave(index)
    _play_vfx("wave_transition", level.path_curve.get_point_position(1), 1.0)
    _refresh_hud()

func _on_wave_cleared(index: int, bonus: int) -> void:
    if GameState.finished:
        return
    GameState.add_gold(bonus)
    _say("Wave %d cleared! +%d gold" % [index, bonus])
    _refresh_hud()

func _on_all_waves_cleared() -> void:
    GameState.win()

func _on_game_over(won: bool) -> void:
    wave_manager.stop()
    result_title.text = "VICTORY!" if won else "DEFEAT"
    result_detail.text = "Waves sent: %d / %d    Lives left: %d    Gold: %d" % [GameState.wave, GameState.total_waves, GameState.lives, GameState.gold]
    overlay.visible = true
    get_tree().paused = true
    _refresh_hud()

func _on_spawn_requested(monster_id: String) -> void:
    _spawn_monster(monster_id, false, true)

# ---------------------------------------------------------------- VFX entry point (towers and monsters emit vfx_requested)
func _play_vfx(vfx_name: String, pos: Vector2, scale_f: float = 1.0, tint: Color = Color.WHITE) -> void:
    VFX.play_once(level.vfx, vfx_name, pos, scale_f, tint)

# ---------------------------------------------------------------- placement
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
    pl.preview_valid = level.grid.can_place(cell, pl.preview_size) and GameState.can_afford(int(td.get("cost", 0)))
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
            _on_right_click()

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
        if not level.grid.can_place(cell, _tower_cell_size()):
            return
        var cost := int(towers_data[selected_id].get("cost", 0))
        if not GameState.spend(cost):
            _say("Not enough gold (need %d)" % cost)
            return
        _place_tower(selected_id, cell, 1)
        selected_id = ""
        level.placement.clear()
    else:
        var t = level.grid.occupancy.get(cell)
        if t != null and is_instance_valid(t):
            _try_upgrade(t)

func _on_right_click() -> void:
    if selected_id != "":
        selected_id = ""
        level.placement.clear()
        return
    var cell: Vector2i = level.grid.world_to_cell(get_global_mouse_position())
    var t = level.grid.occupancy.get(cell)
    if t != null and is_instance_valid(t):
        _try_sell(t)

func _try_upgrade(t) -> void:
    var cost: int = t.upgrade_cost()
    if cost < 0:
        _say("Already max level" if t.level >= TowerScript.MAX_LEVEL else "Tower is busy")
        return
    if not t.can_upgrade():
        _say("Tower is busy")
        return
    if not GameState.spend(cost):
        _say("Not enough gold (need %d)" % cost)
        return
    t.upgrade()

func _try_sell(t) -> void:
    if not t.can_sell():
        _say("Tower is busy")
        return
    var value: int = t.sell_value()
    GameState.add_gold(value)
    level.grid.remove(t)
    towers.erase(t)
    _play_vfx("sell_effect", t.global_position, 1.0)
    t.queue_free()
    _say("Sold for %d gold" % value)

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

# ---------------------------------------------------------------- monsters
func _spawn_monster(id: String, as_boss := false, counted := false) -> void:
    var m = MonsterScript.new()
    m.set_meta("counted", counted)          # counted = belongs to a wave (debug spawns do not hold a wave open)
    level.actors.add_child(m)
    m.vfx_requested.connect(_play_vfx)
    m.damaged.connect(_on_monster_damaged)
    m.died.connect(_on_monster_died)
    m.reached_end.connect(_on_monster_reached_end)
    var d: Dictionary = monsters_data[id].duplicate()
    if as_boss:
        d["boss"] = true
    m.setup(id, d, level.path_curve)
    monsters.append(m)

func _on_monster_died(m) -> void:
    GameState.add_gold(int(m.data.get("reward", 0)))
    _resolve(m)

func _on_monster_reached_end(m) -> void:
    GameState.lose_lives(int(m.data.get("lives_cost", 1)))
    _resolve(m)

func _resolve(m) -> void:
    if bool(m.get_meta("counted", false)):
        wave_manager.monster_resolved()

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
