# Architecture

batox-theme is a dark EmulationStation theme for Batocera in the style of a modern console's home
screen: one row of square tiles with the systems' logos, the selected one grows into a card with
its details, over a picture of the system at sunset; inside a system, a list of games at the
left and the selected game's cover and details at the right.

How it should look, and why, is in [STYLE.md](STYLE.md): read it before changing a screen.

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

- **A console home screen.** A single row of square tiles; the selected one is larger, in a thin
  white frame, with its name next to it and its figures under it.
- **A list to find a game.** Inside a system, the games in a list at the left; at the right the
  selected game's cover, name, details and description.
- **Dark and calm.** Flat dark surfaces over the system's picture, white type, one accent color
  (see [STYLE.md](STYLE.md)).
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
- `<imagegrid>` with `autoLayout`, `scrollDirection`, `centerSelection`, `scrollLoop` and an
  `<itemTemplate>` of `container`/`image`/`text`/`ninepatch`, with `storyboard` animations on
  `activate`/`deactivate`;
- the system view's `<carousel name="systemcarousel">` with an `<itemTemplate>`, like the game
  grid's;
- data bindings in `itemTemplate` and paths: `{game:image}`, `{game:thumbnail}`,
  `{game:name}`, `{system:theme}`, `{system:fullName}`, and `exists()`, `firstfile()` and `?:`
  expressions;
- `${system.fullName}`, `${system.manufacturer}` and `${system.releaseYearOrNull}` in the system
  view's own elements;
- metadata elements `md_description`, `md_developer`, `md_genre`, `md_releasedate`, `md_players`,
  `md_rating`, `md_name`, `md_image`, `md_fanart`;
- `<subset>` with `displayName`, `appliesTo` and `ifSubset`, shown in Batocera's theme menu;
- `<include lang="...">` for translated names;
- `${themePath}` and `${system.theme}` in paths.

### Engine notes

Learned on the console (Batocera 43.1); each one cost a round of screenshots:

- **No function inside another.** `firstfile(a, firstfile(b, c))` and `exists(firstfile(...))`
  give nothing. Write one flat `firstfile(a, b, c)`, and test `exists()` on a plain path.
- **No lookups in `<visible>`.** An item-template element whose `<visible>` holds
  `exists(firstfile(...))` is never shown. Make the choice in the `<path>` instead
  (`firstfile(console, logo)`, `exists(x) ? y : ""`).
- **No game bindings in a view's own elements' `<visible>`** (an extra image with
  `exists({game:fanart})` never showed). To darken the game art, tint `md_fanart` itself with
  `<color>` (it multiplies the picture).
- **Grid or carousel for the systems.** With a grid, the system view's own elements (background,
  texts) stay those of the system selected when the view opened. A carousel gives every system
  its own copy of them, so they follow the selection, and it takes the same `<itemTemplate>`.
- **A grid clips its items.** A selected tile that grows past the grid's edges is cut: the
  grid's `<padding>` (in screen fractions) leaves it room.
- **Selection on the left.** A carousel (or a grid with `centerSelection` true) keeps the
  selection at its center, so one much wider than the screen that starts off-screen puts that
  center near the left edge.
- **A scaled ninepatch blurs.** A frame drawn as a ninepatch inside a tile that the carousel
  scales up turns into a soft haze; four thin images (top, bottom, sides) stay crisp.
- **The carousel can push its neighbors.** `scaledLogoSpacing` 1 moves the tiles next to the
  selected one so it doesn't cover them, and `logoAlignment` top keeps every tile's top on the
  row, so the selected one grows down and to the right.
- **`systemInfoDelay`** (the carousel's) is how long the engine waits before showing
  `systemInfo`, its own line of games. The home hides that line and shows `{system:total}` in
  the selected tile's strip instead, which has no delay.
- **No date.** Themes get no current date: `{global:clock}` is the "show clock" setting ("YES"),
  the `<clock>` element shows the time only (`%H:%M`, or `%I:%M %p` with the 12-hour option)
  and ignores `<format>`, and the date format in the engine is the screensaver's.
- **The `screen` view draws the engine's elements only** (`clock`, `batteryIndicator`,
  `controllerActivity`...): extra texts don't show there.
