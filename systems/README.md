# Per-system artwork

One folder per system, named as the system's `${system.theme}` (its name in Batocera's
`es_systems.cfg`: `snes`, `megadrive`, `gba`...):

| File | Size | Use |
|---|---|---|
| `background.jpg` | 1920×1080, about 100 KB | behind the home and the game list of the system |

Every system Batocera knows has one, drawn by `tools/render-system-backgrounds.py` (the machine
on a pier at sunset): don't edit them by hand, change the script and run it for that system. A
system the script doesn't know shows Carbon's photo, read where Batocera installs it, darkened.
The tiles' logos are Carbon's too, drawn in white. See
[docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md#per-system-artwork).
