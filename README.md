# Mewgenics Sandbox Menu

A small Windows overlay for **Mewgenics** that lets you spawn any enemy, load any boss arena, paint tiles and change the weather — to build your own challenges, test synergies or just make fights messier.

It is a **sandbox, not a trainer**: there is no god mode, auto-win, kill-all, free coins, free items or stat editing. Everything it does makes a fight *harder or weirder*, not easier.

## Features

- **Enemies** — every enemy in the game (≈650), searchable, with Elite / Champion and any elite buffs (Spiky, Flaming, Mirror, …).
- **Bosses & levels** — load any boss, miniboss or house-boss arena mid-combat.
- **Tiles** — place water, lava, ice, oil, toxic sludge, brambles, glass and more.
- **Weather** — for this battle, globally, for the rest of the chapter or for the house.
- **Save snapshots** — one-click backup of your saves before experimenting, and restore later.
- English and Russian UI (follows your Windows language), names come from your own game files.
- `F8` shows / hides the window.

## How it works

Mewgenics ships with a developer console. This tool:

1. reads the list of enemies, levels, tiles and weather straight from **your installed game** (`resources.gpak`) — no game files are included in this repo;
2. offers to enable the console (adds `enable_debugconsole true` to `%APPDATA%\Glaiel Games\Mewgenics\<id>\settings.txt`, with a backup);
3. when you click **Send to game**, it focuses the game, opens the console, types the command and closes it.

Nothing is injected into the game process and no game files are modified.

## Install

1. Install [Python 3.10+](https://www.python.org/downloads/) (tick *Add to PATH*).
2. Download this repository and double-click `MewgenicsSandboxMenu.pyw` (or run `run.bat`). On first start it offers to install PySide6.
3. On first start, allow it to enable the debug console, then (re)start Mewgenics.

The Steam install is found automatically; otherwise you'll be asked for the folder containing `resources.gpak`.

If the game is set to run as administrator, the menu asks for admin rights too — Windows does not let a normal program send keys to an elevated one.

## Usage

Start a run, enter a fight, pick an enemy and press **Send to game** (or double-click). Most commands only work in combat; house weather works in the house.

## Notes and limits

- Windows only.
- Some tiles or spawns can behave oddly in arenas that were not designed for them — take a snapshot first.
- The developer console is an unofficial, unsupported feature of the game; a game update can change or remove commands.
- Save snapshots are stored in `%LOCALAPPDATA%\MewgenicsSandboxMenu\snapshots`.

## Build the exe yourself

The release exe is built with PyInstaller from this exact source:

1. Install Python 3.12.
2. Run `build.bat` (installs PySide6 + PyInstaller 6.22.3 and builds).
3. The result is `dist\MewgenicsSandboxMenu.exe`.

## Credits

- Mewgenics © Edmund McMillen & Tyler Glaiel (Glaiel Games). This project is not affiliated with or endorsed by them.
- Console command reference: the [Mewgenics Wiki](https://mewgenics.wiki.gg/wiki/Debug_Console).

## License

MIT — see [LICENSE](LICENSE).

---
