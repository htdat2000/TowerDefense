extends SceneTree
## Headless smoke test for the chase-and-survive rules. WRITTEN, NOT RUN by the author: run it and report the output.
##   godot --headless --path . --import                                       (once, builds the import cache)
##   godot --headless --path . --fixed-fps 60 -s res://scripts/smoke_test.gd
## Part 1 (smoke_checks.gd): data, assets, wave generation, flow field unit tests.
## Part 2 plays main.tscn: character and collision, building inside the radius, a timed wave, statuses, upgrades, panel, speed,
## sell, one-hit tower destruction, character damage, defeat, restart. Prints a "FAIL ..." line per broken check, exit code 1 if any failed.
## Also scan the output for engine lines: SCRIPT ERROR, Parser Error, ERROR:, WARNING:.
## The timeline uses game time, so it also works without --fixed-fps (just slower).

const Checks = preload("res://scripts/smoke_checks.gd")
const MAIN_SCENE := "res://scenes/main.tscn"
const MAX_TIME := 45.0

var _checks := Checks.new()
var _main = null                 # main.gd instance (untyped on purpose: dynamic calls)
var _gs = null                   # GameState autoload
var _t := 0.0
var _frames := 0
var _phase := 0
var _phase_t := 0.0
var _fired := 0
var _kills := 0
var _start_gold := 0

func _initialize() -> void:
    print("== smoke test: data, assets, flow field, gameplay ==")
    _gs = root.get_node_or_null("GameState")
    _checks.check(_gs != null, "autoload GameState is registered")
    _checks.run()
    var packed := load(MAIN_SCENE) as PackedScene
    _checks.check(packed != null, "main.tscn loads")
    if packed == null or _gs == null:
        return
    _main = packed.instantiate()
    root.add_child(_main)
    current_scene = _main                      # main._ready runs after _initialize, so hook signals later (step 0)

func _process(delta: float) -> bool:
    if _main == null:
        return _finish()
    _t += delta
    _frames += 1
    if _t > MAX_TIME:
        _checks.check(false, "timeline stuck in phase %d after %d s" % [_phase, int(MAX_TIME)])
        return _finish()
    var in_phase := _t - _phase_t
    match _phase:
        0:
            if _frames >= 3:
                _step_setup()
        1:
            _upgrade_all()
            if in_phase >= 1.0:
                _step_player()
                _step_wave()
        2:
            _upgrade_all()
            if in_phase >= 0.5:
                _step_spawn_extras()
        3:
            _upgrade_all()
            if in_phase >= 1.5:
                _step_statuses()
        4:
            _upgrade_all()
            if in_phase >= 9.0:
                _step_verify()
        5:
            if in_phase >= 0.5:
                _step_after_restart()
                return _finish()
    return false

func _next(p: int) -> void:
    _phase = p
    _phase_t = _t

func _on_actor_added(n) -> void:               # untyped: towers and monsters have different signals
    if n.has_signal("fired"):
        n.fired.connect(_on_fired)
    elif n.has_signal("attacked_tower"):
        n.died.connect(_on_died)

func _on_fired(_tower, _target) -> void:
    _fired += 1

func _on_died(_m) -> void:
    _kills += 1

func _upgrade_all() -> void:
    for t in _main.towers:
        if is_instance_valid(t) and t.can_upgrade():
            _main._try_upgrade(t)

# ---------------------------------------------------------------- steps
func _step_setup() -> void:
    _checks.check(_main.level != null, "main._ready built the level")
    if _main.level == null:
        _next(5)
        return
    _checks.check(_main.player != null and _main.player.alive, "the character exists and is alive")
    _main.level.actors.child_entered_tree.connect(_on_actor_added)
    _gs.add_gold(100000)
    _start_gold = _gs.gold
    _main.player.max_hp = 1000000.0               # the test must not die before the defeat step
    _main.player.hp = 1000000.0
    _checks.check(_main.level.flow.dist_at(_main.player.cell) == 0.0, "flow field is centred on the character cell")
    _checks.check(_main.level.flow.reachable(_main.level.entry_cell), "the monster entry reaches the character")
    _checks.check(_main.wave_manager.in_prep(), "the run starts in the prepare phase")
    _main._select_tower("stone")
    _checks.check(_main.selected_id == "stone", "tower button selects a tower (placement preview ran)")
    _main._cancel_selection()
    _checks.check(_main.selected_id == "", "cancel clears the picked tower")
    var near: Array = _main.level.available_cells(_main.player.global_position, _main._build_radius_px(), _main.player.cell)
    var ids: Array = _main.towers_data.keys()
    _checks.check(near.size() >= ids.size(), "buildable cells exist inside the build radius")
    if near.size() >= ids.size():
        var step := maxi(floori(near.size() / float(ids.size() + 1)), 1)
        for i in ids.size():
            var c: Vector2i = near[mini(i * step, near.size() - 1)]
            _checks.check(_main._can_build_here(c, Vector2i(1, 1)), "build rule accepts a free cell inside the radius %s" % c)
            _main._place_tower(String(ids[i]), c, 1)
            _checks.check(_main.level.grid.occupancy.has(c), "grid occupancy set at %s" % c)
        _checks.check(_main.towers.size() == ids.size(), "all towers placed")
    _checks.check(not _main._can_build_here(_main.player.cell, Vector2i(1, 1)), "build rule refuses the character cell")
    _checks.check(not _main._can_build_here(Vector2i(0, 0), Vector2i(1, 1)), "build rule refuses a cell outside the radius")
    _next(1)

