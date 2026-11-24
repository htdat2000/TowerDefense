extends Node2D
## Floating damage number built from the damage_digits_* glyph strips. Set position, add to a layer, then call setup().
## kind: "normal" | "crit" | "heal". Frees itself after the tween.
const VFX = preload("res://scripts/vfx_library.gd")

func setup(amount: int, kind: String = "normal") -> void:
    var glyph_set := "damage_digits_" + kind      # not "set_name": that would shadow Node.set_name()
    var text := str(maxi(amount, 0))
    if kind == "heal":
        text = "+" + text
    var info := VFX.info(glyph_set)
    if info.is_empty():
        queue_free()
        return
    var adv := float(info["frame_w"]) * 0.62          # glyph cells have padding; tighten the spacing
    var total := adv * text.length()
    for i in text.length():
        var s := Sprite2D.new()
        s.texture = VFX.glyph_texture(glyph_set, text[i])
        s.position = Vector2(-total * 0.5 + adv * (i + 0.5), 0.0)
        add_child(s)
    var rise := 34.0 if kind == "crit" else 26.0
    scale = Vector2(0.6, 0.6)
    var tw := create_tween()
    tw.set_parallel(true)
    tw.tween_property(self, "scale", Vector2.ONE, 0.15).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
    tw.tween_property(self, "position:y", position.y - rise, 0.7)
    tw.tween_property(self, "modulate:a", 0.0, 0.25).set_delay(0.45)
    tw.chain().tween_callback(queue_free)
