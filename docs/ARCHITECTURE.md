# Architecture

batox-theme is a dark EmulationStation theme for Batocera in the style of a modern console's home
screen: one row of large tiles, the selected tile grows, its title and details appear under it,
and the background turns into the selected game's artwork.

- [Goals](#goals)
- [Target](#target)
- [Repository layout](#repository-layout)
- [Design tokens](#design-tokens)
- [Views](#views)
- [Per-system artwork](#per-system-artwork)
- [Options in Batocera's menu](#options-in-batoceras-menu)
- [Performance](#performance)
- [Tools and workflow](#tools-and-workflow)
- [Milestones](#milestones)
- [Legal](#legal)
- [Open decisions](#open-decisions)

## Goals

- **A console home screen.** A single row of square tiles in the middle of the screen; the
  selected one is larger, framed by a soft glow, with its name next to it.
- **The game in front.** In a game list, the background becomes the selected game's fanart or
  screenshot, darkened, and the area under the row shows its details: description, developer,
  year, genre, players, rating.
- **Dark and calm.** A deep navy background with slow light waves, white type, one accent color.
- **Readable from the sofa.** Sized for a 1080p TV first; still usable on 720p, 4:3 and small
  screens.
- **Light on a Raspberry Pi 4.** No blur shaders or videos by default.

Not goals: copying any console's assets (see [Legal](#legal)), and themed per-system layouts
(every system uses the same layout, with its own artwork).

## Target

| | |
|---|---|
| Engine | batocera-emulationstation, theme `formatVersion` 7 |
| Batocera | 43 and newer (tested on 43.1) |
| Reference screen | 1920×1080 (16:9) |
| Also | 1280×720, 4:3, vertical screens and tiny screens through `if`/`tinyScreen`/`verticalScreen` |
| Install path | `/userdata/themes/batox-theme` |

Engine features used, all present in Batocera's own theme (es-theme-carbon) on 43.1:

- `<variables>` with evaluated expressions (`${screen.ratio}`, `${screen.height}`), used for the
  design tokens and for screen-size conditions;
- `<customView name="..." inherits="grid">`, for the Home and Library game views;
- `<imagegrid>` with `autoLayout`, `scrollDirection`, `centerSelection`, `scrollLoop` and an
  `<itemTemplate>` of `container`/`image`/`text`/`ninepatch`, with `storyboard` animations on
  `activate`/`deactivate`;
- `<carousel name="systemcarousel">` of `type` horizontal for the system view;
- data bindings in `itemTemplate` and paths: `{game:image}`, `{game:thumbnail}`,
  `{game:marquee}`, `{game:fanart}`, `{game:folder}`, `{system:fullName}`, `{system:logo}`, and
  `exists()`/`?:` expressions;
- metadata elements `md_description`, `md_developer`, `md_genre`, `md_releasedate`, `md_players`,
  `md_rating`, `md_name`, `md_image`, `md_fanart`;
- `<subset>` with `displayName`, `appliesTo` and `ifSubset`, shown in Batocera's theme menu;
- `<include lang="...">` for translated names;
- `${themePath}` and `${system.theme}` in paths.

## Repository layout

```
batox-theme/
  theme.xml               entry point: includes, languages, subsets, views
  _inc/
    variables.xml         design tokens: the only place colors, sizes and fonts are set
    backgrounds/          generated backgrounds (tools/render-background.py)
    frames/               ninepatch frames: tile border, selection glow, panels; white.png
    fonts/                OFL fonts and their licenses (milestone 2)
    icons/                SVG icons: help prompts, battery, controller (milestone 3)
  views/
    screen.xml            always on top: clock, battery, controllers
    splash.xml            loading screen (milestone 3)
    menu.xml              EmulationStation's menus, dark and rounded (milestone 3)
    system.xml            Home of systems: the row of system tiles
    home.xml              customView "Home" (inherits grid): the row of game tiles
    library.xml           customView "Library" (inherits grid): every game, several rows
    detailed.xml          list view, for long lists and small screens
    common.xml            shared by game views: background art, details area, help bar
  subsets/
    accent/               accent colors: blue (default), purple, teal, red, gray
    motion/               animations on (default) or off
    background/           waves, game art (default), plain (milestone 5)
  systems/
    README.md             the artwork convention
    _default/             fallback tile and background (milestone 4)
    <system>/             per-system artwork, named by ${system.theme} (milestone 4)
  lang/                   en.xml (always included), pt_BR.xml, more later
  tools/
    check.py              validates the theme (XML, includes, paths, sizes)
    render-background.py  draws the wave backgrounds, in pure Python
    deploy.sh             copies the theme to a console over SSH
    package.sh            builds the release ZIP
  docs/
    ARCHITECTURE.md       this file
    screenshots/          one per view and screen size, for the README
  .github/workflows/      ci.yml (check.py on every push), release.yml (ZIP on a tag)
```

Rules:

- **Tokens only in `_inc/variables.xml`.** Views refer to `${...}` variables, never to literal
  colors, fonts or sizes, so an accent subset or a screen-size condition changes them in one
  place.
- **Paths relative to the theme**: `./...` in `theme.xml`, `${themePath}/...` inside views and
  item templates.
- **Every referenced file exists.** `tools/check.py` fails the build otherwise; the engine would
  only log it.
- **Original or openly licensed assets only**, each with its license next to it.

## Design tokens

Colors (hex, `RRGGBBAA` where transparency matters):

| Token | Value | Use |
|---|---|---|
| `bgTop` / `bgBottom` | `0B1A33` / `04080F` | background gradient |
| `wave` | `3B7BE0` at 10–25 % | light waves over the background |
| `surface` | `14233DE6` | panels, unselected tiles |
| `accent` | `3B8CFF` | selection glow, focus, progress |
| `textPrimary` | `FFFFFF` | titles, selected tile name |
| `textSecondary` | `A9B7CC` | details, metadata |
| `textMuted` | `6B7A90` | labels, help bar |
| `scrim` | `000000A0` | darkens game art behind text |

Type: one sans-serif family with an open license (Inter, OFL 1.1), regular and semibold. Sizes,
as a fraction of the screen height: title 0.040, tile name 0.026, body 0.021, metadata 0.019,
clock 0.021.

Layout at 16:9 (fractions of the screen):

```
0.00 ┌──────────────────────────────────────────────────────────────┐
     │ system / view name                       clock · controllers │  top bar   0.03–0.08
0.25 │  Selected title (large)                                      │
0.30 │ ┏━━━━━━━┓ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐    │  tile row  0.30–0.56
     │ ┃ sel.  ┃ │    │ │    │ │    │ │    │ │    │ │    │ │    │    │  tile 0.187 h, selected ×1.45
0.56 │ ┗━━━━━━━┛ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘    │
0.62 │ developer · year · genre · players · ★★★★☆                   │  details   0.62–0.90
     │ description, three to five lines                             │
0.94 │ (A) Play  (B) Back  (X) Options                              │  help bar  0.94–1.00
1.00 └──────────────────────────────────────────────────────────────┘
```

Motion: the selected tile scales from 1.0 to 1.45 in 200 ms (ease-out); the game art crossfades in
300 ms; the waves never move faster than the eye notices. The motion subset turns all of it off.

## Views

### System view: Home of systems

- `systemcarousel` of type horizontal across the tile row; logos 0.105×0.187, `logoScale` 1.45,
  about 8 logos shown. The selected system's name and game count (`systemInfo`) sit under the
  row.
- Background: the system's `background.jpg` darkened, else the waves.
- First milestone question: whether a horizontal carousel can keep the selection near the left
  edge, as the reference does, or whether the grid-based system view (Carbon's `grid` system
  view) is needed for that.

### Home (customView, inherits grid): the game row

- `imagegrid` named `gamegrid`, one row (`autoLayout` *n* 1, `scrollDirection` horizontal),
  `centerSelection` to be tuned so the selection stays near the left.
- `itemTemplate`: a rounded tile (`ninepatch` frame), the box art (`{game:image}`, else
  `{game:thumbnail}`), a folder tile for folders, and the game's name under the selected tile
  only. `storyboard` on `activate`/`deactivate` for the scale and the glow.
- `md_fanart` (else `md_image`) full-screen behind a `scrim`, crossfading on selection.
- Details area: `md_name`, `md_developer`, `md_releasedate`, `md_genre`, `md_players`,
  `md_rating`, `md_description` (three to five lines).
- Default view of the theme.

### Library (customView, inherits grid)

Every game at once: four or five rows of smaller tiles, vertical scrolling, the details of the
selected game in a side panel. For long lists, where one row is slow to browse.

### Detailed

The engine's list view with the same background and details area, for small screens (the 7"
panel) and for people who prefer lists.

### Screen, menu and splash

- `screen`: clock, battery and connected controllers in the top right corner, on every view.
- `menu`: EmulationStation's menus with `surface` panels, `accent` selection and the theme's font.
- `splash`: the waves with the BatoX wordmark and a progress bar in `accent`.

## Per-system artwork

`systems/<name>/`, where `<name>` is the system's `${system.theme}` (as in Batocera's
`es_systems.cfg`: `snes`, `megadrive`...):

| File | Size | Use |
|---|---|---|
| `logo.svg` | | the system tile in the system view |
| `background.jpg` | 1920×1080, under 300 KB | behind the system view and its game lists |

Systems without artwork use `systems/_default`: a typographic tile with `{system:fullName}` and
the waves. Artwork comes first for the systems on the test console (SNES, NES, Mega Drive,
GBA, Game Boy Color, MAME, FBNeo, N64, PC Engine, Master System, Game Gear, Satellaview, Sufami
Turbo).

## Options in Batocera's menu

Subsets, with names translated in `lang/`:

| Subset | Choices | Default |
|---|---|---|
| Accent color | blue, purple, teal, red, gray | blue |
| Background | waves, game art, plain | game art (falls back to waves) |
| Animations | on, off | on |
| Game view | Home, Library, Detailed | Home |

## Performance

- Backgrounds as JPEG, 1920×1080 and under 300 KB; tiles at the size they are drawn.
- No `screenshader` blur and no videos by default (the Pi 4's GPU drops frames with them in a
  full grid); a later subset may offer videos in the details area.
- `imagegrid` keeps few tiles alive: one row shows about eight.
- Animations short and on opacity, scale and position only.

## Tools and workflow

```bash
python3 tools/check.py                    # well-formed XML, includes and paths exist, sizes
python3 tools/render-background.py        # writes _inc/backgrounds/waves.png
CONSOLE=192.168.0.84 tools/deploy.sh      # copies the theme to /userdata/themes/batox-theme
tools/package.sh                          # dist/batox-theme-<version>.zip
```

On the console, choose the theme in Main menu > User interface settings > Theme set; after a
deploy, restart EmulationStation (BatoX's EmulationStation screen has the button) to load the
new files. Screenshots for the README come from `batocera-screenshot` on the console.

CI runs `check.py` on every push; a `v*` tag builds the ZIP and attaches it to a GitHub release.
The ZIP installs from BatoX's EmulationStation screen (install a theme from a ZIP) or by
unpacking it into `/userdata/themes`.

## Milestones

1. **Skeleton** (this commit): layout, tokens, tools, CI, the waves background, and minimal
   views that pass `tools/check.py`. The first look on a console belongs to milestone 2.
2. **Home row**: the system carousel and the Home game row with the selection's scale and glow,
   background art and details area; answer the left-anchored selection question.
3. **Menus, screen and splash**; English and Brazilian Portuguese.
4. **Artwork**: waves backgrounds, the default tile, logos and backgrounds for the systems on the
   test console.
5. **Library view, subsets** (accent, background, motion), small screens and 4:3.
6. **Release 1.0**: screenshots, README, ZIP from CI, installable from BatoX.

## Legal

The theme takes the layout and mood of a console home screen, not its assets: no console maker's
logos, fonts, sounds, wallpapers or names in the theme's files or views. Fonts and icons are
openly licensed (their licenses ship next to them); backgrounds are drawn by
`tools/render-background.py`. System logos are trademarks of their owners and are used to name
the systems, as every EmulationStation theme does.

## Open decisions

- **License**: CC BY-NC-SA 4.0 (the license of Batocera's Carbon theme, which would allow
  reusing its system logos with credit) or CC BY 4.0 for art and MIT for the XML and tools.
- **System logos**: draw our own wordmarks, or reuse Carbon's under its license.
- **Font**: Inter is the default proposal; Nunito Sans or Noto Sans would also fit (Noto covers
  more scripts).
