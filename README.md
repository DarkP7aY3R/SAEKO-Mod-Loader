<p align="center">
  <img src="assets/banner.png" alt="SAEKO Mod Loader banner" width="100%">
</p>

<h1 align="center">SAEKO Mod Loader</h1>

<p align="center">
  <strong>A small unofficial loader for SAEKO: Giantess Dating Sim</strong><br>
  Custom language packs, loose external plugins, Windows loader support, and experimental Linux tooling.
</p>

<p align="center">
  <a href="https://store.steampowered.com/app/2492120/SAEKO_Giantess_Dating_Sim/">
    <img src="https://img.shields.io/badge/Steam-SAEKO-1b2838?logo=steam&logoColor=white" alt="Steam">
  </a>
  <a href="https://saekogame.com/en/index.html">
    <img src="https://img.shields.io/badge/Official%20Site-SAEKO-8b5cf6" alt="Official site">
  </a>
  <a href="https://hyperreal.jp/game/saeko-giantess-dating-sim/">
    <img src="https://img.shields.io/badge/Publisher-HYPER%20REAL-ff69b4" alt="HYPER REAL">
  </a>
  <img src="https://img.shields.io/badge/status-experimental-orange" alt="Status: experimental">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue" alt="Windows and Linux">
  <img src="https://img.shields.io/badge/project-unofficial-lightgrey" alt="Unofficial project">
</p>

<p align="center">
  <a href="#-what-it-does">Features</a>
  ·
  <a href="#-quick-install">Install</a>
  ·
  <a href="#-updating-the-loader">Update</a>
  ·
  <a href="#-uninstall">Uninstall</a>
  ·
  <a href="#-external-plugins">Plugins</a>
  ·
  <a href="#-custom-language-packs">Language Packs</a>
  ·
  <a href="#-linux">Linux</a>
  ·
  <a href="#-official-links">Official Links</a>
</p>

---

## ⚠️ Warning

> [!WARNING]
> This is an **unofficial fan-made project**.  
> It is not affiliated with, endorsed by, or supported by **SAFE HAVN STUDIO** or **HYPER REAL**.

> [!IMPORTANT]
> Back up your game files before installing anything.  
> The Windows loader patches the game executable and restores it from a backup during uninstall.

---

## ✨ What It Does

**SAEKO Mod Loader** is a lightweight modding helper for installing external loader files, custom language packs, and optional loose plugin DLLs.

| Feature | Status |
|---|---|
| Windows Steam build DLL loader | ✅ Supported |
| Native in-game `Mods` entry | ✅ Supported |
| Loose custom language CSV files | ✅ Supported |
| Optional external `.dll` / `.ini` plugins | ✅ Supported |
| Native Linux loader files | 🧪 Experimental |
| Proton Windows build support | ✅ Use Windows loader |

### Core features

- Installs a DLL loader for the Windows Steam build.
- Adds a native in-game `Mods` entry drawn with SAEKO UI assets.
- Loads custom language CSV files as a separate selectable language.
- Keeps translations as loose files outside the executable.
- Copies optional external `.dll` and `.ini` plugin files from `mods/`.
- Includes helper scripts for install, uninstall, validation, and Linux setup.

---

## 📦 Quick Install

1. Download or clone this repository.
2. Close **SAEKO** if it is running.
3. Run:

```bat
install.bat
```

4. Start **SAEKO** from Steam.

If the installer cannot find the game, run it manually:

```powershell
python .\tools\install_dll_loader.py --install --dll ".\saeko_mod_loader.dll" --config ".\saeko_mod_loader.ini" --mods-dir ".\mods" --game-dir "X:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim" --no-translation-copy
```

> [!NOTE]
> Replace `X:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim` with your real SAEKO installation path.

---

## 🔄 Updating the Loader

To update an existing installation:

1. Close **SAEKO**.
2. Download the newest loader release.
3. Extract it somewhere safe.
4. Run:

```bat
install.bat
```

The installer updates the loader files in the game folder.

> [!TIP]
> You usually do not need to uninstall first.  
> If something behaves strangely after updating, do a clean reinstall.

### Clean reinstall

Use this when:

- the game fails to start,
- the loader menu does not appear,
- plugin behavior gets weird,
- language packs show `None`,
- the game was updated by Steam and the loader no longer works.

Steps:

1. Close **SAEKO**.
2. Run:

