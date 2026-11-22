# KNOWN ISSUES
- The project has been written and statically checked but **never run in Godot** (this is the single place this is stated). M0 resolves it.
- Untested first-run risks: `level.gd` (runtime TileSet + autotile painting), `tower.gd`/`monster.gd` (SpriteFrames from strips, frame events), `placement_layer.gd` drawing, `main.gd` UI lambdas, Phase 5 VFX scripts.
- Tile layers use Nearest filtering to avoid seams; fractional zoom may still show seams (add atlas padding or use integer scaling).
- Preview-only: ice explosion offset in `prototype_with_starter_towers.png` (not a sprite bug).
- `project.godot` features says "4.7"; README says 4.3+. Minimum is 4.3 (TileMapLayer).
