extends Node2D
## Chase-and-survive tower defense prototype: Grassland map, a controllable character, timed endless waves.
## Controls: WASD or arrows move the character. Pick a tower button, hover a cell inside the yellow build ring, left click builds.
## Left click a placed tower with nothing picked opens its panel: stats, targeting, upgrade, sell with two clicks.
## Right click or Esc: cancel the picked tower, or close the panel. "Call next wave" skips the countdown.
## Monsters chase the character through a flow field. Towers block monsters, not the character. When towers leave no route,
## monsters attack the tower on their cheapest route, and it is destroyed in one hit. The run ends when the character dies.
## Debug keys: F1 freeze, F2 slow, F3 burning, F4 poison, F5 stun, F6 boss Treant, 7 Boar, 8 Mushroom, 9 hit every monster for 10.
## All gameplay numbers come from data/*.json and are PLACEHOLDERS. Run state lives in the GameState autoload, wave timing in wave_manager.gd.

const Data = preload("res://scripts/data.gd")
const LevelScript = preload("res://scripts/level.gd")
const TowerScript = preload("res://scripts/tower.gd")
const MonsterScript = preload("res://scripts/monster.gd")
const ProjectileScript = preload("res://scripts/projectile.gd")
const PlayerScript = preload("res://scripts/player.gd")
const VFX = preload("res://scripts/vfx_library.gd")
const DamageNumber = preload("res://scripts/damage_number.gd")
const WaveManager = preload("res://scripts/wave_manager.gd")
const Targeting = preload("res://scripts/targeting.gd")

const LEVEL_DATA := "res://data/waves_grassland_01.json"
const DEBUG_STATUS_KEYS := {KEY_F1: "freeze", KEY_F2: "slow", KEY_F3: "burning", KEY_F4: "poison", KEY_F5: "stun"}

var level
var player
var wave_manager
var towers_data: Dictionary
var monsters_data: Dictionary
var towers: Array = []
var monsters: Array = []
var selected_id := ""              # tower type picked from the build bar
var selected_tower = null          # placed tower whose panel is open
var _sell_armed := false           # first click on Sell arms it, second click sells
var _hud_t := 0.0
var hint: Label
var msg: Label
var status: Label
var call_btn: Button
var speed_btn: Button
var overlay: Control
var result_title: Label
var result_detail: Label
var panel: PanelContainer
var panel_title: Label
var panel_stats: Label
var panel_target_btn: Button
var panel_upgrade_btn: Button
var panel_sell_btn: Button

func _ready() -> void:
    towers_data = Data.load_json("res://data/towers.json")
    monsters_data = Data.load_json("res://data/monsters.json")
    level = LevelScript.new()
    add_child(level)
    level.build()
    player = PlayerScript.new()
    level.actors.add_child(player)
    var sc: Array = level.player_cfg.get("start_cell", [10, 5])
    player.setup(level.player_cfg, level.grid, Vector2i(int(sc[0]), int(sc[1])))
    level.refresh_flow(player.cell)
    wave_manager = WaveManager.new()
    wave_manager.name = "WaveManager"
    add_child(wave_manager)
    wave_manager.load_level(LEVEL_DATA)
    get_tree().paused = false
    GameState.reset(wave_manager.start_gold())
    _build_ui()
    player.cell_changed.connect(_on_player_cell_changed)
    player.hp_changed.connect(_on_player_hp_changed)
    player.damaged.connect(_on_player_damaged)
    player.died.connect(_on_player_died)
    wave_manager.spawn_requested.connect(_on_spawn_requested)
    wave_manager.wave_started.connect(_on_wave_started)
    wave_manager.wave_bonus.connect(_on_wave_bonus)
    GameState.gold_changed.connect(_on_gold_changed)
    GameState.wave_changed.connect(_on_wave_changed)
    GameState.speed_changed.connect(_on_speed_changed)
    GameState.game_over.connect(_on_game_over)
    for st in wave_manager.start_towers():
        var sd: Dictionary = st
        var c: Array = sd["cell"]
        _place_tower(String(sd["id"]), Vector2i(int(c[0]), int(c[1])), int(sd.get("level", 1)))
    wave_manager.start()
    _refresh_hud()

func _button(text: String) -> Button:
    var b := Button.new()
    b.text = text
    b.focus_mode = Control.FOCUS_NONE        # keeps the arrow keys free for moving the character
    return b

