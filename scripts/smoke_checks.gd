extends RefCounted
## Data + asset + logic checks for the headless smoke test (used by smoke_test.gd, can also be run on its own).
## Unlike tools/art/validate.py this goes through Godot's importer: a PNG that exists on disk but was never
## imported (or has the wrong size) fails here. Only failures are printed; counts are in passed / failed.
## Also unit-tests the flow field (detours, siege route through towers) on tiny in-memory grids.

const Data = preload("res://scripts/data.gd")
const GridManager = preload("res://scripts/grid_manager.gd")
const FlowField = preload("res://scripts/flow_field.gd")
const WaveManager = preload("res://scripts/wave_manager.gd")

const TOWER_KEYS := ["name", "folder", "frame", "head_rotates", "event_frame", "muzzle", "projectile",
    "projectile_speed", "impact", "cost", "sell_refund", "upgrade_costs", "levels"]
const MONSTER_KEYS := ["folder", "frame", "stride", "hp", "speed", "tint", "reward", "damage", "attack_cooldown"]
const TOWER_STRIPS := {"spawn": 10, "base_idle": 0, "head_idle": 0, "head_attack": 8, "destroyed": 10, "base": 1, "head_static": 1}
const MONSTER_ANIMS := {"idle": 6, "walk": 8, "attack": 8, "hit": 4, "death": 10}
const DIRS := ["E", "S", "W", "N"]
const ENV := "res://assets/Environment/"
const GRID := "res://assets/Environment/Shared/Grid/"
const SINGLES := [
    ENV + "Grassland/grassland_tileset_32.png", ENV + "Grassland/Effects/grassland_shadow_64.png",
    ENV + "Grassland/Objects/grassland_obj_tree_64.png", ENV + "Grassland/Objects/grassland_obj_boulder_64.png",
    ENV + "Grassland/Objects/grassland_obj_bush_64.png", ENV + "Grassland/Objects/grassland_obj_fence_h_32.png",
    ENV + "Grassland/Decorations/grassland_deco_lilypad_32.png", ENV + "Grassland/Decorations/grassland_deco_arrow_right_32.png",
    ENV + "Grassland/Decorations/grassland_deco_flower_red_32.png", ENV + "Grassland/Decorations/grassland_deco_flower_yellow_32.png",
    ENV + "Grassland/Decorations/grassland_deco_flower_white_32.png", ENV + "Grassland/Decorations/grassland_deco_flower_blue_32.png",
    ENV + "Grassland/Decorations/grassland_deco_tuft_32.png", ENV + "Grassland/Decorations/grassland_deco_mushroom_32.png",
    ENV + "Grassland/Decorations/grassland_deco_rock_small_32.png", ENV + "Grassland/Decorations/grassland_deco_stump_32.png",
    GRID + "grid_line_64.png", GRID + "grid_range_ring_256.png",
    GRID + "grid_cell_available_64.png", GRID + "grid_cell_selected_64.png", GRID + "grid_cell_invalid_64.png",
    GRID + "grid_cell_occupied_64.png", GRID + "grid_footprint_selected_128.png", GRID + "grid_footprint_invalid_128.png"]

var passed := 0
var failed := 0
var towers: Dictionary = {}
var monsters: Dictionary = {}
var vfx: Dictionary = {}
var status: Dictionary = {}
var map: Dictionary = {}

func check(ok: bool, what: String) -> void:
    if ok:
        passed += 1
    else:
        failed += 1
        print("FAIL  ", what)

func run() -> void:
    towers = _load_dict("res://data/towers.json")
    monsters = _load_dict("res://data/monsters.json")
    vfx = _load_dict("res://data/vfx.json")
    status = _load_dict("res://data/status_effects.json")
    map = _load_dict("res://data/map_grassland_01.json")
    _check_towers()
    _check_monsters()
    _check_waves()
    _check_map()
    _check_player_ai()
    _check_flow_field()
    _check_assets()

func _load_dict(path: String) -> Dictionary:
    var v: Variant = Data.load_json(path)
    check(v is Dictionary, "parse " + path)
    if v is Dictionary:
        return v as Dictionary
    return {}

func _check_towers() -> void:
    for id in ["stone", "archer", "frost"]:          # main.gd builds its tower bar from these ids
        check(towers.has(id), "towers.json has '%s' (used by main.gd tower bar)" % id)
    for id in towers.keys():
        var t: Dictionary = towers[id]
        for key in TOWER_KEYS:
            check(t.has(key), "tower %s: key '%s'" % [id, key])
        var levels: Array = t.get("levels", [])
        var costs: Array = t.get("upgrade_costs", [])
        check(levels.size() == 5, "tower %s: levels[] has 5 entries" % id)
        check(costs.size() == 4, "tower %s: upgrade_costs has 4 entries" % id)
        for lv in levels:
            var ld: Dictionary = lv
            for key in ["damage", "range_cells", "cooldown"]:
                check(ld.has(key), "tower %s: a level entry lacks '%s'" % [id, key])
            for s in ld.get("statuses", []):
                var sd: Dictionary = s
                check(status.has(String(sd.get("kind", ""))), "tower %s: unknown status '%s'" % [id, sd.get("kind", "")])

