extends Node2D
## The controllable character. Move with WASD or the arrow keys. Monsters chase it, its death is the defeat.
## Collision: stopped by water and blocked cells only, towers never block the player (grid_manager.is_solid_for_player).
## Placeholder art is drawn with shapes in _draw, replace it with sprites when the hero art exists.
## Numbers come from data/player.json (hp, speed, collision_radius, build_radius_cells, regen_per_sec).
## Signals go up: hp_changed, cell_changed (flow field recompute), damaged, died.

const HealthBar = preload("res://scripts/health_bar.gd")

signal hp_changed(hp: float, max_hp: float)
signal cell_changed(cell: Vector2i)
signal damaged(amount: float)
signal died

var grid                          # GridManager instance (dynamic on purpose)
var hp := 100.0
var max_hp := 100.0
var speed := 150.0
var radius := 14.0
var build_radius_cells := 4.0
var regen := 0.0
var cell := Vector2i(-1, -1)
var alive := true
var facing := Vector2.DOWN
var bar                           # HealthBar script instance
var _flash := 0.0
var _walk_t := 0.0
var _moving := false

func setup(cfg: Dictionary, grid_ref, start_cell: Vector2i) -> void:
    grid = grid_ref
    max_hp = float(cfg.get("hp", 100.0))
    hp = max_hp
    speed = float(cfg.get("speed", 150.0))
    radius = float(cfg.get("collision_radius", 14.0))
    build_radius_cells = float(cfg.get("build_radius_cells", 4.0))
    regen = float(cfg.get("regen_per_sec", 0.0))
    bar = HealthBar.new()
    bar.name = "HealthBar"
    bar.z_index = 2
    add_child(bar)
    bar.setup(30.0, -radius - 22.0, 0.0, true)
    teleport(start_cell)

func is_alive() -> bool:
    return alive

func teleport(c: Vector2i) -> void:
    position = grid.cell_center(c)
    _update_cell()

func take_damage(amount: float) -> void:
    if not alive or amount <= 0.0:
        return
    hp = maxf(hp - amount, 0.0)
    _flash = 0.25
    bar.set_fraction(hp / max_hp)
    damaged.emit(amount)
    hp_changed.emit(hp, max_hp)
    if hp <= 0.0:
        alive = false
        died.emit()

func heal(amount: float) -> void:
    if not alive or amount <= 0.0 or hp >= max_hp:
        return
    hp = minf(hp + amount, max_hp)
    bar.set_fraction(hp / max_hp)
    hp_changed.emit(hp, max_hp)

# ---------------------------------------------------------------- movement
func _input_vector() -> Vector2:
    var v := Vector2.ZERO
    if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP):
        v.y -= 1.0
    if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN):
        v.y += 1.0
    if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT):
        v.x -= 1.0
    if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT):
        v.x += 1.0
    return v

func _blocked(p: Vector2) -> bool:
    for ox in [-radius, radius]:
        for oy in [-radius, radius]:
            if grid.is_solid_for_player(grid.world_to_cell(p + Vector2(ox, oy))):
                return true
    return false

func _move_once(step: Vector2) -> void:
    var p := position
    var nx := Vector2(p.x + step.x, p.y)
    if not _blocked(nx):
        p = nx
    var ny := Vector2(p.x, p.y + step.y)
    if not _blocked(ny):
        p = ny
    position = p

func _move(step: Vector2) -> void:
    var n := maxi(int(ceil(step.length() / 12.0)), 1)
    var part := step / float(n)
    for i in n:
        _move_once(part)
    _update_cell()

func _update_cell() -> void:
    var nc: Vector2i = grid.world_to_cell(position)
    if nc != cell:
        cell = nc
        cell_changed.emit(cell)

func _process(delta: float) -> void:
    _walk_t += delta
    _flash = maxf(_flash - delta, 0.0)
    if alive:
        var v := _input_vector()
        _moving = v != Vector2.ZERO
        if _moving:
            v = v.normalized()
            facing = v
            _move(v * speed * delta)
        if regen > 0.0 and hp < max_hp:
            heal(regen * delta)
    queue_redraw()

func _draw() -> void:
    var bob := 0.0
    if _moving:
        bob = sin(_walk_t * 14.0) * 1.5
    draw_set_transform(Vector2(2.0, 8.0), 0.0, Vector2(1.0, 0.6))
    draw_circle(Vector2.ZERO, radius, Color(0.08, 0.16, 0.08, 0.3))
    draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
    var body := Color(0.31, 0.55, 0.9).lerp(Color.WHITE, _flash / 0.25)
    if not alive:
        body = Color(0.5, 0.5, 0.55)
    draw_circle(Vector2(0.0, bob), radius + 1.5, Color(0.2, 0.16, 0.2))
    draw_circle(Vector2(0.0, bob), radius, body)
    draw_circle(Vector2(-4.0, -5.0 + bob), radius * 0.4, Color(1.0, 1.0, 1.0, 0.35))
    var f := facing.normalized() * radius * 0.6
    draw_circle(f + Vector2(0.0, bob), 3.6, Color.WHITE)
    draw_circle(f * 1.2 + Vector2(0.0, bob), 1.8, Color(0.14, 0.11, 0.16))