func _build_ui() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var bar := HBoxContainer.new()
    bar.position = Vector2(12, 8)
    layer.add_child(bar)
    for id in ["stone", "archer", "frost"]:
        var b := _button("%s  %dg" % [towers_data[id]["name"], int(towers_data[id].get("cost", 0))])
        b.pressed.connect(_select_tower.bind(id))
        bar.add_child(b)
    call_btn = _button("Call next wave")
    call_btn.pressed.connect(_on_call_wave_pressed)
    bar.add_child(call_btn)
    speed_btn = _button("Speed x1")
    speed_btn.pressed.connect(_on_speed_pressed)
    bar.add_child(speed_btn)
    var gb := _button("Toggle grid")
    gb.pressed.connect(_on_grid_pressed)
    bar.add_child(gb)
    status = Label.new()
    status.position = Vector2(12, 44)
    layer.add_child(status)
    msg = Label.new()
    msg.position = Vector2(12, 684)
    layer.add_child(msg)
    hint = Label.new()
    hint.position = Vector2(12, 716)
    hint.text = "WASD / arrows: move. Pick a tower, click a green cell inside the yellow ring to build. Click a placed tower for its panel. Right click or Esc: cancel.\nDebug: F1 freeze  F2 slow  F3 burning  F4 poison  F5 stun  F6 boss  7 boar  8 mushroom  9 hit all (10)"
    layer.add_child(hint)
    _build_panel(layer)
    _build_overlay()

func _build_panel(layer: CanvasLayer) -> void:
    panel = PanelContainer.new()
    panel.visible = false
    panel.set_anchors_preset(Control.PRESET_TOP_RIGHT)
    panel.offset_left = -272.0
    panel.offset_right = -12.0
    panel.offset_top = 52.0
    panel.offset_bottom = 52.0         # height = content (minimum size)
    layer.add_child(panel)
    var box := VBoxContainer.new()
    box.add_theme_constant_override("separation", 6)
    panel.add_child(box)
    panel_title = Label.new()
    panel_title.add_theme_font_size_override("font_size", 18)
    box.add_child(panel_title)
    panel_stats = Label.new()
    box.add_child(panel_stats)
    panel_target_btn = _button("")
    panel_target_btn.pressed.connect(_on_panel_target_pressed)
    box.add_child(panel_target_btn)
    panel_upgrade_btn = _button("")
    panel_upgrade_btn.pressed.connect(_on_panel_upgrade_pressed)
    box.add_child(panel_upgrade_btn)
    panel_sell_btn = _button("")
    panel_sell_btn.pressed.connect(_on_panel_sell_pressed)
    box.add_child(panel_sell_btn)
    var close_btn := _button("Close")
    close_btn.pressed.connect(_deselect_tower)
    box.add_child(close_btn)

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
    var rb := _button("Restart")
    rb.pressed.connect(_on_restart_pressed)
    box.add_child(rb)

# ---------------------------------------------------------------- HUD / messages
func _refresh_hud() -> void:
    var hp_text := "-"
    if player != null:
        hp_text = "%d / %d" % [int(ceil(player.hp)), int(player.max_hp)]
    var timer_text := ""
    if GameState.finished:
        timer_text = "Defeat"
    elif wave_manager.in_prep():
        timer_text = "Prepare: %d s" % int(ceil(wave_manager.time_to_next()))
    else:
        timer_text = "Next wave in %d s" % int(ceil(wave_manager.time_to_next()))
    status.text = "HP: %s    Gold: %d    Wave: %d    %s" % [hp_text, GameState.gold, GameState.wave, timer_text]
    call_btn.disabled = GameState.finished or wave_manager.time_to_next() <= 0.0

func _say(text: String) -> void:
    msg.text = text
    get_tree().create_timer(2.5).timeout.connect(_clear_msg.bind(text))

func _clear_msg(text: String) -> void:
    if is_instance_valid(msg) and msg.text == text:
        msg.text = ""

func _on_gold_changed(_gold: int) -> void:
    _refresh_hud()
    _refresh_panel()

func _on_wave_changed(_wave: int) -> void:
    _refresh_hud()

func _on_speed_changed(s: float) -> void:
    speed_btn.text = "Speed x%d" % int(s)

func _on_speed_pressed() -> void:
    GameState.cycle_speed()

func _on_grid_pressed() -> void:
    level.grid_renderer.grid_visible = not level.grid_renderer.grid_visible

func _on_call_wave_pressed() -> void:
    if not GameState.finished:
        wave_manager.call_next_wave()

func _on_restart_pressed() -> void:
    get_tree().paused = false
    get_tree().reload_current_scene()

# ---------------------------------------------------------------- player
func _on_player_cell_changed(c: Vector2i) -> void:
    level.refresh_flow(c)

