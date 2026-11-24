extends Node2D
## Floating monster health bar (M3). Child of the monster, drawn above all actors (z_index set by monster.gd).
## Hidden at full hp (bosses always show it). Colour follows the hp fraction. A small shield icon marks armored monsters.
## Pure drawing: monster.gd calls setup() once and set_fraction() whenever hp changes.

const BORDER := Color(0.0, 0.0, 0.0, 0.75)
const BACK := Color(0.18, 0.12, 0.14, 0.9)
const SHIELD := Color(0.62, 0.68, 0.82)
const SHIELD_EDGE := Color(0.2, 0.22, 0.32)

var frac := 1.0
var bar_w := 30.0
var bar_h := 4.0
var armor := 0.0
var boss := false

func setup(width: float, y: float, armor_value: float, is_boss: bool) -> void:
    bar_w = width * (1.3 if is_boss else 1.0)
    bar_h = 6.0 if is_boss else 4.0
    position = Vector2(0.0, y)
    armor = armor_value
    boss = is_boss
    visible = is_boss
    queue_redraw()

func set_fraction(f: float) -> void:
    var nf := clampf(f, 0.0, 1.0)
    if is_equal_approx(nf, frac):
        return
    frac = nf
    visible = boss or frac < 0.999
    queue_redraw()

func _bar_color() -> Color:
    if frac > 0.6:
        return Color(0.35, 0.9, 0.35)
    if frac > 0.3:
        return Color(0.98, 0.82, 0.25)
    return Color(0.92, 0.3, 0.28)

func _draw() -> void:
    var x := -bar_w * 0.5
    draw_rect(Rect2(x - 1.0, -1.0, bar_w + 2.0, bar_h + 2.0), BORDER)
    draw_rect(Rect2(x, 0.0, bar_w, bar_h), BACK)
    var fw := bar_w * frac
    if fw > 0.0:
        draw_rect(Rect2(x, 0.0, fw, bar_h), _bar_color())
        draw_rect(Rect2(x, 0.0, fw, 1.0), Color(1.0, 1.0, 1.0, 0.3))
    if armor > 0.0:
        var sx := x - 10.0
        var pts := PackedVector2Array([
            Vector2(sx, -2.0), Vector2(sx + 7.0, -2.0), Vector2(sx + 7.0, bar_h + 1.0),
            Vector2(sx + 3.5, bar_h + 4.0), Vector2(sx, bar_h + 1.0)])
        draw_colored_polygon(pts, SHIELD)
        var closed := pts.duplicate()
        closed.append(pts[0])
        draw_polyline(closed, SHIELD_EDGE, 1.0)