func _step_player() -> void:
    var p = _main.player
    var g = _main.level.grid
    var start: Vector2i = p.cell
    p._move(Vector2(-300.0, 0.0))                  # towards the water on the left of the start cell
    _checks.check(not g.is_solid_for_player(p.cell), "the character does not enter water")
    _checks.check(p.global_position.x >= 576.0, "the character is stopped at the water edge")
    p.teleport(start)
    _checks.check(p.cell == start, "teleport puts the character back")
    if _main.towers.size() > 0:
        var t0 = _main.towers[0]
        _checks.check(not p._blocked(g.cell_center(t0.cell)), "towers do not block the character")
    _checks.check(_main.level.flow.dist_at(p.cell) == 0.0, "flow field follows the character cell")

func _step_wave() -> void:
    _checks.check(_main.wave_manager.call_next_wave(), "call_next_wave skips the prepare countdown")
    _next(2)

func _step_spawn_extras() -> void:
    _checks.check(_gs.wave >= 1, "GameState.wave counts the started wave")
    for id in _main.monsters_data.keys():
        _main._spawn_monster(String(id), false)
    _main._spawn_monster("treant", true)             # same as debug key F6
    _checks.check(_main.monsters.size() >= _main.monsters_data.size() + 1, "every monster type + boss spawned")
    _next(3)

func _step_statuses() -> void:
    var applied := 0
    for m in _main.monsters:
        if is_instance_valid(m) and m.is_alive():
            for kind in _checks.status.keys():
                m.apply_status(String(kind), 1.5)
            applied += 1
    _checks.check(applied > 0, "monsters alive to receive status effects")
    _next(4)

func _step_verify() -> void:
    for t in _main.towers:
        _checks.check(t.built and t.level == t.max_level(), "tower %s reached max level" % t.tower_id)
    _checks.check(_fired > 0, "towers fired at least once")
    if _kills == 0:
        print("WARN  no monster died in the test window (balance or ranges?)")
    _checks.check(_gs.gold < _start_gold, "upgrades charged gold")
    var chasing := 0
    for m in _main.monsters:
        if is_instance_valid(m) and m.is_alive() and m.path_left < 1.0e6:
            chasing += 1
    _checks.check(chasing > 0 or _main.monsters.is_empty(), "living monsters have a route to the character")
    # tower panel
    var t0 = _main.towers[0]
    _main._select_placed(t0)
    _checks.check(_main.panel.visible, "tower panel opens")
    var before: String = t0.targeting
    _main._on_panel_target_pressed()
    _checks.check(t0.targeting != before, "targeting mode cycles")
    _main._deselect_tower()
    _checks.check(not _main.panel.visible, "tower panel closes")
    # speed + grid toggle
    for expected in [2.0, 3.0, 1.0]:
        _gs.cycle_speed()
        _checks.check(is_equal_approx(Engine.time_scale, expected), "speed cycles to x%d" % int(expected))
    _main.level.grid_renderer.grid_visible = false
    _main.level.grid_renderer.grid_visible = true
    # sell
    var cell: Vector2i = t0.cell
    var count: int = _main.towers.size()
    _main._try_sell(t0)
    _checks.check(not _main.level.grid.occupancy.has(cell), "sell frees the grid cell")
    _checks.check(_main.towers.size() == count - 1, "sell removes the tower from the list")
    # a monster destroys a tower in one hit: no refund, cell freed at once
    var t1 = _main.towers[0]
    var cell1: Vector2i = t1.cell
    var gold_before: int = _gs.gold
    _main._on_monster_attacked_tower(null, t1)
    _checks.check(not _main.level.grid.occupancy.has(cell1), "a destroyed tower frees its grid cell at once")
    _checks.check(not _main.towers.has(t1), "a destroyed tower leaves the tower list")
    _checks.check(t1.is_destroyed(), "the tower plays its destroyed state")
    _checks.check(_gs.gold == gold_before, "a destroyed tower gives no refund")
    _main._on_monster_attacked_tower(null, t1)       # second hit on the same tower must do nothing
    _checks.check(_main.towers.size() == count - 2, "a second hit on a destroyed tower is ignored")
    # the character takes damage, then dies: defeat
    var p = _main.player
    var hp0: float = p.hp
    _main._on_monster_attacked_player(null, 5.0)
    _checks.check(p.hp < hp0, "monster attack damages the character")
    p.take_damage(p.hp + 1.0)
    _checks.check(not p.alive, "the character dies at 0 hp")
    _checks.check(_gs.finished, "character death -> defeat")
    _checks.check(paused, "tree paused on game over")
    _checks.check(_main.overlay.visible, "result overlay visible")
    _main._on_restart_pressed()
    _next(5)

func _step_after_restart() -> void:
    var m = current_scene
    _checks.check(m != null and not is_instance_valid(_main), "restart reloaded the scene")
    _checks.check(not paused, "tree unpaused after restart")
    _checks.check(is_equal_approx(Engine.time_scale, 1.0), "time scale back to x1 after restart")
    _checks.check(not _gs.finished and _gs.wave == 0, "GameState reset after restart")
    if m != null and is_instance_valid(m):
        _checks.check(_gs.gold == m.wave_manager.start_gold(), "gold reset from level data")
        _checks.check(m.player.alive and is_equal_approx(m.player.hp, m.player.max_hp), "the character is back at full hp")
        _checks.check(m.wave_manager.in_prep(), "the new run starts in the prepare phase")

func _finish() -> bool:
    print("== %d checks passed, %d failed ==" % [_checks.passed, _checks.failed])
    quit(1 if _checks.failed > 0 else 0)
    return true
