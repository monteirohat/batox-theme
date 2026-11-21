# Per-system artwork

One folder per system, named as the system's `${system.theme}` (its name in Batocera's
`es_systems.cfg`: `snes`, `megadrive`, `gba`...):

| File | Size | Use |
|---|---|---|
| `background.jpg` | 1920×1080, about 90 KB | behind the home when the system is selected |

The backgrounds are drawn by `tools/render-system-backgrounds.py` (the machine on a pier at
sunset): don't edit them by hand, change the script and run it again. A system without one shows
Carbon's photo, read where Batocera installs it, darkened. The tiles' logos are Carbon's too,
drawn in white. See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md#per-system-artwork).
