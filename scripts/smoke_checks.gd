extends RefCounted
## Data + asset checks for the M0 smoke test (used by smoke_test.gd, can also be run on its own).
## Unlike tools/art/validate.py this goes through Godot's importer: a PNG that exists on disk but was never
## imported (or has the wrong size) fails here. Only failures are printed; counts are in passed / failed.

const Data = preload("res://scripts/data.gd")

const TOWER_KEYS := ["name", "folder", "frame", "head_rotates", "event_frame", "muzzle", "projectile",
    "projectile_speed", "impact", "cost", "sell_refund", "upgrade_costs", "levels"]
const MONSTER_KEYS := ["folder", "frame", "stride", "hp", "speed", "tint", "reward", "lives_cost"]
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
    _check_towers()
    _check_monsters()
    _check_waves()
    _check_map()
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

func _check_waves() -> void:
    var waves := _load_dict("res://data/waves_grassland_01.json")
    var list: Array = waves.get("waves", [])
    check(list.size() > 0, "waves file has waves")
    for w in list:
        var wd: Dictionary = w
        for g in wd.get("groups", []):
            var gd: Dictionary = g
            check(monsters.has(String(gd.get("monster", ""))), "waves: unknown monster '%s'" % gd.get("monster", ""))
    for st in waves.get("start_towers", []):
        var sd: Dictionary = st
        check(towers.has(String(sd.get("id", ""))), "waves: unknown start tower '%s'" % sd.get("id", ""))

func _check_map() -> void:
    var map := _load_dict("res://data/map_grassland_01.json")
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
