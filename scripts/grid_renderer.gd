extends Node2D
## GRID RENDERING LAYER. Independent from ground tiles. Toggle with grid_visible.
## Never touches the ground/path/water layers.

const LINE_TEX := "res://assets/Environment/Shared/Grid/grid_line_64.png"
var cols := 0
var rows := 0
var grid_visible := true:
    set(v):
        grid_visible = v
        queue_redraw()
var _tex: Texture2D

func setup(c: int, r: int) -> void:
    cols = c
    rows = r
    _tex = load(LINE_TEX) as Texture2D
    queue_redraw()

func _draw() -> void:
    if not grid_visible or _tex == null:
        return
    for y in rows:
        for x in cols:
            draw_texture(_tex, Vector2(x * 64, y * 64))