func _on_player_hp_changed(_hp: float, _max_hp: float) -> void:
    _refresh_hud()

func _on_player_damaged(amount: float) -> void:
    var n = DamageNumber.new()
    level.vfx.add_child(n)
    n.position = player.global_position + Vector2(0.0, -46.0)
    n.setup(maxi(int(round(amount)), 1), "crit")

func _on_player_died() -> void:
    GameState.defeat()

# ---------------------------------------------------------------- tower panel
func _select_placed(t) -> void:
    selected_id = ""
    level.placement.clear()
    selected_tower = t
    _sell_armed = false
    _refresh_panel()

func _deselect_tower() -> void:
    selected_tower = null
    _sell_armed = false
    if panel != null:
        panel.visible = false
    level.placement.clear_selection()

func _stat_line(t, key: String, label: String, fmt: String) -> String:
    var line: String = label + ": " + (fmt % float(t.stat(key, 0.0)))
    if t.level < t.max_level():
        line += "   ->   " + (fmt % float(t.stat_at(t.level + 1, key, 0.0)))
    return line

func _status_text(t) -> String:
    var parts := PackedStringArray()
    for s in t.statuses():
        var sd: Dictionary = s
        parts.append("%s %d%% %.1fs" % [String(sd["kind"]), int(round(float(sd.get("chance", 1.0)) * 100.0)), float(sd["duration"])])
    return ", ".join(parts)

func _refresh_panel() -> void:
    if panel == null:
        return
    if not is_instance_valid(selected_tower):
        if selected_tower != null:
            _deselect_tower()
        return
    var t = selected_tower
    panel.visible = true
    level.placement.select_cell(t.cell, t.footprint, t.range_px())
    panel_title.text = "%s   Lv %d / %d" % [String(t.data["name"]), t.level, t.max_level()]
    var lines := PackedStringArray()
    lines.append(_stat_line(t, "damage", "Damage", "%.1f"))
    lines.append(_stat_line(t, "range_cells", "Range cells", "%.2f"))
    lines.append(_stat_line(t, "cooldown", "Cooldown s", "%.2f"))
    if float(t.stat("splash_radius_cells", 0.0)) > 0.0:
        lines.append(_stat_line(t, "splash_radius_cells", "Splash cells", "%.2f"))
    var effects := _status_text(t)
    if effects != "":
        lines.append("Effects: " + effects)
    lines.append("Invested: %dg" % t.invested)
    panel_stats.text = "\n".join(lines)
    panel_target_btn.text = "Target: " + String(Targeting.LABELS[t.targeting]) + "  (click to change)"
    var cost: int = t.upgrade_cost()
    if cost < 0:
        panel_upgrade_btn.text = "Max level"
        panel_upgrade_btn.disabled = true
    else:
        panel_upgrade_btn.text = "Upgrade  %dg" % cost
        panel_upgrade_btn.disabled = not (t.can_upgrade() and GameState.can_afford(cost))
    var value: int = t.sell_value()
    panel_sell_btn.text = ("Confirm sell  +%dg" if _sell_armed else "Sell  +%dg") % value
    panel_sell_btn.disabled = not t.can_sell()

func _on_panel_target_pressed() -> void:
    if is_instance_valid(selected_tower):
        selected_tower.cycle_targeting()
        _refresh_panel()

func _on_panel_upgrade_pressed() -> void:
    _sell_armed = false
    if is_instance_valid(selected_tower):
        _try_upgrade(selected_tower)
    _refresh_panel()

func _on_panel_sell_pressed() -> void:
    if not is_instance_valid(selected_tower):
        return
    if not _sell_armed:
        _sell_armed = true
        _refresh_panel()
        return
    _try_sell(selected_tower)

func _on_tower_state_changed(t) -> void:
    if t == selected_tower:
        _refresh_panel()

func _cancel_selection() -> void:
    if selected_id != "":
        selected_id = ""
        level.placement.clear()
    elif selected_tower != null:
        _deselect_tower()

# ---------------------------------------------------------------- waves / defeat
func _on_wave_started(index: int) -> void:
    GameState.set_wave(index)
    _play_vfx("wave_transition", level.grid.cell_center(level.entry_cell), 1.0)
    _say("Wave %d" % index)

func _on_wave_bonus(index: int, gold: int) -> void:
    if GameState.finished or gold <= 0:
        return
    GameState.add_gold(gold)
    _say("Wave %d survived! +%d gold" % [index, gold])

