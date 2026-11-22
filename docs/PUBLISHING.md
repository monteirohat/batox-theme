# Publishing

How a version of the theme is released, and how a theme reaches Batocera's own list. What is
stated as fact here was read in EmulationStation's source or tried on a console; what is not
known is said so.

## Before a release

1. `python3 tools/check.py` passes.
2. Whatever a tool draws is up to date: run the `render-*` tools and confirm `git status` shows
   no change you didn't mean.
3. On a console, at 1080p: walk the home through every system, open a game list with and
   without covers and videos, open the main menu and a settings menu, and switch the accent
   color (see [STYLE.md](STYLE.md#before-a-screen-is-done)).
4. The screenshots in `docs/screenshots/` still show the theme as it is (`home.jpg`,
   `game-list.jpg`, `menu.jpg`, `loading.jpg`, and `batocera-list.jpg`, 569 x 320, the size Batocera's list
   uses). Take them with `batocera-screenshot`; an "update available" notice spoils them, and
   goes away with `batocera-settings-set updates.enabled 0` (set it back to 1 afterwards).
   The loading screen lasts under a second: restart EmulationStation and take several
   screenshots in a row, a second later.
5. `CHANGELOG.md`: move what is under "Unreleased" to a new version with today's date, and add
   its link at the bottom.

## Releasing

```bash
git tag v1.0.0
git push origin main v1.0.0
```

The Release workflow runs `tools/package.sh` and attaches `batox-theme.zip` to a GitHub release
named after the tag. The ZIP holds one folder, `batox-theme`, with only what the theme ships:
`.gitattributes` marks `docs`, `tools` and the repository's own files `export-ignore`.

Version numbers follow Semantic Versioning: a new screen or option is a minor version, a fix a
patch, and a change that breaks someone's setup (a removed option, a renamed folder) a major one.

## How Batocera lists themes

Read in EmulationStation's source (`ApiSystem.cpp`) and in the public list:

- The console's Updates & downloads > Themes screen reads
  `https://updates.batocera.org/themes.json` (the wiki also links
  `https://batocera.org/upgrades/themes.json`, with the same content). Each entry has a name, an
  author, the URL of a GitHub repository, the date of its last update, its size in megabytes and
  a screenshot kept on Batocera's server.
- To install a theme, the console downloads **the repository's default branch** as a ZIP from
  GitHub and unpacks it as `/userdata/themes/<name>`. It does not use releases or tags.

So for a listed theme:

- `main` is what people get, at any moment: it must always be a working theme. Work that isn't
  ready goes on a branch.
- `theme.xml` must be at the repository's root (it is).
- GitHub's ZIP honors `export-ignore`, so `docs` and `tools` stay out of it too.
- The folder is named after the list's entry, not the repository: ask for the name
  `batox-theme`, so installs from the list and from the release ZIP share one folder.

The entry to ask for is in [batocera-list-entry.json](batocera-list-entry.json), with its
screenshot in `screenshots/batocera-list.jpg`. The list's entries also carry an `up_to_date` number,
which Batocera's team sets; what it measures isn't documented.

### Getting listed

Batocera's wiki ([Themes](https://wiki.batocera.org/themes),
[Write themes](https://wiki.batocera.org/write_themes_for_emulationstation)) does not say how a
theme is added to the list, nor what it requires of one; the list is kept by the Batocera team.
Ask them through their community channels (the links are on <https://batocera.org>), with the
repository's URL, the entry above and the screenshot. This step has not been done yet, and the
right channel is not confirmed.

What the wiki does recommend to theme authors: keep the theme small, for weak hardware's video
memory (this one ships about 36 MB, nearly all of it the systems' pictures), and compress its images.

### Until it is listed

People install the release ZIP by hand or with BatoX (see the [README](../README.md#install)).

A console can also be pointed at another list: `global.themes.url=<URL of a themes.json>` in
`/userdata/system/batocera.conf` replaces Batocera's list with that one in the Themes screen.
It replaces the whole list, so it suits testing an entry more than everyday use.
