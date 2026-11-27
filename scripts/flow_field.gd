extends RefCounted
## Flow field on the logical grid, centred on the character cell. Pure logic, no nodes.
## dist[cell] = cost for a monster to get from that cell to the target, INCLUDING the cost of the cell itself (target = 0).
## Cell cost: free cell = free_cost, tower cell = tower_cost (very high, so towers are only crossed when no free route exists).
## Water and blocked cells are never entered. The target cell is always free, even when a tower stands on it.
## Monsters call next_cell every frame; it returns the neighbour with the lowest dist, or the same cell when there is no route.
## Because dist includes the cell cost, a neighbour that holds a tower looks expensive and is only chosen when no free route exists.

const NO_ROUTE := 1.0e9
const DIRS := [Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(0, -1)]

var cols := 0
var rows := 0
var target := Vector2i(-1, -1)
var dist := PackedFloat32Array()

func _i(c: Vector2i) -> int:
    return c.y * cols + c.x

func compute(grid, tgt: Vector2i, free_cost: float, tower_cost: float) -> void:
    cols = int(grid.cols)
    rows = int(grid.rows)
    target = tgt
    dist.resize(cols * rows)
    dist.fill(NO_ROUTE)
    if not grid.in_bounds(tgt):
        return
    var done := PackedByteArray()
    done.resize(cols * rows)
    dist[_i(tgt)] = 0.0
    var open: Array = [tgt]
    while not open.is_empty():
        var bi := 0
        var bd: float = dist[_i(open[0])]
        for k in range(1, open.size()):
            var dk: float = dist[_i(open[k])]
            if dk < bd:
                bd = dk
                bi = k
        var cur: Vector2i = open[bi]
        open.remove_at(bi)
        var ci := _i(cur)
        if done[ci] == 1:
            continue
        done[ci] = 1
        for d in DIRS:
            var n: Vector2i = cur + d
            if not grid.in_bounds(n) or not grid.walkable(n):
                continue
            var ni := _i(n)
            if done[ni] == 1:
                continue
            var cell_cost := free_cost
            if grid.occupancy.has(n):
                cell_cost = tower_cost
            var nd: float = dist[ci] + cell_cost
            if nd < dist[ni]:
                dist[ni] = nd
                open.append(n)

func dist_at(c: Vector2i) -> float:
    if c.x < 0 or c.y < 0 or c.x >= cols or c.y >= rows:
        return NO_ROUTE
    return dist[_i(c)]

func reachable(c: Vector2i) -> bool:
    return dist_at(c) < NO_ROUTE * 0.5

func next_cell(c: Vector2i) -> Vector2i:
    var best := c
    var bd := dist_at(c)
    for d in DIRS:
        var n: Vector2i = c + d
        var dn := dist_at(n)
        if dn < bd:
            bd = dn
            best = n
    return best
