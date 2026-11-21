# batox-theme

A modern dark EmulationStation theme for Batocera, from the BatoX project.

batox-theme takes the layout of a console's home screen: one row of large tiles, the selected
one grows, its details appear under it, and the background turns into the selected game's art.
Dark navy, soft waves of light, white type and one accent color, sized for a TV first.

> **Status: in development.** The architecture and the skeleton are in place; the views are being
> built milestone by milestone (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#milestones)).

## Install

- **With [BatoX](https://github.com/monteirohat/batox)**: download `batox-theme.zip` from the
  [latest release](https://github.com/monteirohat/batox-theme/releases) and install it from the
  EmulationStation screen.
- **By hand**: unpack the ZIP into `/userdata/themes`, so the theme is at
  `/userdata/themes/batox-theme`.

Then choose it in Main menu > User interface settings > Theme set. Requires Batocera 43 or newer.

## Options

In Main menu > User interface settings > Theme configuration:

| Option | Choices |
|---|---|
| Accent color | blue (default), purple, teal, red, gray |
| Animations | on (default), off |
| Game view | Home (one row of tiles), Library (every game at once), Detailed (a list) |

## Development

```bash
python3 tools/check.py                    # checks XML, includes, files, variables and sizes
python3 tools/render-background.py        # draws _inc/backgrounds/waves.png
CONSOLE=192.168.0.84 tools/deploy.sh      # copies the theme to a console over SSH
tools/package.sh                          # builds dist/batox-theme.zip from the last commit
```

How the theme is organized, its design tokens and its views are described in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Pushing a `v*` tag publishes a release with the
ZIP.

## Credits and trademarks

The theme's backgrounds are drawn by its own tool, and its fonts and icons are openly licensed.
It takes inspiration from console home screens but uses none of their assets, and it is not
affiliated with any console maker or with the Batocera project. System logos are trademarks of
their owners.
