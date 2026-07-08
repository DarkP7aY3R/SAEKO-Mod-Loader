<p align="center">
  <img src="assets/banner.png" alt="SAEKO Mod Loader banner" width="100%">
</p>

<h1 align="center">SAEKO Mod Loader</h1>

<p align="center">
  An unofficial mod loader and translation helper for <strong>SAEKO: Giantess Dating Sim</strong>.
</p>

<p align="center">
  <a href="https://store.steampowered.com/app/2492120/SAEKO_Giantess_Dating_Sim/">
    <img src="https://img.shields.io/badge/Steam-SAEKO%3A%20Giantess%20Dating%20Sim-1b2838?logo=steam&logoColor=white">
  </a>
  <a href="https://saekogame.com/en/index.html">
    <img src="https://img.shields.io/badge/Official%20Site-SAEKO-7b4ab8">
  </a>
  <a href="https://safehavn.dev/">
    <img src="https://img.shields.io/badge/Developer-SAFE%20HAVN%20STUDIO-6f42c1">
  </a>
  <img src="https://img.shields.io/badge/Status-Experimental-orange">
  <img src="https://img.shields.io/badge/Platform-Windows-blue">
</p>

> [!WARNING]
> This is an unofficial fan-made project. It is not affiliated with, endorsed by, or supported by SAFE HAVN STUDIO or HYPER REAL.  
> Back up your game files before installing mods. Humanity has survived worse, but your save folder may not.

<<<<<<< HEAD
If no `translation/` folder exists, the installer only installs the DLL loader, config, EXE bootstrap, and launcher. It does not copy CSV files.
=======
---
>>>>>>> d957242 (Add GitHub banner and official links)

## ✨ Features

- Installs the SAEKO mod loader DLL.
- Supports optional translation folders.
- Does **not** require a `pl/` folder.
- Includes tools for validating translation CSV files.
- Designed to be easy to version-control on GitHub.

---

## 🔗 Official SAEKO links

| Link | Description |
|---|---|
| [Steam Store](https://store.steampowered.com/app/2492120/SAEKO_Giantess_Dating_Sim/) | Official Steam page for the game |
| [Official Website](https://saekogame.com/en/index.html) | Official SAEKO website |
| [Official X / Twitter](https://twitter.com/saekogame) | Official SAEKO social account |
| [Official Discord](https://discord.gg/3U7H7CjgxP) | Community Discord linked on the official site |
| [SAFE HAVN STUDIO](https://safehavn.dev/) | Developer blog |
| [HYPER REAL](https://hyperreal.jp/) | Publisher website |
| [HYPER REAL X / Twitter](https://twitter.com/HYPERREAL_jp) | Publisher social account |

---

## 👥 Original game credits

SAEKO: Giantess Dating Sim was developed by **SAFE HAVN STUDIO** and published by **HYPER REAL**.

| Person / Team | Role | Link |
|---|---|---|
| SAFE HAVN STUDIO | Developer | [Development blog](https://safehavn.dev/) |
| HYPER REAL | Publisher | [Official site](https://hyperreal.jp/) |
| kyp | Story, programming, music, graphics | [@_newkyp](https://twitter.com/_newkyp) |
| koh | Graphics | [@koh9083](https://twitter.com/koh9083) |
| maztani | Design | [@k_maztani](https://twitter.com/k_maztani) |

---

## 📦 Installation

1. Download or clone this repository.
2. Put the files next to the game executable, or use the included installer.
3. Run:

```bat
install.bat
```

To install the loader without copying any translation folder:

```powershell
python .\tools\install_dll_loader.py --install --dll ".\saeko_mod_loader.dll" --config ".\saeko_mod_loader.ini" --no-translation-copy
```

---

## 🗂️ Project structure

```text
<<<<<<< HEAD
translation/
=======
SAEKO_Mod_Loader/
├─ assets/
│  ├─ banner.png
│  └─ social-preview.png
├─ source/
│  └─ en/
├─ tools/
├─ install.bat
├─ uninstall.bat
├─ saeko_mod_loader.dll
├─ saeko_mod_loader.ini
└─ README.md
>>>>>>> d957242 (Add GitHub banner and official links)
```

---

## 🛠️ Development notes

Before committing changes, check what Git sees:

```powershell
git status
```

Then commit and push:

<<<<<<< HEAD
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
=======
```powershell
git add .
git commit -m "Update README and assets"
git push
>>>>>>> d957242 (Add GitHub banner and official links)
```

---

## ⚠️ Legal note

This repository is for modding and translation tooling. Do not upload copyrighted game assets, paid game files, or redistributed game content unless you have permission. Keep it clean, because GitHub is not a magical copyright laundromat.
