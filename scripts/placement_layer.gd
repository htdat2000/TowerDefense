extends Node2D
## PLACEMENT VISUALIZATION LAYER: available / occupied cells, selected or invalid footprint,
## translucent tower ghost and range ring. Pure overlay: ground art is never modified.

const DIR := "res://assets/Environment/Shared/Grid/"
var available: Array = []        # Array of Vector2i
var occupied: Array = []
var preview_active := false
var preview_cell := Vector2i.ZERO
var preview_size := Vector2i(1, 1)
var preview_valid := true
var range_px := 0.0
var ghost_textures: Array = []   # Array of Texture2D drawn at 55% alpha
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

func _draw() -> void:
    for c in available:
        draw_texture(_tex("grid_cell_available_64"), Vector2(c) * 64.0)
    for c in occupied:
        draw_texture(_tex("grid_cell_occupied_64"), Vector2(c) * 64.0)
    if not preview_active:
        return
    var state := "selected" if preview_valid else "invalid"
    var origin := Vector2(preview_cell) * 64.0
    if preview_size == Vector2i(1, 1):
        draw_texture(_tex("grid_cell_%s_64" % state), origin)
    else:
        draw_texture(_tex("grid_footprint_%s_128" % state), origin)   # 2x2 footprint
    var center := origin + Vector2(preview_size) * 32.0
    if range_px > 0.0:
        var s := range_px / 124.0                                      # ring sprite radius = 124 px
        draw_texture_rect(_tex("grid_range_ring_256"), Rect2(center - Vector2(128, 128) * s, Vector2(256, 256) * s), false)
    for g in ghost_textures:
        var t := g as Texture2D
        draw_texture(t, center - t.get_size() * 0.5, Color(1, 1, 1, 0.55))
