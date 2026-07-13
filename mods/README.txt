SAEKO Mod Loader mods folder

Put extra mod DLL files here.
Optional config files can use the same base name, for example:
  ExampleMod.dll
  ExampleMod.ini

Disable a DLL by renaming it to:
  ExampleMod.dll.disabled

Config-only INI files are listed in the loader log but are not toggled in-game.

Included test mods:
  saeko_resolution_unlock.dll
  saeko_resolution_unlock.ini
  saeko_texture_packs.dll
  saeko_texture_packs.ini

It unlocks extra 16:9 and 16:10 settings resolutions from the INI list.
The mod also patches SAEKO's internal Layout and font scaling code, so the
game canvas can fill the selected WxH resolution without forced 16:9 bars.

The texture pack mod can export local vanilla PNG files to:
  ../texture_packs/default/

Then it can replace PNG assets from folders configured in:
  saeko_texture_packs.ini

Default startup auto-export is disabled to avoid slow first launches. Use the
in-game Mods popup button "Generate textures" when you want to create default/.
