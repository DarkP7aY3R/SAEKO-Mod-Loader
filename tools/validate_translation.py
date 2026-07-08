#!/usr/bin/env python3
"""Validate SAEKO translation CSV structure against the extracted source."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "source" / "en"
DEFAULT_TRANSLATION = ROOT / "translation"
TRANSLATABLE_FIRST_COLUMN_FILES = {
    Path("staffs.csv"),
    Path("staffs-stove.csv"),
}
SCRIPT_SPEAKER_KEYS = {
    "akari",
    "chio",
    "clara",
    "kazu",
    "kina",
    "m",
    "maru",
    "moko",
    "rin",
    "s",
    "saeko",
    "shimon",
    "taki",
    "yui",
}
TRANSLATABLE_SCRIPT_COMMAND_ROWS = {
    "center",
    "intro",
    "radio",
}


def read_csv(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_utf8_bom(path: Path) -> bool:
    return path.read_bytes().startswith(b"\xef\xbb\xbf")


def rel_csvs(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*.csv"))


def is_story_script(rel: Path) -> bool:
    return rel.parts[0] == "basic" or rel.name.startswith(("day_", "night_"))


def validate_file(base: Path, translated: Path, rel: Path) -> list[str]:
    errors: list[str] = []
    translated_path = translated / rel
    if has_utf8_bom(translated_path):
        errors.append(f"{rel}: file starts with UTF-8 BOM; save as UTF-8 without BOM")

    try:
        base_rows = read_csv(base / rel)
    except Exception as exc:  # noqa: BLE001
        return [f"{rel}: cannot read source CSV: {exc}"]

    try:
        translated_rows = read_csv(translated_path)
    except Exception as exc:  # noqa: BLE001
        return [f"{rel}: cannot read translated CSV: {exc}"]

    if len(base_rows) != len(translated_rows):
        errors.append(f"{rel}: row count changed {len(base_rows)} -> {len(translated_rows)}")

    for index, (base_row, translated_row) in enumerate(zip(base_rows, translated_rows), start=1):
        if len(base_row) != len(translated_row):
            errors.append(f"{rel}:{index}: column count changed {len(base_row)} -> {len(translated_row)}")
            continue

        if not base_row:
            continue

        base_key = base_row[0]
        translated_key = translated_row[0]
        if (
            rel not in TRANSLATABLE_FIRST_COLUMN_FILES
            and base_key != translated_key
            and not base_key.lstrip().startswith("#")
        ):
            errors.append(f"{rel}:{index}: first column changed {base_key!r} -> {translated_key!r}")
            continue

        if not is_story_script(rel) or base_key.lstrip().startswith("#"):
            continue

        script_key = base_key.strip()
        if script_key in SCRIPT_SPEAKER_KEYS:
            if len(base_row) >= 3 and base_row[1] != translated_row[1]:
                errors.append(
                    f"{rel}:{index}: speaker metadata changed {base_row[1]!r} -> {translated_row[1]!r}"
                )
        elif script_key not in TRANSLATABLE_SCRIPT_COMMAND_ROWS and base_row != translated_row:
            errors.append(f"{rel}:{index}: command row changed {base_row!r} -> {translated_row!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--translation", type=Path, default=DEFAULT_TRANSLATION, help="Translation CSV folder to validate. Defaults to ./translation.")
    args = parser.parse_args()

    base = args.base.resolve()
    translated = args.translation.resolve()

    if not base.exists():
        raise SystemExit(f"Missing source folder: {base}")
    if not translated.exists():
        raise SystemExit(f"Missing translation folder: {translated}\nPass --translation <folder> or create ./translation first.")

    base_files = rel_csvs(base)
    translated_files = rel_csvs(translated)
    errors: list[str] = []

    missing = sorted(set(base_files) - set(translated_files))
    extra = sorted(set(translated_files) - set(base_files))
    errors.extend(f"{path}: missing translated file" for path in missing)
    errors.extend(f"{path}: extra translated file" for path in extra)

    unchanged = 0
    checked = 0
    for rel in base_files:
        if rel in missing:
            continue
        checked += 1
        errors.extend(validate_file(base, translated, rel))
        if sha256(base / rel) == sha256(translated / rel):
            unchanged += 1

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"OK: {checked} CSV files match the expected structure.")
    print(f"Unchanged files: {unchanged}/{checked}")
    if unchanged:
        print("Unchanged files are fine at the start; this number should go down as you translate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
