extends RefCounted
## Static VFX helper (no instance needed): const VFX = preload("res://scripts/vfx_library.gd")
##   VFX.play_once(parent, "fire_explosion", pos, scale, tint)   one-shot, frees itself
##   VFX.make_loop("status_freeze", scale)                       looping sprite, caller adds it as a child
## Effect list, frame sizes, fps and loop flags come from res://data/vfx.json (generated from the art atlas).

const DATA_PATH := "res://data/vfx.json"
const GLYPHS := "0123456789+"
static var _data: Dictionary = {}
static var _frames: Dictionary = {}
static var _glyphs: Dictionary = {}

static func _ensure() -> void:
    if not _data.is_empty():
        return
    var f := FileAccess.open(DATA_PATH, FileAccess.READ)
    if f == null:
        push_error("VfxLibrary: cannot open " + DATA_PATH)
        return
    var parsed = JSON.parse_string(f.get_as_text())
    if parsed is Dictionary:
        _data = parsed

static func has_effect(vfx_name: String) -> bool:
    _ensure()
    return _data.has(vfx_name)

static func info(vfx_name: String) -> Dictionary:
    _ensure()
    return _data.get(vfx_name, {})

static func get_frames(vfx_name: String) -> SpriteFrames:
    _ensure()
    if _frames.has(vfx_name):
        return _frames[vfx_name]
    var e: Dictionary = _data[vfx_name]
    var tex := load(String(e["path"])) as Texture2D
    var sf := SpriteFrames.new()
    if sf.has_animation(&"default"):
        sf.remove_animation(&"default")
    sf.add_animation(&"play")
    sf.set_animation_speed(&"play", maxf(float(e["fps"]), 1.0))
    sf.set_animation_loop(&"play", bool(e["loop"]))
    var fw := int(e["frame_w"])
    var fh := int(e["frame_h"])
    for i in int(e["frames"]):
        var at := AtlasTexture.new()
        at.atlas = tex
        at.region = Rect2(i * fw, 0, fw, fh)
        sf.add_frame(&"play", at)
    _frames[vfx_name] = sf
    return sf

static func _make(vfx_name: String, scale_f: float, tint: Color) -> AnimatedSprite2D:
    _ensure()
    if not _data.has(vfx_name):
        push_error("VfxLibrary: unknown effect '%s' (see data/vfx.json)" % vfx_name)
        return null
    var s := AnimatedSprite2D.new()
    s.sprite_frames = get_frames(vfx_name)
    s.scale = Vector2(scale_f, scale_f)
    s.modulate = tint
    return s

## Looping effect (status overlays, indicators). Not added to the tree; it starts playing when it enters it.
static func make_loop(vfx_name: String, scale_f: float = 1.0, tint: Color = Color.WHITE) -> AnimatedSprite2D:
    var s := _make(vfx_name, scale_f, tint)
    if s != null:
        s.autoplay = "play"
    return s

## One-shot effect at a world position. Frees itself when finished (loop effects keep playing).
static func play_once(parent: Node, vfx_name: String, pos: Vector2, scale_f: float = 1.0, tint: Color = Color.WHITE) -> AnimatedSprite2D:
    if parent == null or not is_instance_valid(parent):
        return null
    var s := _make(vfx_name, scale_f, tint)
    if s == null:
        return null
    parent.add_child(s)
    s.global_position = pos
    if not bool(_data[vfx_name]["loop"]):
        s.animation_finished.connect(s.queue_free)
    s.play("play")
    return s

## One glyph of a damage_digits_* set ("0123456789+").
static func glyph_texture(set_name: String, ch: String) -> Texture2D:
    _ensure()
    var idx := GLYPHS.find(ch)
    if idx < 0 or not _data.has(set_name):
        return null
    var key := "%s:%d" % [set_name, idx]
    if _glyphs.has(key):
        return _glyphs[key]
    var e: Dictionary = _data[set_name]
    var at := AtlasTexture.new()
    at.atlas = load(String(e["path"])) as Texture2D
    at.region = Rect2(idx * int(e["frame_w"]), 0, int(e["frame_w"]), int(e["frame_h"]))
    _glyphs[key] = at
    return at