```bat
uninstall.bat
```

3. Open the game folder and check that these files are gone:

```text
saeko_mod_loader.dll
saeko_mod_loader.ini
saeko_mod_loader/
saeko_mod_loader.log
```

4. Run:

```bat
install.bat
```

5. Start the game from Steam.

---

## 🧹 Uninstall

Run:

```bat
uninstall.bat
```

The uninstaller tries to restore the original game executable:

```text
saeko_win64.exe
```

from the backup created during installation:

```text
saeko_win64.original.exe
```

It also removes installed loader files from the game folder.

> [!IMPORTANT]
> Do not delete `saeko_win64.original.exe` if you still want the uninstaller to restore the original executable.

### What uninstall removes

The uninstaller removes loader-related files such as:

```text
<game folder>/saeko_mod_loader.dll
<game folder>/saeko_mod_loader.ini
<game folder>/saeko_mod_loader/
<game folder>/saeko_mod_loader.log
```

### What uninstall restores

If the backup exists, the uninstaller restores:

```text
<game folder>/saeko_win64.exe
```

from:

```text
<game folder>/saeko_win64.original.exe
```

### What uninstall does not remove

The uninstaller does not intentionally remove:

```text
Steam files
save files
Steam Cloud data
screenshots
your downloaded release ZIP files
```

> [!NOTE]
> Save files are not part of the loader installation.  
> Still, backing up your saves before modding is a good survival instinct, unlike trusting a patched executable with your emotional wellbeing.

---

## 🧯 Manual Cleanup

Use this only if `uninstall.bat` fails.

1. Close **SAEKO**.
2. Open the game folder.
3. Delete these loader files:

```text
saeko_mod_loader.dll
saeko_mod_loader.ini
saeko_mod_loader/
saeko_mod_loader.log
```

4. If this file exists:

```text
saeko_win64.original.exe
```

rename or copy it back to:

```text
saeko_win64.exe
```

> [!CAUTION]
> Only restore `saeko_win64.original.exe` if it came from your own local game installation.  
> Do not download game executables from strangers on the internet. That is not modding. That is volunteering to be malware’s roommate.

### Last resort: verify game files through Steam

If the original executable backup is missing or the game still does not start, verify the game files through Steam:

```text
Steam Library → SAEKO → Properties → Installed Files → Verify integrity of game files
```

This can redownload missing or broken game files.

---

## 🌐 Custom Language Packs

Custom language packs are optional.

Create a folder named:

```text
translation/
```

and put translated CSV files inside it.

You can also use a language-specific folder such as:

```text
pl/
```

Before installing a language pack, validate the CSV structure:

```powershell
python .\tools\validate_translation.py --translation ".\translation"
```

Then edit:

```text
saeko_mod_loader.ini
```

Example:

```ini
language_code=custom
language_label=Custom
fallback_language=en
template_source_language=ja
translation_dir=saeko_mod_loader/lang
```

The loader shows the configured language label only when every expected CSV file is present.

If files are missing, the in-game language menu shows:

```text
None
```

and the loader blocks gameplay until the pack is complete.

---

## 🌐 Removing a Language Pack

To remove an installed custom language pack:

1. Close **SAEKO**.
2. Open the game folder.
3. Delete the installed language folder:

```text
<game folder>/saeko_mod_loader/lang/
```

4. Edit:

```text
saeko_mod_loader.ini
```

and set the language settings back to your preferred defaults.

Example:

```ini
language_code=custom
language_label=Custom
fallback_language=en
template_source_language=ja
translation_dir=saeko_mod_loader/lang
```

If the custom language is incomplete, the loader may show:

```text
None
```

in the in-game language menu until the missing files are fixed or the pack is removed.

---

## 🔌 External Plugins

Optional plugin files live in:

```text
mods/
```

Example layout:

```text
mods/
├─ ExamplePlugin.dll
└─ ExamplePlugin.ini
```

Disable a plugin before install by renaming the DLL:

```text
mods/ExamplePlugin.dll.disabled
```

Restart the game after changing plugin files.

> [!NOTE]
> The loader does not rename loaded DLL files while SAEKO is running.  
> Close the game first, because Windows file locking exists to test everyone’s patience.

---

## 🔌 Removing External Plugins

External plugin files are installed from:

```text
mods/
```

and copied into the game loader folder.

To disable a plugin before installing:

