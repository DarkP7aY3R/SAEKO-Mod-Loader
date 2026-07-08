# SAEKO Mod Loader

Universal DLL loader for adding a custom SAEKO translation as a separate language.

This version does **not** require a `pl/` folder to install. The loader can be installed first, and translation CSV files can be added later.

## Install without translation files

1. Keep this folder anywhere outside the game directory.
2. Run `install.bat`.
3. Start the game from Steam.

If no `translation/` folder exists, the installer only installs the DLL loader, config, EXE bootstrap, and launcher. It does not copy CSV files.

If auto-detection fails, run:

```powershell
python .	ools\install_dll_loader.py --install --dll ".\saeko_mod_loader.dll" --config ".\saeko_mod_loader.ini" --game-dir "X:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim" --no-translation-copy
```

## Install with translation files

Put your CSV translation in one of these folders:

```text
translation/
```

`install.bat` will validate and copy the first folder it finds. You can also choose a folder manually:

```powershell
python .	oolsalidate_translation.py --translation ".	ranslation"
python .	ools\install_dll_loader.py --install --dll ".\saeko_mod_loader.dll" --config ".\saeko_mod_loader.ini" --translation-dir ".	ranslation"
```

## Uninstall

Run `uninstall.bat`.

## Modder Notes

- Edit translation files in `translation/` or pass your own folder with `--translation-dir`.
- Edit `saeko_mod_loader.ini` to change language code, label, game CSV folder, fallback language, or template source language.
- Save CSV as UTF-8 without BOM.
- Run `python .	oolsalidate_translation.py --translation ".	ranslation"` before installing translated files.
- Do not edit command IDs, script labels, face names, music IDs, or column counts.

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
- Copies CSV files only when a translation folder exists or `--translation-dir` is passed.
- Sets SAEKO settings `Lang` to the configured language code.

No game assets are packed into the EXE; translations stay as loose CSV files.
