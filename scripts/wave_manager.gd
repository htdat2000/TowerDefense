extends Node
## Data-driven wave spawner (data/waves_*.json). It owns NO scene knowledge: it emits spawn_requested(monster_id)
## and main.gd spawns the monster. main.gd calls monster_resolved() when a wave monster died or reached the end.
## A wave is cleared when every spawn event fired and no wave monster is alive. Uses _process(delta), so it follows
## Engine.time_scale (speed x1-3) and get_tree().paused.
##
## Wave format: {"bonus": gold, "groups": [{"monster": id, "count": n, "interval": s, "delay": s}, ...]}
## Group spawn times are delay + i * interval, counted from the start of the wave (groups overlap freely).

const Data = preload("res://scripts/data.gd")

signal spawn_requested(monster_id: String)
signal wave_started(index: int, total: int)      # index is 1-based
signal wave_cleared(index: int, bonus: int)      # index is 1-based
signal all_waves_cleared

var cfg: Dictionary = {}
var waves: Array = []
var next_index := 0          # 0-based index of the next wave to start
var running := false
var _clock := 0.0
var _queue: Array = []       # [{"t": float, "id": String}] sorted by t
var _qpos := 0
var _alive := 0

func load_level(path: String) -> bool:
    var d = Data.load_json(path)
    if not (d is Dictionary):
        push_error("WaveManager: cannot load " + path)
        return false
    cfg = d
    var w: Array = cfg.get("waves", [])
    waves = w
    next_index = 0
    running = false
    if waves.is_empty():
        push_error("WaveManager: no waves in " + path)
        return false
    return true

func start_gold() -> int:
    return int(cfg.get("start_gold", 100))

func start_lives() -> int:
    return int(cfg.get("start_lives", 10))

func start_towers() -> Array:
    var a: Array = cfg.get("start_towers", [])
    return a

func total() -> int:
    return waves.size()

func can_start() -> bool:
    return not running and next_index < waves.size()

func start_next() -> bool:
    if not can_start():
        return false
    var w: Dictionary = waves[next_index]
    _queue.clear()
    for g in w.get("groups", []):
        var gd: Dictionary = g
        var delay := float(gd.get("delay", 0.0))
        var interval := float(gd.get("interval", 1.0))
        for i in int(gd.get("count", 1)):
            _queue.append({"t": delay + i * interval, "id": String(gd["monster"])})
    _queue.sort_custom(func(a, b): return float(a["t"]) < float(b["t"]))
    _qpos = 0
    _clock = 0.0
    _alive = 0
    running = true
    next_index += 1
    wave_started.emit(next_index, waves.size())
    return true

func stop() -> void:
    running = false

func monster_resolved() -> void:
    _alive = maxi(_alive - 1, 0)
    _check_done()

func _process(delta: float) -> void:
    if not running:
        return
    _clock += delta
    while _qpos < _queue.size() and float(_queue[_qpos]["t"]) <= _clock:
        var ev: Dictionary = _queue[_qpos]
        _qpos += 1
        _alive += 1
        spawn_requested.emit(String(ev["id"]))
    _check_done()

func _check_done() -> void:
    if not running or _qpos < _queue.size() or _alive > 0:
        return
    running = false
    var finished_wave: Dictionary = waves[next_index - 1]
    wave_cleared.emit(next_index, int(finished_wave.get("bonus", 0)))
    if next_index >= waves.size():
        all_waves_cleared.emit()
