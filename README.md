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
  <a href="#-external-plugins">Plugins</a>
  ·
  <a href="#-custom-language-packs">Language Packs</a>
  ·
  <a href="#-linux">Linux</a>
  ·
  <a href="#-official-links">Official Links</a>
</p>

---

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
| Linux native loader files | 🧪 Experimental |
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
