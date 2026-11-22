# ASSET CATALOG (GENERATED - do not edit; run tools/art/gen_catalog.py)

PNG files: environment 33, towers 123, monsters 110, projectiles 10, vfx 32.

## Towers (96x96, pivot centre, 5 levels, head faces EAST)
| id | folder | head rotates | event frame | projectile | range (cells) | cooldown | damage |
|---|---|---|---|---|---|---|---|
| stone | Stone | True | 3 | projectile_stone.png | 3.2 | 1.1 | 6 |
| archer | Archer | True | 5 | projectile_arrow.png | 3.8 | 0.6 | 3 |
| frost | Frost | False | 5 | projectile_ice_shard.png | 3.0 | 1.4 | 2 |

Strips per level: spawn, base_idle, head_idle, head_attack, destroyed, base, head_static. Anim fps: build 14, idle 8, attack 16, destroyed 12.

## Monsters (4 directions E,S,W,N; strips in Strips/)
| id | frame | role | stride | hp | speed |
|---|---|---|---|---|---|
| slime | 64 | Normal | 20 | 12 | 60 |
| goblin | 80 | Fast | 18 | 10 | 85 |
| boar | 80 | Fast charger | 30 | 18 | 120 |
| mushroom | 64 | Special (spore burst) | 18 | 16 | 55 |
| treant | 96 | Tank / Elite | 24 | 60 | 40 |

Frames/fps: idle 6 @8 loop, walk 8 @12 loop, attack 8 @14 (damage frame 4), hit 4 @12, death 10 @12, spawn 10 @12 (E only).

## Status effects
| kind | speed mult | dps |
|---|---|---|
| freeze | 0.0 | 0.0 |
| slow | 0.5 | 0.0 |
| stun | 0.0 | 0.0 |
| burning | 1.0 | 3.0 |
| poison | 0.85 | 2.0 |

## VFX (horizontal strips, pivot centre)
| name | group | frames | frame size | fps | loop | tintable |
|---|---|---|---|---|---|---|
| fireball | projectile | 1 | 32x32 | 0 | False | False |
| lightning_bolt | projectile | 1 | 48x16 | 0 | False | False |
| poison_glob | projectile | 1 | 32x32 | 0 | False | False |
| cannonball | projectile | 1 | 32x32 | 0 | False | False |
| magic_orb | projectile | 1 | 32x32 | 0 | False | False |
| nature_seed | projectile | 1 | 32x16 | 0 | False | False |
| sniper_round | projectile | 1 | 48x12 | 0 | False | False |
| fire_explosion | impact | 8 | 80x80 | 16 | False | False |
| lightning_impact | impact | 6 | 64x64 | 18 | False | False |
| poison_splash | impact | 7 | 64x64 | 14 | False | False |
| magical_burst | impact | 8 | 64x64 | 16 | False | False |
| nature_root_impact | impact | 8 | 64x64 | 14 | False | False |
| cannon_explosion | impact | 9 | 96x96 | 16 | False | False |
| status_freeze | status | 8 | 64x64 | 10 | True | False |
| status_burning | status | 8 | 64x64 | 12 | True | False |
| status_poison | status | 8 | 64x64 | 10 | True | False |
| status_slow | status | 8 | 64x64 | 10 | True | False |
| status_stun | status | 8 | 64x64 | 10 | True | False |
| tower_spawn_particles | tower | 8 | 96x96 | 14 | False | True |
| tower_destruction_particles | tower | 10 | 96x96 | 12 | False | False |
| tower_upgrade | tower | 12 | 96x96 | 14 | False | False |
| upgrade_ready | tower | 8 | 32x32 | 8 | True | False |
| placement_valid_pulse | tower | 8 | 96x96 | 10 | True | False |
| placement_invalid_pulse | tower | 8 | 96x96 | 10 | True | False |
| sell_effect | tower | 8 | 96x96 | 14 | False | False |
| enemy_spawn_particles | enemy | 8 | 64x64 | 14 | False | True |
| enemy_death_particles | enemy | 8 | 64x64 | 14 | False | True |
| critical_hit | enemy | 6 | 64x64 | 16 | False | False |
| boss_appearance | enemy | 12 | 192x192 | 12 | False | False |
| coin_spin | feedback | 8 | 24x24 | 12 | True | False |
| gold_collect_sparkle | feedback | 6 | 48x48 | 16 | False | False |
| level_complete | feedback | 12 | 192x192 | 12 | False | False |
| wave_transition | feedback | 8 | 128x128 | 12 | False | False |
| damage_digits_normal | feedback | 11 | 22x30 | 0 | False | False |
| damage_digits_crit | feedback | 11 | 30x40 | 0 | False | False |
| damage_digits_heal | feedback | 11 | 22x30 | 0 | False | False |

Environment: grassland_tileset_32.png (32 px tiles, 8 columns; row 0 grass, rows 1-6 path, rows 7-12 water); decorations, objects, shadows and shared grid sprites under assets/Environment/.
