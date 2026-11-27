extends Node
## Data-driven timed wave spawner (data/waves_*.json). It owns NO scene knowledge: it emits spawn_requested
## and main.gd spawns the monster. Waves do NOT wait for the previous wave to be cleared.
## Timeline: prepare_time seconds of build time, then wave 1; every wave_interval seconds the next wave starts.
## After the listed waves the "endless" block generates waves forever (more monsters, shorter intervals, more hp, a boss every few waves).
## Uses _process(delta), so it follows Engine.time_scale (speed x1-3) and get_tree().paused.
##
## Wave format: {"bonus": gold, "groups": [{"monster": id, "count": n, "interval": s, "delay": s, "boss": bool}, ...]}
## Group spawn times are wave_start + delay + i * interval. The bonus of a wave is paid when the NEXT wave starts.

const Data = preload("res://scripts/data.gd")

signal spawn_requested(monster_id: String, hp_mult: float, boss: bool)
signal wave_started(index: int)                 # 1-based
signal wave_bonus(index: int, gold: int)        # wave `index` was survived until the next one started

var cfg: Dictionary = {}
var waves: Array = []
var endless: Dictionary = {}
var prepare_time := 30.0
var wave_interval := 25.0
var hp_scale := 0.0
var next_index := 0          # 0-based index of the next wave to start
var running := false
var clock := 0.0
var _next_start := 0.0
var _events: Array = []      # [{"t": float, "id": String, "hp": float, "boss": bool}] sorted by t

func load_level(path: String) -> bool:
    var d = Data.load_json(path)
    if not (d is Dictionary):
        push_error("WaveManager: cannot load " + path)
        return false
    cfg = d
    var w: Array = cfg.get("waves", [])
    waves = w
    var e: Variant = cfg.get("endless", {})
    if e is Dictionary:
        endless = e
    prepare_time = maxf(float(cfg.get("prepare_time", 30.0)), 0.0)
    wave_interval = maxf(float(cfg.get("wave_interval", 25.0)), 1.0)
    hp_scale = float(cfg.get("hp_scale_per_wave", 0.0))
    next_index = 0
    running = false
    if waves.is_empty():
        push_error("WaveManager: no waves in " + path)
        return false
    return true

func start_gold() -> int:
    return int(cfg.get("start_gold", 100))

func start_towers() -> Array:
    var a: Array = cfg.get("start_towers", [])
    return a

func total() -> int:
    return waves.size()

func start() -> void:
    clock = 0.0
    _next_start = prepare_time
    _events.clear()
    next_index = 0
    running = true

func stop() -> void:
    running = false

func in_prep() -> bool:
    return running and next_index == 0

func time_to_next() -> float:
    return maxf(_next_start - clock, 0.0)

func call_next_wave() -> bool:
    if not running or _next_start <= clock:
        return false
    _next_start = clock
    return true

func wave_at(i: int) -> Dictionary:
    if i < waves.size():
        var w: Dictionary = waves[i]
        return w
    return _endless_wave(i - waves.size())

func _endless_wave(k: int) -> Dictionary:
    var pool: Array = endless.get("pool", [])
    var groups: Array = []
    var base := float(endless.get("base_count", 6)) + float(endless.get("count_growth", 1.0)) * float(k)
    var per := maxi(int(round(base / 2.0)), 1)
    var interval := maxf(float(endless.get("interval", 1.0)) - float(endless.get("interval_shrink", 0.0)) * float(k), float(endless.get("min_interval", 0.4)))
    var gap := float(endless.get("group_gap", 6.0))
    for j in pool.size():
        groups.append({"monster": String(pool[j]), "count": per, "interval": interval, "delay": gap * float(j)})
    var boss_every := int(endless.get("boss_every", 0))
    var boss := String(endless.get("boss", ""))
    if boss != "" and boss_every > 0 and (k + 1) % boss_every == 0:
        groups.append({"monster": boss, "count": 1 + floori(float(k + 1) / float(boss_every)), "interval": 5.0, "delay": gap * 0.5, "boss": true})
    return {"bonus": int(endless.get("bonus", 0)), "groups": groups, "hp_mult": 1.0 + hp_scale * float(k + 1)}

func _begin_wave(i: int) -> void:
    var w := wave_at(i)
    var start := _next_start
    var hp_mult := float(w.get("hp_mult", 1.0))
    for g in w.get("groups", []):
        var gd: Dictionary = g
        var delay := float(gd.get("delay", 0.0))
        var interval := float(gd.get("interval", 1.0))
        var is_boss := bool(gd.get("boss", false))
        for n in int(gd.get("count", 1)):
            _events.append({"t": start + delay + float(n) * interval, "id": String(gd["monster"]), "hp": hp_mult, "boss": is_boss})
    _events.sort_custom(func(a, b): return float(a["t"]) < float(b["t"]))
    next_index = i + 1
    _next_start = start + wave_interval
    wave_started.emit(next_index)
    if i > 0:
        var prev := wave_at(i - 1)
        wave_bonus.emit(i, int(prev.get("bonus", 0)))

func _process(delta: float) -> void:
    if not running:
        return
    clock += delta
    while clock >= _next_start:
        _begin_wave(next_index)
    while not _events.is_empty() and float(_events[0]["t"]) <= clock:
        var ev: Dictionary = _events.pop_front()
        spawn_requested.emit(String(ev["id"]), float(ev["hp"]), bool(ev["boss"]))
