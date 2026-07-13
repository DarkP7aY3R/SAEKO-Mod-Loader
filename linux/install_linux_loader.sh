#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME_DIR="${1:-}"

if [[ -z "$GAME_DIR" ]]; then
  for candidate in \
    "$HOME/.local/share/Steam/steamapps/common/SAEKO Giantess Dating Sim" \
    "$HOME/.steam/steam/steamapps/common/SAEKO Giantess Dating Sim" \
    "$HOME/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/SAEKO Giantess Dating Sim"; do
    if [[ -d "$candidate" ]]; then
      GAME_DIR="$candidate"
      break
    fi
  done
fi

if [[ -z "$GAME_DIR" || ! -d "$GAME_DIR" ]]; then
  echo "Game directory not found. Pass it as the first argument." >&2
  exit 1
fi

SO="$ROOT/linux/dist/libsaeko_mod_loader.so"
if [[ ! -f "$SO" ]]; then
  "$ROOT/linux/build_linux_loader.sh"
fi

mkdir -p "$GAME_DIR/saeko_mod_loader/lang" "$GAME_DIR/saeko_mod_loader/mods"
cp "$SO" "$GAME_DIR/libsaeko_mod_loader.so"
cp "$ROOT/saeko_mod_loader.ini" "$GAME_DIR/saeko_mod_loader.ini"
cp -a "$ROOT/pl/." "$GAME_DIR/saeko_mod_loader/lang/"
if [[ -d "$ROOT/mods" ]]; then
  find "$ROOT/mods" -maxdepth 1 -type f \( -name '*.so' -o -name '*.ini' \) -exec cp -f {} "$GAME_DIR/saeko_mod_loader/mods/" \;
fi

cat > "$GAME_DIR/run_saeko_mod_loader_linux.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "\$(dirname "\${BASH_SOURCE[0]}")"
export LD_PRELOAD="\$PWD/libsaeko_mod_loader.so\${LD_PRELOAD:+:\$LD_PRELOAD}"
exec ./saeko "\$@"
EOF
chmod +x "$GAME_DIR/run_saeko_mod_loader_linux.sh"

echo "Installed Linux loader to: $GAME_DIR"
echo
echo "Steam launch option:"
echo "LD_PRELOAD=\"$GAME_DIR/libsaeko_mod_loader.so\" %command%"
echo
echo "If the native executable name is not ./saeko, adjust run_saeko_mod_loader_linux.sh."
