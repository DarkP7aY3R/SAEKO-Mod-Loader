# GitHub Release Checklist

Use this checklist before publishing the loader or attaching a release zip.

## Do not publish generated game assets

Do not commit or upload these folders unless you have explicit rights to the
game assets inside them:

- `saeko_mod_loader/texture_packs/default/`
- `saeko_mod_loader/texture_packs/real_world_safe_experiment/`
- any other generated texture pack derived from the local game install

The release zip should include only `texture_packs/README.txt` and generator
tools, not generated PNG files.

## Validate repository contents

```powershell
git status --short
python .\tools\install_dll_loader.py --install --dry-run --dll ".\saeko_mod_loader.dll" --config ".\saeko_mod_loader.ini" --mods-dir ".\mods" --texture-packs-dir ".\texture_packs" --no-translation-copy
```

Expected checks:

- `saeko_mod_loader.dll` exists in the repository root.
- `mods\saeko_resolution_unlock.dll` exists.
- `mods\saeko_texture_packs.dll` exists.
- Any release archive contains `tools\create_real_world_texture_pack.py`.
- Any release archive does not contain `texture_packs\default\` or `real_world_safe_experiment\`.
- The repository does not contain generated PNG texture packs.

If you are working from the private development workspace instead of this
release repository, rebuild the Windows DLLs there before copying release files:

```powershell
.\build_dll_loader.bat
.\build_resolution_unlock_mod.bat
.\build_texture_pack_mod.bat
.\package_release.bat
```

## Runtime defaults

- `mods\saeko_texture_packs.ini` must ship with `active_packs=` empty.
- `mods\saeko_texture_packs.ini` must ship with `export_default=false`.
- Users generate `default/` through the in-game `Mods -> Generate textures` action.
- Optional texture packs are enabled by setting `active_packs=<pack_name>` locally.

## Local smoke test

After installing locally, check:

```text
saeko_mod_loader.log
saeko_mod_loader\mods\saeko_texture_packs.log
saeko_mod_loader\mods\saeko_resolution_unlock.log
```

The game should reach the title screen without a Windows panic dialog. If a
texture pack is enabled, `saeko_texture_packs.log` should show `patched_png=...`.
