extends RefCounted
## Plays a one-shot strip effect (impact, explosion...) and frees itself.
const SFB = preload("res://scripts/sprite_frames_builder.gd")

static func play(parent: Node, strip_path: String, frame_px: int, fps: float, pos: Vector2) -> AnimatedSprite2D:
    var spr := AnimatedSprite2D.new()
    var frames := SFB.new_frames()
    SFB.add_strip(frames, "play", strip_path, Vector2i(frame_px, frame_px), fps, false)
    spr.sprite_frames = frames
    parent.add_child(spr)
    spr.global_position = pos
    spr.animation_finished.connect(spr.queue_free)
    spr.play("play")
    return spr