- **`batteryIndicator` ignores `<origin>`**: its box starts at `<pos>` and its icons (the
  network's, and the battery's on a handheld) sit at the box's right.
- **Elements outside a carousel item** (the strip under the selected tile) are drawn, not cut.
- **Moving around for screenshots**: a virtual keyboard through `/dev/uinput` presses the arrows
  on the console; EmulationStation takes it like a real one.
- **Several `<path>` lines**: the last one whose file exists is used.
- **An element only when a file exists**: `if="exists(${themePath} + '/x/' + ${system.theme} +
  '/y.jpg')"` on an element, with the variables outside the quotes. Declared a second time under
  the same name, an element takes the new values: this is how a system with a background of the
  theme's own drops the tint its photo would get.
- **Element names are case sensitive**: `<webimage>` draws, `<webImage>` is skipped with only a
  warning in the log. `tools/check.py` checks every view's elements against the engine's list.
- **`controllerActivity` gives each device a square** as tall as its box and centers the image
  on it: a wider image spills over its neighbor, so the device icons are square with the drawing
  in the middle. `itemSpacing` is a fraction of the screen's width.
- **A shader on an image**: `<shader><path>file.glsl</path>...</shader>` inside an `<image>` runs
  the theme's own GLSL on it; a child named `<x_binding>` sets the shader's uniform `x` from an
  expression, per item of a carousel. This is how the logos turn white.
- **A list of systems in an expression**: `contains(" ${list} ", " " + {system:theme} + " ")`,
  the list being a variable of names separated by spaces. It works in a `<path>`, a `<visible>`,
  an `<opacity>` and a shader's `_binding`, and a condition may sit in another's "else"
  (`a ? 1 : b ? 2 : 3`).
- **Keys belong to the engine.** A theme can't react to a key or add a second place to move
  to: on the system view, left and right change the system, and down and up jump to the next
  group of systems when Batocera's "Quick system select" is on, else do nothing.
- **A delayed element on the system view.** Each system has its own copy of the view's
  elements, and an element's `<storyboard>` (with no event) starts over when its system is
  selected: an `opacity` animation with `begin="1000"` shows it after a second of rest.
  `begin` and `duration` take plain numbers; a `${variable}` there counts as 0.
- **System figures**: `{system:favorites}`, `{system:gamesPlayed}`, `{system:gameTime}`,
  `{system:lastPlayedDate}`, `{system:mostPlayed}`, `{system:isCheevosSupported}` and
  `{system:isNetplaySupported}` work in the system view's texts. A text shows "None" for 0:
  `{system:favorites} > 0 ? {system:favorites} : "0"` shows the number.
- **A list's rows**: `<lines>` on a `textlist` sets how many rows fit its height, whatever the
  font. `selectorImagePath` is stretched over the selected row (keep `selectorColor` white, it
  multiplies the image).
- **Game details**: an `md_` element the theme doesn't declare isn't drawn; several names in
  one `name="a, b, c"` share a declaration (`<visible>false</visible>` hides the engine's
  `md_lbl_*`).
