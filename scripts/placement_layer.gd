extends Node2D
## PLACEMENT VISUALIZATION LAYER: available / occupied cells, selected or invalid footprint,
## translucent tower ghost and range ring. Pure overlay: ground art is never modified.
## M2: also draws the selection of an already placed tower (footprint highlight + range ring).
## Footprints: 1x1 and 2x2 use the dedicated sprites, any other size is tiled from 1x1 cell sprites.

const DIR := "res://assets/Environment/Shared/Grid/"
const RING_RADIUS := 124.0       # radius of the ring sprite in px (sprite is 256x256)
var available: Array = []        # Array of Vector2i
var occupied: Array = []
var preview_active := false
var preview_cell := Vector2i.ZERO
var preview_size := Vector2i(1, 1)
var preview_valid := true
var range_px := 0.0
var ghost_textures: Array = []   # Array of Texture2D drawn at 55% alpha
var selection_active := false    # a placed tower is selected (panel open)
var selection_cell := Vector2i.ZERO
var selection_size := Vector2i(1, 1)
var selection_range_px := 0.0
var _cache := {}

func _tex(n: String) -> Texture2D:
    if not _cache.has(n):
        _cache[n] = load(DIR + n + ".png")
    return _cache[n]

func clear() -> void:
    preview_active = false
    available = []
    ghost_textures = []
    range_px = 0.0
    queue_redraw()

func select_cell(c: Vector2i, size: Vector2i, rng_px: float) -> void:
    selection_active = true
    selection_cell = c
    selection_size = size
    selection_range_px = rng_px
    queue_redraw()

func clear_selection() -> void:
    selection_active = false
    queue_redraw()

func _draw_footprint(origin: Vector2, size: Vector2i, state: String) -> void:
    if size == Vector2i(1, 1):
        draw_texture(_tex("grid_cell_%s_64" % state), origin)
    elif size == Vector2i(2, 2):
        draw_texture(_tex("grid_footprint_%s_128" % state), origin)
    else:
        for y in size.y:
            for x in size.x:
                draw_texture(_tex("grid_cell_%s_64" % state), origin + Vector2(x, y) * 64.0)

func _draw_ring(center: Vector2, radius: float) -> void:
    if radius <= 0.0:
        return
    var s := radius / RING_RADIUS
    draw_texture_rect(_tex("grid_range_ring_256"), Rect2(center - Vector2(128, 128) * s, Vector2(256, 256) * s), false)

func _draw() -> void:
    for c in available:
        draw_texture(_tex("grid_cell_available_64"), Vector2(c) * 64.0)
    for c in occupied:
        draw_texture(_tex("grid_cell_occupied_64"), Vector2(c) * 64.0)
    if selection_active:
        var sorigin := Vector2(selection_cell) * 64.0
        _draw_footprint(sorigin, selection_size, "selected")
        _draw_ring(sorigin + Vector2(selection_size) * 32.0, selection_range_px)
    if not preview_active:
        return
    var state := "selected" if preview_valid else "invalid"
    var origin := Vector2(preview_cell) * 64.0
    _draw_footprint(origin, preview_size, state)
    var center := origin + Vector2(preview_size) * 32.0
    _draw_ring(center, range_px)
    for g in ghost_textures:
        var t := g as Texture2D
        if t != null:
            draw_texture(t, center - t.get_size() * 0.5, Color(1, 1, 1, 0.55))
