extends RefCounted
## Tiny JSON helper. JSON numbers arrive as float: wrap with int() where an int is needed.

static func load_json(path: String) -> Variant:
    var f := FileAccess.open(path, FileAccess.READ)
    if f == null:
        push_error("Data.load_json: cannot open " + path)
        return null
    return JSON.parse_string(f.get_as_text())
