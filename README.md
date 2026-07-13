<p align="center">
  <img src="assets/banner.png" alt="SAEKO Mod Loader banner" width="100%">
</p>

# SAEKO Mod Loader

Universal DLL loader for SAEKO mods, custom languages, resolution unlocking, and experimental texture pack overrides.

## Warning

This is an unofficial fan-made project. It is not affiliated with, endorsed by, or supported by SAFE HAVN STUDIO or HYPER REAL.

Back up your game files before installing mods.

## Install

1. Keep this folder anywhere outside the game directory.
2. Run `install.bat`.
3. Optional: put extra mod DLL/INI files in `mods/`.
4. Start the game from Steam.

The installer tries to auto-detect the Steam install directory. If that fails, run:

```powershell
python .\tools\install_dll_loader.py --install --dll ".\saeko_mod_loader.dll" --config ".\saeko_mod_loader.ini" --mods-dir ".\mods" --texture-packs-dir ".\texture_packs" --game-dir "X:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim" --no-translation-copy
```

To install a language mod, place user-made CSV files in `translation/` or `pl/` before running `install.bat`.

## Uninstall

Run `uninstall.bat`.

## Modder Notes

- Create translation files in `translation/`, or generate templates from the in-game `Mods` popup.
- Edit `saeko_mod_loader.ini` to change language code, label, game CSV folder, fallback language, or template source language.
- Put optional external DLL mods and matching INI files in `mods/`; the installer copies them into the game's `saeko_mod_loader\mods` folder.
- `mods_enabled=false` disables the built-in language/translation mod while keeping the loader core and native `Mods` menu available.
- Extra DLL mods live in `mods/` and are toggled individually by adding/removing `.disabled`.
- The optional `saeko_resolution_unlock.dll` test mod unlocks more 16:9 and 16:10 resolutions from `mods\saeko_resolution_unlock.ini`.
- The resolution mod patches settings text, parsing, `scene.Game.Layout`, and font scaling. Its INI supports `render_mode=stretch`, `render_mode=fill`, and `render_mode=native`.
- The optional `saeko_texture_packs.dll` experimental mod can export embedded PNG files to `saeko_mod_loader\texture_packs\default` through the in-game `Generate textures` action, and can load overrides from pack folders configured in `mods\saeko_texture_packs.ini`.
- Save CSV as UTF-8 without BOM.
- Run `python .\tools\validate_translation.py --translation ".\translation"` before installing a language mod.
- Do not edit command IDs, script labels, face names, music IDs, or column counts.

## Mods Menu

The loader injects a native `Mods` option next to `Other` on the title screen. SAEKO draws both the title entry and the popup from patched UI assets, so this is not an external overlay. If external DLL mods are detected, the title label shows a count such as `Mods 2/2`.

Clicking `Mods` opens an asset-based `SAEKO Mod Loader` popup with two modder actions:

- `Generate text` creates translation CSV templates when the custom language generator is active, or opens the translation folder when there is nothing to generate.
- `Generate textures` creates or opens `saeko_mod_loader\texture_packs\default` for texture pack authors. If PNG templates already exist, the loader skips the unsafe runtime scan and only opens the folder.

The popup writes diagnostics to `saeko_mod_loader.log`, including popup patch counts, external DLL mod counts, and texture generator results.

DLL toggling is file/config based and requires a restart, so the loader does not rename DLL files while SAEKO is running.

Example external mod group:

```text
mods\ExampleMod.dll
mods\ExampleMod.ini
```

Disable a DLL by renaming it to:

```text
mods\ExampleMod.dll.disabled
```

Restart is required because DLL plugins and the Go `embed.FS` table are loaded when the process starts.

## Texture Packs

The repository includes an experimental texture pack plugin:

```text
mods\saeko_texture_packs.dll
mods\saeko_texture_packs.ini
texture_packs\README.txt
```

Use the title-screen `Mods` popup action `Generate textures` to scan the active Go `embed.FS` table and export SAEKO's embedded PNG files to:

```text
<game folder>\saeko_mod_loader\texture_packs\default
```

Create a sibling folder, copy any PNG files you want to edit, then configure priority in:

```text
<game folder>\saeko_mod_loader\mods\saeko_texture_packs.ini
```

Example:

```text
active_packs=my_pack,my_ui_pack
```

First pack wins. Missing files fall back to vanilla embedded assets. The generated `default` folder contains assets from the user's local game install and is not included in this repository or release zip.

### Real World Experiment Generator

The repository also includes:

```text
tools\create_real_world_texture_pack.py
```

After `default` exists, run:

```powershell
python -m pip install -r .\tools\requirements-texture.txt
python .\tools\create_real_world_texture_pack.py
```

It creates a local `real_world_safe_experiment` pack next to `default`. The generator keeps original file names, dimensions, alpha channels, text, outlines, and composition, then applies a conservative cleanup pass with mild smoothing, color grading, and subtle photographic grain. It intentionally avoids the aggressive material replacement that can make textures look corrupted. This is an experimental safe preview, not a hand-authored photoreal remake.

Enable it locally with:

```text
active_packs=real_world_safe_experiment
```

The generated pack includes `_AI_PROMPT_MANIFEST.tsv` with per-texture image-to-image prompts for a future real AI pass. Do not redistribute generated `default` or `real_world_safe_experiment` folders unless you have rights to the game assets used to create them.

## Linux

The repository includes an independent native Linux loader in `linux_loader/`.

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

Use the Linux loader for the native Linux Steam build. If you run the Windows build through Proton, use the Windows loader.

If `language_code` is a built-in SAEKO language such as `en`, `ja`, or `de`, the loader skips custom language injection but still patches the title version, UI row, and `Mods` menu.

## Loader Status

The language menu is patched at runtime:

- The configured language label means all expected CSV files are present.
- If any expected CSV file is missing, the language menu shows `None` and the loader blocks gameplay on the title screen.
- The popup says `Custom language is not ready` and uses SAEKO's own confirm UI/assets.
- `Exit game` closes the game.
- If the built-in template source is available, `Generate text to translate` writes missing CSV files from `template_source_language` without overwriting existing translations.
- While generating, the loader draws an `x / y files` progress message on the game window, then closes the game cleanly.
- Generated templates create `SAEKO_TRANSLATION_TEMPLATE.txt`; delete that marker only when the translation is ready to test.
- The log still records a status such as `39/40 files ready`.

The title version string uses a fixed loader-owned label:

```text
V2.1.3 modded
```

Diagnostic log:

```text
<game folder>\saeko_mod_loader.log
```

## What The Installer Changes

- Backs up `saeko_win64.exe` as `saeko_win64.original.exe`.
- Adds a tiny `.plldr` bootstrap section and imports `saeko_mod_loader.dll`.
- Copies CSV files into the configured game folder from `saeko_mod_loader.ini` only when a translation folder is provided.
- Sets SAEKO settings `Lang` to the configured language code when installing a translation, or `en` when installing only the loader/mod menu.

No game assets are packed into the EXE; translations stay as loose CSV files.
The texture pack `default` folder is generated locally from the installed game and should not be redistributed unless you have rights to those assets.
