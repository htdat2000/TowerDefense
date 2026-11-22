extends Node
## Autoload "GameState": run-wide state (gold, lives, wave, speed) and its signals.
## No gameplay numbers live here: starting values are passed to reset() from the level data (data/waves_*.json).
## Signals go up; UI and main.gd listen. Never connect lambdas to this autoload (they outlive scene reloads).

signal gold_changed(gold: int)
signal lives_changed(lives: int)
signal wave_changed(wave: int, total: int)
signal speed_changed(speed: float)
signal game_over(won: bool)

const SPEEDS := [1.0, 2.0, 3.0]

var gold := 0
var lives := 0
var wave := 0            # number of waves started so far
var total_waves := 0
var speed := 1.0
var finished := false
var victory := false

func reset(start_gold: int, start_lives: int, waves_total: int) -> void:
    gold = start_gold
    lives = start_lives
    wave = 0
    total_waves = waves_total
    finished = false
    victory = false
    set_speed(1.0)
    gold_changed.emit(gold)
    lives_changed.emit(lives)
    wave_changed.emit(wave, total_waves)

func can_afford(cost: int) -> bool:
    return gold >= cost

func spend(cost: int) -> bool:
    if cost < 0 or gold < cost:
        return false
    gold -= cost
    gold_changed.emit(gold)
    return true

func add_gold(amount: int) -> void:
    if amount == 0:
        return
    gold = maxi(gold + amount, 0)
    gold_changed.emit(gold)

func lose_lives(amount: int) -> void:
    if finished or amount <= 0:
        return
    lives = maxi(lives - amount, 0)
    lives_changed.emit(lives)
    if lives == 0:
        _finish(false)

func set_wave(w: int) -> void:
    wave = w
    wave_changed.emit(wave, total_waves)

func win() -> void:
    if finished:
        return
    _finish(true)

func set_speed(s: float) -> void:
    speed = s
    Engine.time_scale = s
    speed_changed.emit(speed)

func cycle_speed() -> void:
    var i: int = SPEEDS.find(speed)
    set_speed(float(SPEEDS[(i + 1) % SPEEDS.size()]))

func _finish(did_win: bool) -> void:
    finished = true
    victory = did_win
    game_over.emit(did_win)
