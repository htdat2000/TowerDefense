extends RefCounted
## Builds SpriteFrames at runtime from horizontal PNG strips (frame N is at x = N * frame_width).
## Strip files and fps/loop values follow Documentation/*.json and 03_ASSET_SPECS.md.

static func new_frames() -> SpriteFrames:
    var f := SpriteFrames.new()
    if f.has_animation(&"default"):
        f.remove_animation(&"default")
    return f

static func add_strip(frames: SpriteFrames, anim: String, path: String, frame_size: Vector2i, fps: float, loop: bool) -> bool:
    var tex := load(path) as Texture2D
    if tex == null:
        push_error("SpriteFramesBuilder: missing strip " + path)
        return false
    var count := int(tex.get_width() / float(frame_size.x))
    if not frames.has_animation(anim):
        frames.add_animation(anim)
    frames.set_animation_speed(anim, fps)
    frames.set_animation_loop(anim, loop)
    for i in count:
        var at := AtlasTexture.new()
        at.atlas = tex
        at.region = Rect2(i * frame_size.x, 0, frame_size.x, frame_size.y)
        frames.add_frame(anim, at)
    return true
