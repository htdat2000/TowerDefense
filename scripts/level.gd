extends Node2D
## Builds the Grassland level from data files using SEPARATE layers (bottom -> top):
## Ground, Water, Path (TileMapLayer, 47-tile blob autotiling) | Shadows, Decals, SmallDecor, Objects |
## Grid (render only) | Placement overlay | Actors (towers, monsters, player, y-sorted) | Projectiles | Vfx.
## Grid LOGIC lives in grid_manager.gd and does not depend on any of these nodes.
## Chase rules: the flow field (flow_field.gd) is owned here, main.gd calls refresh_flow(cell) when the character changes cell
## or a tower is placed, sold or destroyed. The old enemy_path of the map is only used for the monster entry (spawn point) and the decals.

const Data = preload("res://scripts/data.gd")
const GridManager = preload("res://scripts/grid_manager.gd")
const GridRenderer = preload("res://scripts/grid_renderer.gd")
const PlacementLayer = preload("res://scripts/placement_layer.gd")
const FlowField = preload("res://scripts/flow_field.gd")

const ENV := "res://assets/Environment/Grassland/"
const NEIGHBORS := [[1, 0, -1], [2, 1, 0], [4, 0, 1], [8, -1, 0], [16, 1, -1], [32, 1, 1], [64, -1, 1], [128, -1, -1]]

var grid := GridManager.new()
var flow := FlowField.new()
var ai: Dictionary = {}              # data/ai.json
var player_cfg: Dictionary = {}      # data/player.json
var spawn_point := Vector2.ZERO      # world position where monsters appear (one cell outside the map)
var entry_cell := Vector2i.ZERO      # first map cell monsters walk into
var ground: TileMapLayer
var water: TileMapLayer
var path_layer: TileMapLayer
var shadows: Node2D
var decals: Node2D
var small_decor: Node2D
var objects: Node2D
var grid_renderer   # GridRenderer script instance (dynamic on purpose)
var placement       # PlacementLayer script instance
var actors: Node2D
var projectiles: Node2D
var vfx: Node2D
var _map: Dictionary
var _meta: Dictionary
var _tex_cache := {}

func build() -> void:
    _map = Data.load_json("res://data/map_grassland_01.json")
    _meta = Data.load_json("res://data/grassland_tileset_32.json")
    var decor: Dictionary = Data.load_json("res://data/map_decor.json")
    ai = Data.load_json("res://data/ai.json")
    player_cfg = Data.load_json("res://data/player.json")
    grid.load_from_json(_map)
    if bool(player_cfg.get("build_on_path", false)):
        grid.build_types = ["buildable", "path"]

    var tile_set := _make_tileset(load(ENV + "grassland_tileset_32.png") as Texture2D)
    ground = _make_layer("Ground", tile_set, 0)
    water = _make_layer("Water", tile_set, 1)
    path_layer = _make_layer("Path", tile_set, 2)
    shadows = _make_node("Shadows", 3)
    decals = _make_node("Decals", 3)
    small_decor = _make_node("SmallDecor", 4)
    objects = _make_node("Objects", 5)
    objects.y_sort_enabled = true

    _paint_ground()
    _paint_blob(water, "water", 7, _meta["water_index_by_mask"])
    _paint_blob(path_layer, "path", 1, _meta["path_index_by_mask"])
    _place_objects(decor)
    _scatter_small()
    _place_arrows()
    _build_spawn()

    grid_renderer = GridRenderer.new()
    grid_renderer.name = "Grid"
    grid_renderer.z_index = 10
    add_child(grid_renderer)
    grid_renderer.setup(grid.cols, grid.rows)

    placement = PlacementLayer.new()
    placement.name = "Placement"
    placement.z_index = 11
    add_child(placement)

    actors = _make_node("Actors", 20)
    actors.y_sort_enabled = true
    projectiles = _make_node("Projectiles", 25)
    vfx = _make_node("Vfx", 30)

## Recompute the monster flow field towards the character cell (cheap: the grid has a few hundred cells).
func refresh_flow(target_cell: Vector2i) -> void:
    flow.compute(grid, target_cell, float(ai.get("free_cost", 1.0)), float(ai.get("tower_cost", 1000.0)))

# ------------------------------------------------------------------ helpers
func _make_node(n: String, z: int) -> Node2D:
    var node := Node2D.new()
    node.name = n
    node.z_index = z
    add_child(node)
    return node

func _make_layer(n: String, ts: TileSet, z: int) -> TileMapLayer:
    var l := TileMapLayer.new()
    l.name = n
    l.tile_set = ts
    l.z_index = z
    l.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST   # avoids seams between 32 px tiles
    add_child(l)
    return l

func _make_tileset(tex: Texture2D) -> TileSet:
    var ts := TileSet.new()
    ts.tile_size = Vector2i(32, 32)
    var src := TileSetAtlasSource.new()
    src.texture = tex
    src.texture_region_size = Vector2i(32, 32)
    for y in int(tex.get_height() / 32.0):
        for x in int(tex.get_width() / 32.0):
            src.create_tile(Vector2i(x, y))
    ts.add_source(src, 0)
    return ts

func _tex(rel: String) -> Texture2D:
    if not _tex_cache.has(rel):
        _tex_cache[rel] = load(ENV + rel)
    return _tex_cache[rel]

# ------------------------------------------------------------------ painting
func _paint_ground() -> void:
    var rng := RandomNumberGenerator.new()
    rng.seed = 42
    var pool := [0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3]
    for y in grid.rows * 2:
        for x in grid.cols * 2:
            ground.set_cell(Vector2i(x, y), 0, Vector2i(int(pool[rng.randi() % pool.size()]), 0))

