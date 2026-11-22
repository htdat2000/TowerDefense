extends RefCounted
## Tower target selection. Static helper, no instance needed:
##   const Targeting = preload("res://scripts/targeting.gd")
##   var m = Targeting.pick("first", tower_pos, range_px, monsters)
## Modes: first = furthest along the path, last = least far along the path,
## strongest = highest current hp, closest = nearest to the tower.
## Monsters need: is_alive(), global_position, dist (path distance), hp.

const MODES := ["first", "last", "strongest", "closest"]
const LABELS := {"first": "First", "last": "Last", "strongest": "Strongest", "closest": "Closest"}

static func is_valid_mode(mode: String) -> bool:
    return MODES.has(mode)

static func next_mode(mode: String) -> String:
    var i: int = MODES.find(mode)
    return String(MODES[(i + 1) % MODES.size()])

static func pick(mode: String, from: Vector2, range_px: float, monsters: Array) -> Node2D:
    var best: Node2D = null
    var best_score := -INF
    for m in monsters:
        if not is_instance_valid(m) or not m.is_alive():
            continue
        var d: float = from.distance_to(m.global_position)
        if d > range_px:
            continue
        var score: float = _score(mode, m, d)
        if score > best_score:
            best_score = score
            best = m
    return best

static func _score(mode: String, m, d: float) -> float:
    match mode:
        "last":
            return -float(m.dist)
        "strongest":
            return float(m.hp)
        "closest":
            return -d
        _:
            return float(m.dist)
