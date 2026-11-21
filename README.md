# batox-theme

A modern dark EmulationStation theme for Batocera, from the BatoX project.

batox-theme takes the layout of a console's home screen: one row of square tiles with the
systems' logos, the selected one grows into a card with its details, over a picture of the
system at sunset. Inside a system, the games are a list at the left, with the selected game's
cover and details at the right. Flat dark surfaces, white type and one accent color, sized for
a TV first. The top
bar shows the connected controllers, your RetroAchievements profile when you have an account set
up in Batocera, the network and the clock.

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

## Development

```bash
python3 tools/check.py                    # checks XML, includes, files, elements, variables, sizes
python3 tools/render-background.py        # draws _inc/backgrounds/waves.png
python3 tools/render-system-backgrounds.py  # draws systems/*/background.jpg (needs Chrome)
CONSOLE=192.168.0.84 tools/deploy.sh      # copies the theme to a console over SSH
tools/package.sh                          # builds dist/batox-theme.zip from the last commit
```

How the theme is organized, its design tokens and its views are described in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); how every screen should look, in
[docs/STYLE.md](docs/STYLE.md). Pushing a `v*` tag publishes a release with the
ZIP.

## Credits and trademarks

The theme's backgrounds are drawn by its own tools, the systems' ones included (each machine on
a pier at sunset), its font (Inter, SIL Open Font License) is openly licensed, and its icons are
its own. The system logos, and the backgrounds of the systems not drawn yet, are those of
Batocera's default theme, Carbon (CC BY-NC-SA, by Fabrice Caruso and its contributors), read where
Batocera installs it; this theme doesn't ship them, and draws the logos in white. It takes inspiration from console home screens but uses
none of their assets, and it is not affiliated with any console maker or with the Batocera
project. System logos are trademarks of their owners.

## License

[MIT](LICENSE), except the Inter font, which keeps its own license (SIL Open Font License 1.1,
[_inc/fonts/Inter-LICENSE.txt](_inc/fonts/Inter-LICENSE.txt)).
