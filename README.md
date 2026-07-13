<p align="center">
  <img src="assets/banner.png" alt="SAEKO Mod Loader banner" width="100%">
</p>

<h1 align="center">SAEKO Mod Loader</h1>

<p align="center">
  A small unofficial loader for <strong>SAEKO: Giantess Dating Sim</strong>, built for custom language packs and loose external plugins.
</p>

<p align="center">
  <a href="https://store.steampowered.com/app/2492120/SAEKO_Giantess_Dating_Sim/">
    <img src="https://img.shields.io/badge/Steam-SAEKO-1b2838?logo=steam" alt="Steam">
  </a>
  <img src="https://img.shields.io/badge/status-experimental-orange" alt="Status: experimental">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue" alt="Windows and Linux">
  <img src="https://img.shields.io/badge/license-unofficial-lightgrey" alt="Unofficial project">
</p>

---

## Warning

This is an unofficial fan-made project. It is not affiliated with, endorsed by, or supported by SAFE HAVN STUDIO or HYPER REAL.

Back up your game files before installing anything. The loader patches the game executable on Windows and restores it from a backup during uninstall.

## What It Does

- Installs a DLL loader for the Windows Steam build.
- Adds a native in-game `Mods` entry drawn with SAEKO UI assets.
- Loads custom language CSV files as a separate selectable language.
- Keeps translations as loose files outside the executable.
- Copies optional external `.dll` and `.ini` plugin files from `mods/`.
- Includes helper scripts for install, uninstall, validation, and Linux setup.

## Quick Install

1. Download or clone this repository.
2. Close SAEKO if it is running.
3. Run `install.bat`.
4. Start SAEKO from Steam.

If the installer cannot find the game, run it manually:

```powershell
python .\tools\install_dll_loader.py --install --dll ".\saeko_mod_loader.dll" --config ".\saeko_mod_loader.ini" --mods-dir ".\mods" --game-dir "X:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim" --no-translation-copy
```

## Uninstall

Run:

```bat
uninstall.bat
```

The uninstaller restores `saeko_win64.exe` from `saeko_win64.original.exe`.

## Custom Language Packs

Create a folder named `translation/` and put translated CSV files inside it. You can also use a language-specific folder such as `pl/`.

Before installing a language pack, validate the CSV structure:

```powershell
python .\tools\validate_translation.py --translation ".\translation"
```

Then edit `saeko_mod_loader.ini`:

```ini
language_code=custom
language_label=Custom
fallback_language=en
template_source_language=ja
translation_dir=saeko_mod_loader/lang
```

The loader shows the configured language label only when every expected CSV file is present. If files are missing, the in-game language menu shows `None` and the loader blocks gameplay until the pack is complete.

## External Plugins

Optional plugin files live in:

```text
mods/
```

Example layout:

```text
mods/ExamplePlugin.dll
mods/ExamplePlugin.ini
```

Disable a plugin by renaming the DLL:

```text
mods/ExamplePlugin.dll.disabled
```

Restart the game after changing plugin files. The loader does not rename loaded DLL files while SAEKO is running.

## Linux

For the native Linux Steam build, use the files in `linux/` and `linux_loader/`.

Fedora:

```bash
sudo dnf install gcc rust cargo python3
```

Linux Mint / Ubuntu:

```bash
sudo apt update
sudo apt install build-essential rustc cargo python3
```

Arch:

```bash
sudo pacman -S base-devel rust python
```

Build and install:

```bash
./linux/build_linux_loader.sh
./linux/install_linux_loader.sh
```

Steam launch option:

```text
LD_PRELOAD="/path/to/SAEKO Giantess Dating Sim/libsaeko_mod_loader.so" %command%
```

If you run the Windows build through Proton, use the Windows loader instead.

## Diagnostics

Main log:

```text
<game folder>/saeko_mod_loader.log
```

Installed files:

```text
<game folder>/saeko_mod_loader.dll
<game folder>/saeko_mod_loader.ini
<game folder>/saeko_mod_loader/
```

The title version string is patched to:

```text
V2.1.3 modded
```

## Repository Layout

```text
SAEKO-Mod-Loader/
  assets/
  docs/
  linux/
  linux_loader/
  mods/
  tools/
  install.bat
  uninstall.bat
  saeko_mod_loader.dll
  saeko_mod_loader.ini
```

## Release Safety

Do not commit or publish files generated from a local game install unless you have the rights to redistribute them. This repository is intended to ship loader files, configuration, documentation, and helper tools only.

## Official Links

- [SAEKO on Steam](https://store.steampowered.com/app/2492120/SAEKO_Giantess_Dating_Sim/)
- [Official SAEKO website](https://saekogame.com/en/index.html)
- [HYPER REAL publisher page](https://hyperreal.jp/game/saeko-giantess-dating-sim/)
