# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Architecture (docs/ARCHITECTURE.md) and skeleton: design tokens, the system view, the Home,
  Library and Detailed game views, accent color and animation options, English and Brazilian
  Portuguese, the waves background drawn by `tools/render-background.py`, `tools/check.py`,
  `tools/deploy.sh`, `tools/package.sh`, and CI and release workflows.
- The home, after a console's home screen: one row of square tiles 5 px apart with each
  system's brand logo in white; the selected one, always in the second place, grows 1.7 times into a
  card with a strip and a down arrow under it and a thin white frame, with the system's name,
  maker, year and number of games at its right; the selected system's art behind, darkened, all
  following the selection, the number of games at once; the clock in a light font with the network icon at its left, a
  separator and a help bar.
- A background of the theme's own for 25 systems, drawn by `tools/render-system-backgrounds.py`:
  the machine, inked and lit from behind, on a pier in front of a coastal city at sunset. The
  other systems keep Batocera's own photo, read in place and darkened.
- The systems' logos are Batocera's own (Carbon's, read in place), drawn in white by the theme's
  shader (`_inc/shaders/white.glsl`); a logo on a dark plate also loses its dark parts, and a
  system without a usable logo shows its name. `tools/preview-logos.py` previews them all.
- `tools/render-icons.py` draws the top bar's icons and the down arrow.
- A first version of the game list (Home view): a row of box-art tiles, the game's art behind
  and its details under the row.
- Inter (OFL), light, regular and semibold, as the theme's font, and `tools/render-frames.py` for the selection glow.
- The top bar's left: the connected controllers, lightguns and wheels (white icons of the
  theme's own, lit while in use) on every view, and on the home the RetroAchievements avatar and
  name when an account is configured in Batocera.
- `tools/check.py` checks that every element of a view is one the engine knows.
- MIT license (the Inter font keeps the SIL Open Font License).