func _on_game_over(wave_reached: int) -> void:
    wave_manager.stop()
    result_title.text = "DEFEAT"
    result_detail.text = "Waves reached: %d    Gold: %d" % [wave_reached, GameState.gold]
    overlay.visible = true
    get_tree().paused = true
    _refresh_hud()

func _on_spawn_requested(monster_id: String, hp_mult: float, boss: bool) -> void:
    _spawn_monster(monster_id, boss, hp_mult)

# ---------------------------------------------------------------- VFX entry point (towers and monsters emit vfx_requested)
func _play_vfx(vfx_name: String, pos: Vector2, scale_f: float = 1.0, tint: Color = Color.WHITE) -> void:
    VFX.play_once(level.vfx, vfx_name, pos, scale_f, tint)

# ---------------------------------------------------------------- placement
func _select_tower(id: String) -> void:
    _deselect_tower()
    selected_id = "" if selected_id == id else id
    _update_preview()

func _footprint(id: String) -> Vector2i:
    return TowerScript.footprint_of(towers_data[id])

func _level1_range_cells(td: Dictionary) -> float:
    var levels: Array = td.get("levels", [])
    if not levels.is_empty():
        var first: Dictionary = levels[0]
        return float(first.get("range_cells", td.get("range_cells", 3.0)))
    return float(td.get("range_cells", 3.0))

func _build_radius_px() -> float:
    return float(player.build_radius_cells) * 64.0

## Empty string = a tower of this footprint may be built at `cell`, otherwise the reason.
func _build_block_reason(cell: Vector2i, fp: Vector2i) -> String:
    if not level.grid.can_place(cell, fp):
        return "Cannot build here"
    for y in fp.y:
        for x in fp.x:
            if cell + Vector2i(x, y) == player.cell:
                return "Cannot build under the character"
    if level.grid.footprint_center(cell, fp).distance_to(player.global_position) > _build_radius_px():
        return "Too far from the character"
    return ""

func _can_build_here(cell: Vector2i, fp: Vector2i) -> bool:
    return _build_block_reason(cell, fp) == ""

func _update_preview() -> void:
    var pl = level.placement
    if selected_id == "":
        pl.clear()
        return
    var td: Dictionary = towers_data[selected_id]
    var fp := _footprint(selected_id)
    var cell: Vector2i = level.grid.world_to_cell(get_global_mouse_position())
    pl.available = level.available_cells(player.global_position, _build_radius_px(), player.cell)
    pl.occupied = level.grid.occupancy.keys()
    pl.preview_active = level.grid.in_bounds(cell)
    pl.preview_cell = cell
    pl.preview_size = fp
    pl.preview_valid = _can_build_here(cell, fp) and GameState.can_afford(int(td.get("cost", 0)))
    pl.range_px = _level1_range_cells(td) * 64.0
    pl.set_build_ring(player.global_position, _build_radius_px())
    var base_tex := load("res://assets/Towers/%s/tower_%s_level_01_base.png" % [td["folder"], selected_id]) as Texture2D
    var head_tex := load("res://assets/Towers/%s/tower_%s_level_01_head_static.png" % [td["folder"], selected_id]) as Texture2D
    pl.ghost_textures = [base_tex, head_tex]
    pl.queue_redraw()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton:
        var mb := event as InputEventMouseButton
        if not mb.pressed:
            return
        if mb.button_index == MOUSE_BUTTON_LEFT:
            _on_left_click()
        elif mb.button_index == MOUSE_BUTTON_RIGHT:
            _cancel_selection()

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
    elif k.keycode == KEY_7:
        _spawn_monster("boar")
    elif k.keycode == KEY_8:
        _spawn_monster("mushroom")
    elif k.keycode == KEY_9:
        for m in monsters:
            if is_instance_valid(m) and m.is_alive():
                m.take_damage(10.0, false)
    elif k.keycode == KEY_ESCAPE:
        _cancel_selection()

func _on_left_click() -> void:
    var cell: Vector2i = level.grid.world_to_cell(get_global_mouse_position())
    if selected_id != "":
        var fp := _footprint(selected_id)
        var reason := _build_block_reason(cell, fp)
        if reason != "":
            _say(reason)
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
            _select_placed(t)
        else:
            _deselect_tower()

func _try_upgrade(t) -> void:
    var cost: int = t.upgrade_cost()
    if cost < 0:
        _say("Already max level")
        return
    if not t.can_upgrade():
        _say("Tower is busy")
        return
    if not GameState.spend(cost):
        _say("Not enough gold (need %d)" % cost)
        return
    t.upgrade()

