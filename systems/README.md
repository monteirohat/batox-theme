# Per-system artwork

One folder per system, named as the system's `${system.theme}` (its name in Batocera's
`es_systems.cfg`: `snes`, `megadrive`, `gba`...):

| File | Size | Use |
|---|---|---|
| `logo.svg` | | the system's tile in the system view |
| `background.jpg` | 1920×1080, under 300 KB | behind the system view and the system's game lists |

Systems without a folder use `_default/`. See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md#per-system-artwork).