func _check_monsters() -> void:
    for id in monsters.keys():
        var m: Dictionary = monsters[id]
        for key in MONSTER_KEYS:
            check(m.has(key), "monster %s: key '%s'" % [id, key])
        var tint: Array = m.get("tint", [])
        check(tint.size() == 3, "monster %s: tint needs 3 values" % id)
        check(float(m.get("damage", 0.0)) > 0.0, "monster %s: damage must be above 0" % id)
        check(float(m.get("attack_cooldown", 0.0)) > 0.0, "monster %s: attack_cooldown must be above 0" % id)

func _check_waves() -> void:
    var cfg := _load_dict("res://data/waves_grassland_01.json")
    var list: Array = cfg.get("waves", [])
    check(list.size() > 0, "waves file has waves")
    check(float(cfg.get("prepare_time", 0.0)) > 0.0, "waves: prepare_time above 0")
    check(float(cfg.get("wave_interval", 0.0)) >= 1.0, "waves: wave_interval at least 1 s")
    for w in list:
        var wd: Dictionary = w
        for g in wd.get("groups", []):
            var gd: Dictionary = g
            check(monsters.has(String(gd.get("monster", ""))), "waves: unknown monster '%s'" % gd.get("monster", ""))
    var e: Dictionary = cfg.get("endless", {})
    for id in e.get("pool", []):
        check(monsters.has(String(id)), "waves: endless pool has unknown monster '%s'" % id)
    if e.has("boss"):
        check(monsters.has(String(e["boss"])), "waves: endless boss is unknown")
    for st in cfg.get("start_towers", []):
        var sd: Dictionary = st
        check(towers.has(String(sd.get("id", ""))), "waves: unknown start tower '%s'" % sd.get("id", ""))
    # endless generation must keep producing valid waves
    var wm = WaveManager.new()
    check(wm.load_level("res://data/waves_grassland_01.json"), "wave manager loads the level")
    var far: Dictionary = wm.wave_at(list.size() + 7)
    check(not (far.get("groups", []) as Array).is_empty(), "endless wave has groups")
    check(float(far.get("hp_mult", 1.0)) > 1.0, "endless waves scale monster hp")
    for g in far.get("groups", []):
        var gd: Dictionary = g
        check(monsters.has(String(gd.get("monster", ""))), "endless wave: unknown monster '%s'" % gd.get("monster", ""))
    wm.free()

func _check_map() -> void:
    var cols := int(map.get("cols", 0))
    var rows := int(map.get("rows", 0))
    var cells: Array = map.get("cells", [])
    check(cells.size() == rows and rows > 0, "map: cells has 'rows' rows")
    for row in cells:
        var ra: Array = row
        check(ra.size() == cols, "map: a row does not have 'cols' cells")
    var prev := Vector2i(-99, -99)
    for p in map.get("enemy_path", []):
        var pa: Array = p
        var c := Vector2i(int(pa[0]), int(pa[1]))
        var inside := c.x >= 0 and c.y >= 0 and c.x < cols and c.y < rows
        check(inside, "map: enemy_path cell %s is outside the grid" % c)
        if inside and cells.size() == rows:
            check(String(cells[c.y][c.x]) == "path", "map: enemy_path cell %s is not type 'path'" % c)
        if prev.x != -99:
            check(absi(c.x - prev.x) + absi(c.y - prev.y) == 1, "map: enemy_path jumps between %s and %s" % [prev, c])
        prev = c

func _check_player_ai() -> void:
    var p := _load_dict("res://data/player.json")
    for key in ["hp", "speed", "collision_radius", "build_radius_cells", "start_cell"]:
        check(p.has(key), "player.json: key '%s'" % key)
    var sc: Array = p.get("start_cell", [0, 0])
    var cells: Array = map.get("cells", [])
    if sc.size() == 2 and cells.size() > 0:
        var x := int(sc[0])
        var y := int(sc[1])
        var ok := y >= 0 and y < cells.size() and x >= 0 and x < (cells[0] as Array).size()
        check(ok, "player.json: start_cell is inside the map")
        if ok:
            var t := String(cells[y][x])
            check(t == "buildable" or t == "path", "player.json: start_cell must be walkable, is '%s'" % t)
    var ai := _load_dict("res://data/ai.json")
    for key in ["free_cost", "tower_cost", "default_attack_range_px", "tower_attack_range_px"]:
        check(ai.has(key), "ai.json: key '%s'" % key)
    check(float(ai.get("tower_cost", 0.0)) > 100.0 * float(ai.get("free_cost", 1.0)), "ai.json: tower_cost must be much higher than free_cost")