```text
mods/ExamplePlugin.dll.disabled
```

To remove a plugin from an installed game:

1. Close **SAEKO**.
2. Open:

```text
<game folder>/saeko_mod_loader/mods/
```

3. Delete the plugin files:

```text
ExamplePlugin.dll
ExamplePlugin.ini
```

4. Start the game again.

> [!NOTE]
> Always close the game before deleting plugin DLL files.  
> Windows loves locking loaded DLLs, because apparently even files need workplace drama.

---

## 🧩 Example Plugin Release Layout

A plugin release should usually look like this:

```text
SAEKO_Example_Plugin_v0.1.0/
├─ README.md
├─ RELEASE_NOTES.md
└─ mods/
   ├─ ExamplePlugin.dll
   └─ ExamplePlugin.ini
```

Users should copy the `mods/` folder into the same folder as the loader package before running `install.bat`.

They can also manually copy the files into:

```text
<SAEKO game folder>/saeko_mod_loader/mods/
```

---

## 🐧 Linux

For the native Linux Steam build, use:

```text
linux/
linux_loader/
```

### Fedora

```bash
sudo dnf install gcc rust cargo python3
```

### Linux Mint / Ubuntu

```bash
sudo apt update
sudo apt install build-essential rustc cargo python3
```

### Arch

```bash
sudo pacman -S base-devel rust python
```

### Build and install

```bash
./linux/build_linux_loader.sh
./linux/install_linux_loader.sh
```

### Steam launch option

```text
LD_PRELOAD="/path/to/SAEKO Giantess Dating Sim/libsaeko_mod_loader.so" %command%
```

If you run the Windows build through Proton, use the Windows loader instead.

> [!IMPORTANT]
> Linux support is experimental.  
> If something explodes, check the log before blaming the universe. Then blame the universe.

---

## 🧪 Diagnostics

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

Useful PowerShell check:

```powershell
Get-Content "<game folder>\saeko_mod_loader.log" -Tail 80
```

For install issues, check:

- whether SAEKO is closed,
- whether the game path is correct,
- whether `saeko_win64.original.exe` exists after first install,
- whether antivirus software quarantined the loader DLL,
- whether plugin DLLs are inside `mods/`.

---

## 🗂️ Repository Layout

```text
SAEKO-Mod-Loader/
├─ assets/
│  ├─ banner.png
│  └─ social-preview.png
├─ docs/
├─ linux/
├─ linux_loader/
├─ mods/
│  └─ .gitkeep
├─ texture_packs/
├─ tools/
├─ install.bat
├─ uninstall.bat
├─ saeko_mod_loader.dll
├─ saeko_mod_loader.ini
└─ README.md
```

---

## 🧷 Release Safety

Do **not** commit or publish files generated from a local game install unless you have the rights to redistribute them.

This repository is intended to ship:

- loader files,
- configuration files,
- documentation,
- helper scripts,
- empty plugin folders,
- release packaging notes.

It should **not** ship:

- original game executables,
- extracted game assets,
- private save files,
- local logs,
- personal paths,
- copied full game text dumps unless you have permission.

---

## 🚀 Recommended Release Flow

For loader releases:

```text
SAEKO_Mod_Loader_vX.Y.Z.zip
```

For plugin releases:

```text
SAEKO_PluginName_vX.Y.Z.zip
```

Suggested release contents:

```text
README.md
RELEASE_NOTES.md
mods/
```

Suggested tag format:

```text
loader-v0.1.0
resolution-unlock-v0.1.0
texture-packs-v0.1.0
```

---

## 🔗 Official Links

- [SAEKO on Steam](https://store.steampowered.com/app/2492120/SAEKO_Giantess_Dating_Sim/)
- [Official SAEKO website](https://saekogame.com/en/index.html)
- [HYPER REAL publisher page](https://hyperreal.jp/game/saeko-giantess-dating-sim/)

---

## 👥 Original Game Credits

**SAEKO: Giantess Dating Sim** is developed by **SAFE HAVN STUDIO** and published by **HYPER REAL**.

Credits listed by the official game materials include:

- **kyp** — story, programming, music, graphics
- **koh** — graphics
- **maztani** — design

---

## 🖤 Disclaimer

**SAEKO Mod Loader** is an unofficial fan project made for modding and translation experiments.

All rights to **SAEKO: Giantess Dating Sim** belong to their respective owners.
