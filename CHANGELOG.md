# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.0] - 2026-11-22

### Added

- **A picture for every system**: 354 names, every system of Batocera 43 and those of other
  boards (PlayStation 2 and 3, GameCube, Wii, Switch, Xbox...). About forty machines have a
  drawing of their own; the others share one with their family (a home computer in its keyboard,
  a computer with its monitor, a console with cartridges or discs, a handheld, an arcade
  cabinet, a pinball table) in their own colors; ported games get a computer, collections a
  neon sign. The theme grows from 4 to about 36 MB.
- **Loading screen** (`splash.xml`), shown while EmulationStation starts: a picture of the
  theme's own for no system in particular (cartridges and a controller on the pier, the sun in
  the middle), with the bottom line of every other screen as the progress bar and the engine's
  message where the help prompts are. `tools/render-system-backgrounds.py splash` draws it.

### Changed

- Carbon's photos are now only a fallback, for a system the theme doesn't know.

## [1.0.0] - 2026-11-21

The first version: the home, the game list, the menus and the top bar, for Batocera 43.

### Added

- **Home**, after a console's home screen: one row of square tiles, 5 px apart, with each
  system's logo in white; the selected one, always in the second place, grows into a card in a
  thin white frame with its number of games, and its name, maker and year beside it.
- **The system's panel** under the selected card, shown after the selection rests a second:
  favorites, games played, play time, last day played, the most played game, and
  RetroAchievements and Netplay when the system supports them.
- **A picture for 25 systems**, drawn by `tools/render-system-backgrounds.py`: the machine, inked
  and lit from behind, on a pier in front of a coastal city at sunset, in four moods of sky. The
  other systems show Batocera's own photo, read in place and darkened.
- **System logos in white**: Batocera's own logos (Carbon's, read in place, never copied), drawn
  white by the theme's shader; a logo on a dark plate also loses its dark parts, and a system
  without a usable logo shows its name. `tools/preview-logos.py` previews them all.
- **Game list**: the system's logo as the header, the games in a list at the left with the
  selected row solid in a white frame, and at the right the game's cover, name, eight details as
  labels over values, and description. A game's video plays in the cover's place after a few
  seconds; a game without a cover shows its picture, or a plain tile.
- **Menus**: a dark page over the whole screen and a square panel in its middle, the theme's
  fonts, the selected row solid, square buttons, and 18 white icons of the theme's own.
- **Top bar**: the connected controllers, lightguns and wheels, lit while in use; the
  RetroAchievements avatar and name when an account is set up; the network and the clock.
- **Accent color** option: blue, purple, teal, red or gray.
- **English and Brazilian Portuguese** labels.
- **Documentation**: `docs/STYLE.md` (the look every screen follows), `docs/ARCHITECTURE.md`
  (how the theme is built and what was learned about the engine) and `docs/PUBLISHING.md`.
- **Tools**, in pure Python: `check.py` (XML, includes, files, variables, element names, image
  sizes), `render-system-backgrounds.py`, `render-icons.py`, `render-frames.py`,
  `render-background.py`, `preview-logos.py`, `deploy.sh` and `package.sh`; CI checks every
  push, and a `v*` tag publishes the release ZIP.
- The Inter font (SIL Open Font License); the theme itself is under the MIT license.

[Unreleased]: https://github.com/monteirohat/batox-theme/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/monteirohat/batox-theme/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/monteirohat/batox-theme/releases/tag/v1.0.0
