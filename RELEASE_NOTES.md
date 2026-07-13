# SAEKO Mod Loader Release Notes

## Included

- `saeko_mod_loader.dll` universal DLL loader.
- Native in-game `Mods` menu drawn with SAEKO UI assets.
- Optional loose CSV language folder in `translation/` or `pl/` when the user provides one.
- Optional external mod folder in `mods/`.
- `saeko_resolution_unlock.dll` test mod with 16:9 and 16:10 resolution support.
- `saeko_texture_packs.dll` experimental texture pack mod.
- Native Linux loader source and install scripts in `linux_loader/` and `linux/`.

## Resolution Unlock Notes

The bundled resolution mod now patches four game paths:

- settings menu resolution labels,
- resolution width/height parsing,
- `scene.Game.Layout`,
- `fontutil.Scale`.

The INI now includes:

```text
render_mode=stretch
stretch_textures=true
base_aspect=16:9
```

`stretch` is the default texture-stretch mode. It returns the selected `WxH` canvas so Ebiten fills the whole screen or window, while font scaling still follows SAEKO's 16:9 design height. This avoids the unused black area that appears when 16:10 is forced through a 16:9 canvas. `fill` keeps proportions and uses crop/fill overscan, so it can cut the edges. `native` returns the selected `WxH` canvas directly without the extra stretch font-scale correction.

Fullscreen can still be limited by the monitor/GPU if a display mode is not supported by the system.

## Texture Pack Notes

The experimental texture pack mod scans the active Go `embed.FS` table, exports local embedded PNG files into `saeko_mod_loader/texture_packs/default`, and then patches matching PNG records from folders listed in:

```text
mods/saeko_texture_packs.ini
```

Example:

```text
active_packs=my_pack,my_ui_pack
```

The repository and release zip do not include generated vanilla textures. Users generate `default` from their own installed copy of the game.

## Before Publishing

Run these commands from the project folder before uploading the zip:

```powershell
python .\tools\install_dll_loader.py --install --dry-run --dll ".\saeko_mod_loader.dll" --config ".\saeko_mod_loader.ini" --mods-dir ".\mods" --texture-packs-dir ".\texture_packs" --no-translation-copy
```

If you include a translation folder locally, also run:

```powershell
python .\tools\validate_translation.py --translation ".\translation"
```

Upload:

```text
GitHub release assets from this repository, without generated texture_packs/default or real_world folders.
```
