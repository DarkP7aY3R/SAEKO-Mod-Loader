SAEKO texture_packs folder

The experimental saeko_texture_packs.dll mod exports vanilla PNG files from your
local game install to:

  default/

Create another folder next to default, copy files into it, edit the PNG files,
then set pack priority in:

  mods/saeko_texture_packs.ini

Example:

  active_packs=my_pack,my_ui_pack

First pack wins. Missing files fall back to vanilla embedded assets.

Do not redistribute the generated default folder unless you have rights to the
game assets.

Experimental local generator:

  python -m pip install -r tools/requirements-texture.txt
  python tools/create_real_world_texture_pack.py

It creates real_world_safe_experiment next to default, preserving file names,
dimensions, and alpha. Enable locally in mods/saeko_texture_packs.ini:

  active_packs=real_world_safe_experiment

Do not redistribute generated real_world_safe_experiment PNG files if they were
created from your local game assets.