func _try_sell(t) -> void:
    _sell_armed = false
    if not t.can_sell():
        _say("Tower is busy")
        _refresh_panel()
        return
    var value: int = t.sell_value()
    GameState.add_gold(value)
    level.grid.remove(t)
    towers.erase(t)
    level.refresh_flow(player.cell)
    _play_vfx("sell_effect", t.global_position, 1.0)
    if t == selected_tower:
        _deselect_tower()
    t.queue_free()
    _say("Sold for %d gold" % value)

## A monster destroyed this tower (one hit, no refund). The grid cell is freed at once and the flow field recomputed.
func _destroy_tower(t) -> void:
    if not is_instance_valid(t) or not towers.has(t):
        return
    level.grid.remove(t)
    towers.erase(t)
    if t == selected_tower:
        _deselect_tower()
    t.destroy()
    level.refresh_flow(player.cell)
    _say("A tower was destroyed!")

func _on_tower_destroyed_done(t) -> void:
    if is_instance_valid(t):
        t.queue_free()

func _place_tower(id: String, cell: Vector2i, start_level: int) -> void:
    var fp := _footprint(id)
    var t = TowerScript.new()
    level.actors.add_child(t)
    t.setup(id, towers_data[id], start_level)
    t.cell = cell
    t.position = level.grid.footprint_center(cell, fp)
    t.fired.connect(_on_tower_fired)
    t.vfx_requested.connect(_play_vfx)
    t.state_changed.connect(_on_tower_state_changed)
    t.destroyed_done.connect(_on_tower_destroyed_done)
    level.grid.place(cell, fp, t)
    towers.append(t)
    level.refresh_flow(player.cell)
    t.build()

# ---------------------------------------------------------------- monsters
func _spawn_monster(id: String, as_boss := false, hp_mult := 1.0) -> void:
    var m = MonsterScript.new()
    level.actors.add_child(m)
    m.add_to_group("monsters")              # splash damage and spore healing look monsters up through this group
    m.vfx_requested.connect(_play_vfx)
    m.damaged.connect(_on_monster_damaged)
    m.healed.connect(_on_monster_healed)
    m.died.connect(_on_monster_died)
    m.attacked_player.connect(_on_monster_attacked_player)
    m.attacked_tower.connect(_on_monster_attacked_tower)
    var d: Dictionary = monsters_data[id].duplicate()
    d["hp"] = float(d["hp"]) * hp_mult
    if as_boss:
        d["boss"] = true
    m.setup(id, d, level, player)
    monsters.append(m)

func _on_monster_died(m) -> void:
    GameState.add_gold(int(m.data.get("reward", 0)))

func _on_monster_attacked_player(_m, amount: float) -> void:
    if is_instance_valid(player):
        player.take_damage(amount)

func _on_monster_attacked_tower(_m, tower) -> void:
    _destroy_tower(tower)

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

func _on_monster_healed(m, amount: float) -> void:
    if not is_instance_valid(m):
        return
    var top: float = float(m.data["frame"]) * 0.4
    var n = DamageNumber.new()
    level.vfx.add_child(n)
    n.position = m.global_position + Vector2(0.0, -top)
    n.setup(maxi(int(round(amount)), 1), "heal")

func _on_tower_fired(tower, tgt) -> void:
    if not is_instance_valid(tgt):
        return
    var crit: bool = randf() < float(tower.crit_chance())
    var dmg: float = float(tower.damage()) * (float(tower.crit_mult()) if crit else 1.0)
    var splash := {}
    var radius: float = float(tower.splash_radius_px())
    if radius > 0.0:
        splash = {"radius_px": radius, "mult": float(tower.splash_mult()), "statuses": bool(tower.splash_statuses())}
    var p = ProjectileScript.new()
    level.projectiles.add_child(p)
    p.setup(load(String(tower.data["projectile"])) as Texture2D, tower.muzzle_position(), tgt,
        float(tower.data["projectile_speed"]), dmg, tower.data["impact"], crit, tower.statuses(), splash)

func _process(delta: float) -> void:
    monsters = monsters.filter(func(m): return is_instance_valid(m))
    for t in towers:
        if not is_instance_valid(t) or not t.built:
            continue
        var best = Targeting.pick(t.targeting, t.global_position, t.range_px(), monsters)
        t.target = best
        if best != null:
            t.try_fire(best)
    if selected_id != "":
        _update_preview()                    # the build ring follows the character
    _hud_t += delta
    if _hud_t >= 0.2:
        _hud_t = 0.0
        _refresh_hud()
