# Style

The look the home settled on, approved on the console. Every other screen (game lists, menus,
splash) follows it, so the theme reads as one piece. How the theme is built is in
[ARCHITECTURE.md](ARCHITECTURE.md); this file is what it should look like, and why.

All the values below are tokens in `_inc/variables.xml`. A view never writes a color, a size or
a font: it names a token, and a new need gets a new token there.

## The idea

A console's home screen at dusk: flat dark surfaces over a picture in saturated sunset colors,
white type, one thin white frame on what is selected. Nothing glows, nothing is rounded, nothing
casts a shadow. The picture gives the color; the interface stays quiet over it.

## Color

| Token | Value | Use |
|---|---|---|
| `homeTile` | `15122B` at 65 % | a surface at rest: tiles, plates, panels. The background shows a little through it |
| `homeTileSelected` | `2E2659` at 94 % | the selected surface: lighter, and opaque |
| `homeStrip` | `1E1940` at 94 % | a band attached to the selected surface (its number of games) |
| `selectionColor` | `F2F4F8` | the selection's frame: white, 4.5 px at 1080p |
| `textPrimary` | `FFFFFF` | names, values, what is selected |
| `textSecondary` | `A9B7CC` | labels, supporting lines, the help bar |
| `textMuted` | `6B7A90` | what is disabled or of little weight |
| `accent` | `3B8CFF` (a subset changes it) | sparingly: what a system or a game supports, the rating, activity |
| `separatorColor` | white at 19 % | the bottom bar's line |

- **Dark indigo, not blue.** Surfaces lean to the purple of the sunset pictures, so they sit in
  them instead of on them.
- **Rest is translucent, selection is solid.** Only the selected surface is opaque; that
  difference, with the frame, is what marks it. Don't mark a selection with the accent color.
- **White is for content.** Logos, names and values are white; labels are one step down.
- **The accent is rare.** One or two words on a screen, never a surface.

## Surfaces

- **Square corners**, no outlines at rest, no shadows, no glows, no gradients inside a surface.
- **5 px between surfaces** at 1080p (the gap of the home's tiles): between tiles, between a
  card and the panel under it, between two plates side by side.
- **Edges line up.** A plate starts and ends on an edge that already exists (a tile's, the
  selected card's, the screen's margin), never at a free position.
- **The selection** is the surface in `homeTileSelected` with a white frame just outside it. On
  the home it also grows 1.7 times; in a list the row keeps its size.

## Type

Inter (SIL Open Font License), three weights:

| Weight | Use | Sizes (of the screen's height) |
|---|---|---|
| Light | names and titles, large figures, the clock | title 0.052, game title 0.040, figures 0.027, clock 0.032 |
| Regular | everything else: labels, values, lists, descriptions, help | body 0.021, values 0.019, labels 0.0155, help 0.022 |
| SemiBold | a name standing for a missing logo | 0.036 in a tile |

- **Labels in capitals**, small, in `textSecondary`; **values** under them in white, in the case
  they come in. Nothing else is set in capitals, except what stands in a tile or a strip.
- **A label over its value**, 6 px apart, never beside it and never with a colon.
- **Figures are Light and larger** than text values, and come first.
- **Empty is shown**: "-" for a missing value, "0" for none. A column never collapses.
- **Long text takes two lines** before it is cut with an ellipsis.

## Layout

At 16:9, in fractions of the screen:

| What | Where |
|---|---|
| Side margin | 0.045: the top bar, the bottom bar and the first plate start there |
| Top bar | on the line at 0.065 to 0.115: controllers at the left, network and clock at the right |
| Content | from 0.19 (the home's row) or under a header |
| Bottom line | 0.875, then the help prompts at 0.895 |
| Plates | stop a little above the bottom line (0.835) |

- **Inside a plate**: 28 px at the sides, 30 to 46 px above and under, equal columns, 22 to
  36 px between rows of label and value.
- **Left is for text, right is for the picture.** Pictures are drawn dark on the left; long
  text stays there or on a plate.
- **No dead bands.** A name sits right under what it names; an empty strip between two
  elements is a layout to fix.

## Backgrounds

- **Each system has its picture** (`tools/render-system-backgrounds.py`): its machine, inked and
  lit from behind, on a pier in front of a coastal city at sunset. A game list keeps its
  system's picture, dimmed, so a system is one place.
- **The picture is never covered whole.** Surfaces are translucent or leave it room.
- **The very top stays dark** for the top bar; a soft shade sits behind a name over the sky.

## Motion

- **Moving is immediate.** The selection answers at once; a carousel slides in 250 ms.
- **What follows the selection crossfades** in 300 ms (backgrounds, names).
- **What is secondary waits.** A panel of details fades in (300 ms) after the selection has
  rested a second, and leaves with it.
- **A video waits too.** A game's cover shows first; its video takes the cover's place after
  2.5 seconds on the game.
- No bouncing, no spinning, no pulsing.

## Words

- Short, plain labels, translated in `lang/` (English and Brazilian Portuguese).
- Numbers and dates as the engine formats them for the console's language.
- No brand of the theme on the screens, and no console maker's assets: system logos are
  Batocera's, drawn in white.

## Before a screen is done

1. Only tokens: no literal color, size or font in the view.
2. Surfaces at rest translucent, the selected one solid with the white frame.
3. Every edge on an existing edge; 5 px between surfaces.
4. Labels in capitals over white values; empty values shown.
5. Readable over the brightest and the darkest of the systems' pictures.
6. Checked on the console at 1080p, moving through the screen, with long names and with games
   that have no artwork or description.