- **A cover that becomes a video**: one `md_video` with `snapshotSource` thumbnail,
  `showSnapshotNoVideo` and `showSnapshotDelay` true shows the box of every game (the engine
  falls back to the game's picture), `defaultSnapshot` when there is none, and plays the video
  after `delay` seconds. The sound follows Batocera's own option.
- **A shader's `_binding` without a binding** is still evaluated: with static variables only
  (`" ${system.theme} "`), it picks a value per system in a game view.
- **RetroAchievements**: `${global.cheevos}` is set when an account is configured in Batocera,
  `${global.cheevos.username}` is its name; a `webimage` loads the avatar from
  `media.retroachievements.org` and keeps it in `~/.emulationstation/tmp`.

## Repository layout

```
batox-theme/
  theme.xml               entry point: includes, languages, subsets, views
  _inc/
    variables.xml         design tokens: the only place colors, sizes and fonts are set
    backgrounds/          generated backgrounds (tools/render-background.py)
    frames/               white.png and the list's selector (tools/render-frames.py)
    fonts/                Inter Light, Regular and SemiBold, and their license (OFL 1.1)
    icons/                the top bar's controller, gun and wheel; the tile for a missing cover
    shaders/              white.glsl: draws the systems' logos in white
  views/
    screen.xml            always on top: controllers, network and battery, clock
    splash.xml            loading screen (milestone 3)
    menu.xml              EmulationStation's menus, dark and rounded (milestone 3)
    system.xml            Home of systems: the row of system tiles
    common.xml            the game lists: the system's picture and logo, the list, the bottom bar
    detailed.xml          the selected game's cover, name, details and description
  subsets/
    accent/               accent colors: blue (default), purple, teal, red, gray
    motion/               animations on (default) or off
  systems/
    README.md             the artwork convention
    <system>/             the system's background, named by ${system.theme}
  lang/                   en.xml (always included), pt_BR.xml, more later
  tools/
    check.py              validates the theme (XML, includes, paths, elements, sizes)
    render-background.py  draws the wave backgrounds, in pure Python
    render-system-backgrounds.py  draws the systems' backgrounds (needs Chrome or Chromium)
    render-frames.py      draws white.png and the list's selector, in pure Python
    render-icons.py       draws the top bar's icons and the missing cover's tile, in pure Python
    preview-logos.py      shows every system logo as the home draws it, to pick its treatment
    deploy.sh             copies the theme to a console over SSH
    package.sh            builds the release ZIP
  docs/
    ARCHITECTURE.md       this file
    STYLE.md              how every screen should look
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
| `surface` / `tileSurface` | `14233DE6` / `1A2B48` | panels / game tiles |
| `homeTile` / `homeTileSelected` / `homeStrip` | `15122B` (65 %) / `2E2659` / `1E1940` (94 %) | the home's tiles: dark indigo, after the sunset backgrounds; the unselected ones let the background show through |
| `selectionColor` | `F2F4F8` | the selection frame: white, like a console home's |
| `accent` | `3B8CFF` | rating, focus |
| `textPrimary` | `FFFFFF` | titles, the brand |
| `textSecondary` | `A9B7CC` | details, metadata |
| `textMuted` | `6B7A90` | labels, help bar |
| `artTint` | `4A4A4A` | multiplies the system and game art behind the text: darker |

Type: Inter (OFL 1.1), light, regular and semibold. Sizes, as a fraction of the screen height:
the home's title 0.052 (light), game title 0.040, body 0.021, metadata 0.019, clock 0.032
(light), help bar 0.022.

The home at 16:9 (fractions of the screen), measured on a console's home screen:

```
0.00 ┌──────────────────────────────────────────────────────────────┐
0.07 │ ▭ ▭        ▣ Name                                wifi  13:49 │  top bar
0.19 │┌───┐┏━━━━━━━━━┓┌───┐┌───┐┌───┐┌───┐┌───┐┌───┐┌───┐┌───┐┌───┐ │  square tiles of 202 px,
     ││ ▣ │┃         ┃│ ▣ ││ ▣ ││ ▣ ││ ▣ ││ ▣ ││ ▣ ││ ▣ ││ ▣ ││ ▣ │ │  5 px apart, white logos
0.38 │└───┘┃  logo   ┃└───┘└───┘└───┘└───┘└───┘└───┘└───┘└───┘└───┘ │
0.44 │     ┃         ┃ Final Burn Neo                                │  the selection, in the
0.49 │     ┃─────────┃ Arcade   2019                                │  second place: 1.7 times
0.59 │     ┗918 GAMES┛                                              │  larger, a strip with its
0.62 │     ┌ favorites   played       play time ┐                   │  games, a white frame;
0.84 │     └ last played most played  features  ┘                   │  under it, the panel,
     │                                        the system's picture  │  after a second of rest
0.88 │ ──────────────────────────────────────────────────────────── │  separator
0.90 │ (start) MENU  (Y) SEARCH  (X) RANDOM  (B) SELECT             │  help bar
1.00 └──────────────────────────────────────────────────────────────┘
     behind: the selected system's picture (its machine on a pier at sunset); else Carbon's
     photo, tinted by artTint; else the waves
```

Motion: the selected tile grows 1.7 times, lightens, and its strip and frame fade in, in 200 ms
(ease-out); the background and texts crossfade in 300 ms. The motion subset turns it off.

### Decided

Approved on the console, and kept unless asked:

- **The light font**: Inter Light for the home's title (0.052) and the clock (0.032).
- **The bottom bar**: a thin line at 0.875 of the screen's height (`separatorY`, white at 19 %),
  the help prompts under it at 0.895 (`helpY`), both from 0.045 (`homeMarginX`), in Inter
  Regular 0.022 and `textSecondary`.
- **No brand on the home**, and no date (it isn't possible, see [Engine notes](#engine-notes)).
- **The top bar's left**: the connected controllers (lightguns and wheels too) from 0.045, white,
  lit in `accent` while in use, on every view; on the home, the RetroAchievements profile (avatar
  and name, Inter Light 0.027) at 0.18, after room for four controllers, only when an account is
  configured. Nothing comes from outside Batocera.
- **The top bar's right**: the network icon (and the battery on a handheld) just left of the
  clock, on its line.

## Views

### System view: the home (done)

- `systemcarousel` of type horizontal with an `itemTemplate`: 15 tiles across a carousel 1.6125
  screens wide that starts at x = -0.5678, so the selection always sits in the second place
  (see [Engine notes](#engine-notes)); square tiles of 202 px at 1080p, 5 px apart;
  `scaledLogoSpacing` pushes the neighbors of the selected tile, `logoAlignment` top keeps the
  row's top.
- A tile: a square of `homeTile` with the system's brand logo in white (see
  [Per-system artwork](#per-system-artwork)), else its name. The selected one grows 1.7 times
  into a card: lighter
  (`homeTileSelected`), a `homeStrip` strip with its number of games under it, and a white frame of four
  thin bars.
- At the card's right: the system's name (light, 0.052), and its maker and year. The engine's
  own line of games (`systemInfo`) is hidden: the number is in the strip.
- The name sits right under the row of tiles, so no empty band is left there, and the picture
  of the machine stays clear below.
- Under the selected card, from its left edge, the system's panel, like the one a console home
  opens when you move down from a tile: two rows of a label over its value, in three equal
  columns. Favorites, games played and play time; under them the last day played, the most
  played game and the features the system supports, RetroAchievements and Netplay. The second row's values take two lines when they are long. The plate has an unselected tile's
  color and transparency, sits the tiles' gap under the card, ends at the right edge of the
  second tile after it and stops a little above the bottom bar's line (0.835 of 0.875). A theme can't react to the down key (see [Engine notes](#engine-notes)), so the panel
  fades in by itself once the selection has rested a second on a system, and leaves with it.
- The background, name, maker and year follow the selection, crossfading in 300 ms; the waves,
  the separator and the help bar stay.
- Background: the system's picture, drawn by the theme (see
  [Per-system artwork](#per-system-artwork)); a system without one gets Carbon's photo tinted by
  `artTint`, else the waves.

### Game list (the `detailed` view, the theme's default)

The home's style ([STYLE.md](STYLE.md)) on a list: two plates of an unselected tile's color and
transparency, 5 px apart, from the home's row top (0.208) to a little above the bottom line.

```
0.07 │ ▭ ▭                                               wifi  13:49 │  top bar
0.16 │ SUPER NINTENDO (logo, white)                                  │  header
0.21 │┌──────────────────────┐┌─────────────────────────────────────┐│
     ││ Game                 ││ ┌───────┐  Name of the game         ││  list: twelve rows, the
     ││┏━━━━━━━━━━━━━━━━━━━━┓││ │ cover │  DEVELOPER   PUBLISHER    ││  selected one solid, in
     ││┃ Selected game      ┃││ │       │  GENRE       PLAYERS      ││  a white frame
     ││┗━━━━━━━━━━━━━━━━━━━━┛││ │       │  RELEASED    RATING       ││
     ││ Game                 ││ └───────┘  LAST PLAYED TIMES PLAYED ││  details: cover, name,
     ││ Game                 ││ Description of the game, on several ││  four rows of labels
0.83 │└──────────────────────┘└─ lines, scrolling by itself ────────┘│  over values, description
0.88 │ ──────────────────────────────────────────────────────────── │
0.90 │ (select) OPTIONS  (start) MENU  (A) BACK ...                 │  help bar
     behind: the system's picture, dimmed by listArtTint
```

- **`views/common.xml`** (`basic`, `detailed`, `video`): the system's picture as on the home,
  dimmed; the system's logo in white as the header (the same shader and lists as the tiles,
  else the system's name); the list's plate from the screen's margin, 0.36 wide; the
  `textlist` with `lines` 12, the selected row drawn by `selector.png`; the bottom bar.
- **`views/detailed.xml`** (`detailed`, `video`): the details' plate to the right margin; the
  cover (the game's box, whole in a 0.19 x 0.345 area; its picture when it has no box; else
  `no-cover.svg`), which gives way to the game's video, in the same place and as wide, after
  2.5 seconds on a game that has one (`md_video` with its snapshot); the
  name in Inter Light, on two lines if long; developer, publisher, genre, players, year, rating,
  last time played and times played as labels over values in two columns; the description.
- The engine's own labels (`md_lbl_*`) end with a colon and are hidden; the theme's are in
  `lang/`. The engine writes "Unknown" and "never" for what a game lacks.
- Not shown: the game's marquee and fanart; its screenshot only when it stands for a missing box. Other gamelist styles (grid,
  carousel) are not themed.

### Screen, menu and splash

- `screen`, on every view: the connected controllers at the top left; the network icon (and the
  battery on a handheld) and the clock at the top right.
- `menu` (to do): EmulationStation's menus in the home's style ([STYLE.md](STYLE.md)).
- `splash` (to do): the loading screen.

## Per-system artwork

`systems/<name>/`, where `<name>` is the system's `${system.theme}` (as in Batocera's
`es_systems.cfg`: `snes`, `megadrive`...; `auto-allgames`, `auto-favorites` and
`auto-lastplayed` for the automatic collections):

| File | Size | Use |
|---|---|---|
| `background.jpg` | 1920×1080, under 300 KB | behind the home when the system is selected |

The logos are those of Carbon, the theme every Batocera has, read in place from
`/usr/share/emulationstation/themes/es-theme-carbon/art` and never copied. The backgrounds are
the theme's own for the systems drawn so far, Carbon's for the others.

**Logos.** A tile shows `logos/<name>.svg` (else `.png`), 462 systems, drawn in white by
`_inc/shaders/white.glsl`: every visible pixel of the colored logo turns white, which keeps its
shape. Three lists in `_inc/variables.xml` handle the logos this doesn't suit:

| List | For | What happens |
|---|---|---|
| `logoCutDark` | a logo on a black or dark plate (Mega Drive, Game Boy Advance, MSX) | pixels under 25 % of brightness disappear, so the letters show |
| `logoCutGray` | a logo on a gray or colored plate (Commodore 64, Atari) | the same, under 45 % |
| `logoAsName` | a logo neither suits (All games) | the system's name, in capitals |

A system without a logo shows its name too. `tools/preview-logos.py` draws every logo as the
home does, next to the other treatments, from a copy of Carbon's logos: the systems of the test
console and the logos that whiten into a plain rectangle are sorted; the rest of the 462 are
still to review there.

**Backgrounds.** `tools/render-system-backgrounds.py` draws one picture per system, 25 so far
(the test console's): the machine, inked and lit from behind, on a pier in front of a coastal
city at sunset, with palms, in saturated pinks, oranges and purples over the theme's navy. The
left stays dark for the texts and the very top for the top bar, the sky keeps its color behind
the row of tiles, which are translucent, and a soft shade sits behind the system's name. Four moods of sky (`vice`, `miami`, `gold`, `night`) vary the row.

- A machine is a few boxes (a body, its raised parts, a cartridge, a controller) with details
  drawn flat on their faces, all seen from the same corner; consoles, handhelds, arcade
  cabinets, home computers, and for the collections a pile of cartridges and neon signs. A new
  system is one function and one line in `SYSTEMS`.
- The script writes an SVG and a headless Chrome or Chromium turns it into the JPEG (about
  90 KB each). Everything is drawn there: no photo, no logo, no art from a game or a maker.
- A system without its own picture uses Carbon's photo (`art/background/<name>.jpg`, 323
  systems), read in place, never copied, and tinted by `artTint`; else the waves.

## Options in Batocera's menu

Subsets, with names translated in `lang/`:

| Subset | Choices | Default |
|---|---|---|
| Accent color | blue, purple, teal, red, gray | blue |
| Animations | on, off | on |

## Performance

- Backgrounds as JPEG, 1920×1080 and under 300 KB; tiles at the size they are drawn.
- No `screenshader` blur and no videos by default (the Pi 4's GPU drops frames with them in a
  full grid); a later subset may offer videos in the details area.
- `imagegrid` keeps few tiles alive: one row shows about eight.
- Animations short and on opacity, scale and position only.

## Tools and workflow

```bash
python3 tools/check.py                    # well-formed XML, includes and paths exist, elements, sizes
python3 tools/render-background.py        # writes _inc/backgrounds/waves.png
python3 tools/render-system-backgrounds.py  # writes systems/*/background.jpg (needs Chrome)
CONSOLE=192.168.0.84 tools/deploy.sh      # copies the theme to /userdata/themes/batox-theme
python3 tools/render-frames.py            # writes _inc/frames/white.png and selector.png
python3 tools/render-icons.py             # writes _inc/icons/*.svg
python3 tools/preview-logos.py /tmp/logos # writes dist/logos.html from a copy of Carbon's logos
tools/package.sh                          # dist/batox-theme.zip
```

On the console, choose the theme in Main menu > User interface settings > Theme set; after a
deploy, restart EmulationStation (BatoX's EmulationStation screen has the button) to load the
new files. Screenshots for the README come from `batocera-screenshot` on the console.

CI runs `check.py` on every push; a `v*` tag builds the ZIP and attaches it to a GitHub release.
The ZIP installs from BatoX's EmulationStation screen (install a theme from a ZIP) or by
unpacking it into `/userdata/themes`.

## Milestones

1. **Skeleton** (done): layout, tokens, tools, CI, the waves background, and minimal views.
2. **Home** (done): the system row with the selection on the left, console and logo tiles, the
   glow, the system's art as background, the brand, the help bar; then, after a console's home
   screen, square tiles 5 px apart with the systems' logos in white and the selected card with a white
   frame.
3. **Game list** (first version done): the list at the left, the selected game's cover and
   details at the right, in the home's style.
4. **Menus and splash**, in the same style; English and Brazilian Portuguese.
5. **Artwork**: a background for each of Batocera's other systems; the logos still to review.
6. **Subsets** (accent, motion), small screens and 4:3.
7. **Release 1.0**: screenshots, README, ZIP from CI, installable from BatoX.

## Legal

The theme takes the layout and mood of a console home screen, not its assets: no console maker's
logos, fonts, sounds, wallpapers or names in the theme's files or views. Fonts and icons are
openly licensed (their licenses ship next to them); backgrounds are drawn by
`tools/render-background.py` and `tools/render-system-backgrounds.py`, whose machines are the
theme's own drawings, without logos or names. System logos are trademarks of their owners and are used to name
the systems, as every EmulationStation theme does.

The top bar's icons are the theme's own (`tools/render-icons.py`). The system logos, and the
backgrounds of the systems the theme hasn't drawn yet, come from Batocera's Carbon theme (CC
BY-NC-SA, by Fabrice Caruso and its contributors), read from where Batocera installs it; this
theme ships none of them, and only changes the logos' color as it draws them. The RetroAchievements avatar is
loaded from retroachievements.org on the console, only for an account the user configured.

License: MIT (`LICENSE`) for everything the theme ships, except the Inter font, which keeps its
own license (SIL Open Font License 1.1, `_inc/fonts/Inter-LICENSE.txt`).

## Open decisions

- **More system backgrounds**: 25 systems have their own picture; each of Batocera's other
  systems needs its machine drawn in `tools/render-system-backgrounds.py`.
- **Font**: Inter is the default proposal; Nunito Sans or Noto Sans would also fit (Noto covers
  more scripts).