func _canon(m: int) -> int:
    if not ((m & 1) != 0 and (m & 2) != 0): m &= ~16
    if not ((m & 4) != 0 and (m & 2) != 0): m &= ~32
    if not ((m & 4) != 0 and (m & 8) != 0): m &= ~64
    if not ((m & 1) != 0 and (m & 8) != 0): m &= ~128
    return m

func _paint_blob(layer: TileMapLayer, kind: String, first_row: int, index_map: Dictionary) -> void:
    var tw := grid.cols * 2
    var th := grid.rows * 2
    var members := {}
    for cy in grid.rows:
        for cx in grid.cols:
            if grid.type_at(Vector2i(cx, cy)) == kind:
                for a in 2:
                    for b in 2:
                        members[Vector2i(cx * 2 + a, cy * 2 + b)] = true
    for key in members.keys():
        var t: Vector2i = key
        var m := 0
        for nb in NEIGHBORS:
            var nx: int = t.x + int(nb[1])
            var ny: int = t.y + int(nb[2])
            var has := true   # outside the map counts as connected
            if nx >= 0 and ny >= 0 and nx < tw and ny < th:
                has = members.has(Vector2i(nx, ny))
            if has:
                m |= int(nb[0])
        var k := int(index_map[str(_canon(m))])
        layer.set_cell(t, 0, Vector2i(k % 8, first_row + floori(k / 8.0)))

func _add_sprite(parent: Node2D, tex: Texture2D, pos: Vector2, centered := false) -> Sprite2D:
    var s := Sprite2D.new()
    s.texture = tex
    s.centered = centered
    s.position = pos
    parent.add_child(s)
    return s

func _place_objects(decor: Dictionary) -> void:
    var sh64 := _tex("Effects/grassland_shadow_64.png")
    var big := {
        "trees": _tex("Objects/grassland_obj_tree_64.png"),
        "boulders": _tex("Objects/grassland_obj_boulder_64.png"),
        "bushes": _tex("Objects/grassland_obj_bush_64.png")}
    for k in big.keys():
        for c in decor[k]:
            var p := Vector2(int(c[0]), int(c[1])) * 64.0
            _add_sprite(shadows, sh64, p + Vector2(2, 4))
            _add_sprite(objects, big[k], p)
    var fence := _tex("Objects/grassland_obj_fence_h_32.png")
    for c in decor["fences"]:
        var p := Vector2(int(c[0]), int(c[1])) * 64.0 + Vector2(0, 16)
        _add_sprite(objects, fence, p)
        _add_sprite(objects, fence, p + Vector2(32, 0))
    var lily := _tex("Decorations/grassland_deco_lilypad_32.png")
    for p in decor["lilypads"]:
        _add_sprite(small_decor, lily, Vector2(float(p[0]), float(p[1])))

func _near(c: Vector2i, kinds: Array) -> bool:
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if grid.type_at(c + Vector2i(dx, dy)) in kinds:
                return true
    return false

func _scatter_small() -> void:
    var rng := RandomNumberGenerator.new()
    rng.seed = 42
    var keys := ["flower_red", "flower_yellow", "flower_white", "flower_blue", "tuft", "tuft", "mushroom", "rock_small", "stump"]
    var used := {}
    for i in 110:
        var tx := rng.randi_range(0, grid.cols * 2 - 1)
        var ty := rng.randi_range(0, grid.rows * 2 - 1)
        var c := Vector2i(floori(tx / 2.0), floori(ty / 2.0))
        var k: String = keys[rng.randi() % keys.size()]
        if used.has(Vector2i(tx, ty)) or grid.type_at(c) != "buildable":
            continue
        if k in ["mushroom", "rock_small", "stump"] and _near(c, ["path", "water"]):
            continue
        used[Vector2i(tx, ty)] = true
        _add_sprite(small_decor, _tex("Decorations/grassland_deco_%s_32.png" % k), Vector2(tx * 32, ty * 32))

func _place_arrows() -> void:
    var arrow := _tex("Decorations/grassland_deco_arrow_right_32.png")
    var pts: Array = _map["enemy_path"]
    for i in range(1, pts.size() - 1):
        if i % 2 != 0:
            continue
        var a := Vector2(float(pts[i][0]), float(pts[i][1]))
        var b := Vector2(float(pts[i + 1][0]), float(pts[i + 1][1]))
        var s := _add_sprite(decals, arrow, grid.cell_center(Vector2i(a)), true)
        s.rotation = (b - a).angle()

## Monsters appear one cell outside the map, in line with the first two enemy_path cells, and walk in.
func _build_spawn() -> void:
    var pts: Array = _map["enemy_path"]
    var c0 := Vector2i(int(pts[0][0]), int(pts[0][1]))
    var c1 := Vector2i(int(pts[1][0]), int(pts[1][1]))
    entry_cell = c0
    spawn_point = grid.cell_center(c0) - Vector2(c1 - c0) * 64.0

## Buildable, free cells whose centre is within radius_px of `center` (the character), except the `exclude` cell.
func available_cells(center: Vector2, radius_px: float, exclude: Vector2i) -> Array:
    var out: Array = []
    var r := int(ceil(radius_px / 64.0)) + 1
    var cc: Vector2i = grid.world_to_cell(center)
    for y in range(maxi(cc.y - r, 0), mini(cc.y + r, grid.rows - 1) + 1):
        for x in range(maxi(cc.x - r, 0), mini(cc.x + r, grid.cols - 1) + 1):
            var c := Vector2i(x, y)
            if c == exclude or not grid.is_buildable(c):
                continue
            if grid.cell_center(c).distance_to(center) <= radius_px:
                out.append(c)
    return out
