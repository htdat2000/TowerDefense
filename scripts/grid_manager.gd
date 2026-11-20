extends RefCounted
## GRID LOGIC ONLY (no rendering). Stays valid when the grid is hidden.
## Logical cell = 64 px (2x2 art tiles of 32 px). Cell types come from map_*.json.

const CELL := 64
var cols := 0
var rows := 0
var types: Array = []            # types[y][x] = "path" | "water" | "blocked" | "buildable"
var occupancy: Dictionary = {}   # Vector2i -> tower node

func load_from_json(d: Dictionary) -> void:
    cols = int(d["cols"])
    rows = int(d["rows"])
    types = d["cells"]
    occupancy.clear()

func in_bounds(c: Vector2i) -> bool:
    return c.x >= 0 and c.y >= 0 and c.x < cols and c.y < rows

func type_at(c: Vector2i) -> String:
    if not in_bounds(c):
        return "blocked"
    return String(types[c.y][c.x])

func world_to_cell(p: Vector2) -> Vector2i:
    return Vector2i(floori(p.x / CELL), floori(p.y / CELL))

func cell_center(c: Vector2i) -> Vector2:
    return (Vector2(c) + Vector2(0.5, 0.5)) * CELL

func footprint_center(c: Vector2i, size: Vector2i) -> Vector2:
    return (Vector2(c) + Vector2(size) * 0.5) * CELL

func is_buildable(c: Vector2i) -> bool:
    return type_at(c) == "buildable" and not occupancy.has(c)

func can_place(c: Vector2i, size: Vector2i) -> bool:
    for y in size.y:
        for x in size.x:
            if not is_buildable(c + Vector2i(x, y)):
                return false
    return true

func place(c: Vector2i, size: Vector2i, obj: Object) -> void:
    for y in size.y:
        for x in size.x:
            occupancy[c + Vector2i(x, y)] = obj

func remove(obj: Object) -> void:
    for k in occupancy.keys():
        if occupancy[k] == obj:
            occupancy.erase(k)
