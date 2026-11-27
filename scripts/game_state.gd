extends Node
## Autoload "GameState": run-wide state (gold, wave, speed) and its signals.
## The character's hp lives in player.gd. The run is endless: it only ends when the character dies (defeat).
## No gameplay numbers live here: the starting gold is passed to reset() from the level data (data/waves_*.json).
## Signals go up; UI and main.gd listen. Never connect lambdas to this autoload, they outlive scene reloads.

signal gold_changed(gold: int)
signal wave_changed(wave: int)
signal speed_changed(speed: float)
signal game_over(wave_reached: int)

const SPEEDS := [1.0, 2.0, 3.0]

var gold := 0
var wave := 0            # number of waves started so far, also the score
var speed := 1.0
var finished := false

func reset(start_gold: int) -> void:
    gold = start_gold
    wave = 0
    finished = false
    set_speed(1.0)
    gold_changed.emit(gold)
    wave_changed.emit(wave)

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

func set_wave(w: int) -> void:
    wave = w
    wave_changed.emit(wave)

func defeat() -> void:
    if finished:
        return
    finished = true
    game_over.emit(wave)

func set_speed(s: float) -> void:
    speed = s
    Engine.time_scale = s
    speed_changed.emit(speed)

func cycle_speed() -> void:
    var i: int = SPEEDS.find(speed)
    set_speed(float(SPEEDS[(i + 1) % SPEEDS.size()]))
