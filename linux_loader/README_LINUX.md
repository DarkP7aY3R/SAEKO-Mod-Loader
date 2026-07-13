# SAEKO Mod Loader Linux

Native Linux loader for the Linux Steam build of SAEKO. It is independent from
the Windows PE/DLL installer and uses `LD_PRELOAD`.

## Packages

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

## Build

From the release folder:

```bash
./linux/build_linux_loader.sh
```

## Install

```bash
./linux/install_linux_loader.sh
```

If auto-detection fails:

```bash
./linux/install_linux_loader.sh "$HOME/.local/share/Steam/steamapps/common/SAEKO Giantess Dating Sim"
```

## Steam Launch Option

Set SAEKO launch options in Steam to:

```text
LD_PRELOAD="$HOME/.local/share/Steam/steamapps/common/SAEKO Giantess Dating Sim/libsaeko_mod_loader.so" %command%
```

Adjust the path if Steam is installed elsewhere.

## Notes

- This Linux loader patches the Go `embed.FS` table and language list in
  process memory.
- It loads optional native `.so` plugins from `saeko_mod_loader/mods/`.
- It is for native Linux builds. If you run the Windows build through Proton,
  use the Windows loader from the main release folder.
- Logs are written to `saeko_mod_loader_linux.log` next to the `.so`.
