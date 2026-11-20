extends Node2D
## Playable art prototype: Grassland map + 3 towers (5 levels) + 5 monsters.
## Controls: pick a tower button -> hover map (green = valid, red = invalid) -> left click places it.
## Left click on a placed tower (when no tower is selected) upgrades it (Lv1 -> Lv5). Right click cancels.
## All gameplay numbers (damage, hp, speed, range) are PLACEHOLDERS from data/*.json.

const Data = preload("res://scripts/data.gd")
const LevelScript = preload("res://scripts/level.gd")
const TowerScript = preload("res://scripts/tower.gd")
const MonsterScript = preload("res://scripts/monster.gd")
const ProjectileScript = preload("res://scripts/projectile.gd")

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
    hint.position = Vector2(12, 740)
    hint.text = "Pick a tower, click a green cell to build. Click a tower to upgrade (Lv 1-5). Right click cancels."
    layer.add_child(hint)

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
    level.grid.place(cell, _tower_cell_size(), t)
    towers.append(t)
    t.build()

func _send_wave() -> void:
    for id in ["slime", "goblin", "boar", "mushroom", "treant"]:
        var m = MonsterScript.new()
        level.actors.add_child(m)
        m.setup(id, monsters_data[id], level.path_curve)
        monsters.append(m)
        await get_tree().create_timer(1.2).timeout

func _on_tower_fired(tower, tgt) -> void:
    if not is_instance_valid(tgt):
        return
    var td: Dictionary = tower.data
    var p = ProjectileScript.new()
    level.projectiles.add_child(p)
    p.setup(load(String(td["projectile"])) as Texture2D, tower.muzzle_position(), tgt,
        float(td["projectile_speed"]), tower.damage(), td["impact"])

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