func _grid_open(cols: int, rows: int) -> Object:
    var g = GridManager.new()
    var cells: Array = []
    for y in rows:
        var row: Array = []
        for x in cols:
            row.append("buildable")
        cells.append(row)
    g.load_from_json({"cols": cols, "rows": rows, "cells": cells})
    return g

func _check_flow_field() -> void:
    var g = _grid_open(5, 3)
    var ff = FlowField.new()
    var tgt := Vector2i(4, 1)
    ff.compute(g, tgt, 1.0, 1000.0)
    check(is_equal_approx(ff.dist_at(Vector2i(0, 1)), 4.0), "flow field: open grid distance is 4")
    check(ff.dist_at(tgt) == 0.0, "flow field: target distance is 0")
    check(ff.next_cell(Vector2i(0, 1)) == Vector2i(1, 1), "flow field: steps toward the target")
    var wall := RefCounted.new()
    g.place(Vector2i(2, 0), Vector2i(1, 1), wall)
    g.place(Vector2i(2, 1), Vector2i(1, 1), wall)
    ff.compute(g, tgt, 1.0, 1000.0)
    check(ff.dist_at(Vector2i(0, 1)) < 100.0, "flow field: a gap in the wall is used, no tower is crossed")
    check(ff.next_cell(Vector2i(1, 1)) == Vector2i(1, 2), "flow field: monsters walk around the wall through the gap")
    g.place(Vector2i(2, 2), Vector2i(1, 1), wall)
    ff.compute(g, tgt, 1.0, 1000.0)
    check(ff.dist_at(Vector2i(0, 1)) >= 1000.0, "flow field: sealed wall costs a tower crossing")
    check(g.occupancy.has(ff.next_cell(Vector2i(1, 1))), "flow field: sealed wall, next cell is a tower (siege)")
    g.remove(wall)
    ff.compute(g, tgt, 1.0, 1000.0)
    check(is_equal_approx(ff.dist_at(Vector2i(0, 1)), 4.0), "flow field: route is free again after the wall is gone")
    var w2 = _grid_open(3, 1)
    w2.types[0][1] = "water"
    ff.compute(w2, Vector2i(2, 0), 1.0, 1000.0)
    check(not ff.reachable(Vector2i(0, 0)), "flow field: water is never crossed")
    check(ff.next_cell(Vector2i(0, 0)) == Vector2i(0, 0), "flow field: no route means stay in place")

func _check_strip(path: String, fw: int, fh: int, frames: int) -> void:
    if not ResourceLoader.exists(path):
        check(false, "missing or not imported: " + path)
        return
    var tex := load(path) as Texture2D
    if tex == null:
        check(false, "cannot load " + path)
        return
    var ok := tex.get_height() == fh and fw > 0 and tex.get_width() % fw == 0
    if frames > 0:
        ok = ok and tex.get_width() == fw * frames
    check(ok, "%s is %dx%d, expected frames of %dx%d (x%d)" % [path, tex.get_width(), tex.get_height(), fw, fh, frames])

func _check_assets() -> void:
    for p in SINGLES:
        check(ResourceLoader.exists(String(p)) and load(String(p)) is Texture2D, "missing or not imported: " + String(p))
    for id in towers.keys():
        var t: Dictionary = towers[id]
        var f := int(t.get("frame", 96))
        var dir := "res://assets/Towers/%s/" % t.get("folder", "")
        _check_strip(dir + "tower_%s_shadow.png" % id, f, f, 1)
        for lv in range(1, 6):
            for suffix in TOWER_STRIPS.keys():
                _check_strip(dir + "tower_%s_level_%02d_%s.png" % [id, lv, suffix], f, f, int(TOWER_STRIPS[suffix]))
        check(ResourceLoader.exists(String(t.get("projectile", ""))), "tower %s: projectile missing" % id)
        var imp: Dictionary = t.get("impact", {})
        _check_strip(String(imp.get("path", "")), int(imp.get("frame", 0)), int(imp.get("frame", 0)), 0)
    for id in monsters.keys():
        var m: Dictionary = monsters[id]
        var f := int(m.get("frame", 64))
        var dir := "res://assets/Monsters/Grassland/%s/" % m.get("folder", "")
        _check_strip(dir + "monster_%s_shadow.png" % id, f, f, 1)
        _check_strip(dir + "Strips/monster_%s_spawn_E.png" % id, f, f, 10)
        for anim in MONSTER_ANIMS.keys():
            for d in DIRS:
                _check_strip(dir + "Strips/monster_%s_%s_%s.png" % [id, anim, d], f, f, int(MONSTER_ANIMS[anim]))
    for name in vfx.keys():
        var e: Dictionary = vfx[name]
        _check_strip(String(e.get("path", "")), int(e.get("frame_w", 0)), int(e.get("frame_h", 0)), int(e.get("frames", 0)))
