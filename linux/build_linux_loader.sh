#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cargo build --manifest-path "$ROOT/linux_loader/Cargo.toml" --release
mkdir -p "$ROOT/linux/dist"
cp "$ROOT/linux_loader/target/release/libsaeko_mod_loader.so" "$ROOT/linux/dist/libsaeko_mod_loader.so"
echo "Built: $ROOT/linux/dist/libsaeko_mod_loader.so"
