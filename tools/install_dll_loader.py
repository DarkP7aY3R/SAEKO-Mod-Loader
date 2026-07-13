#!/usr/bin/env python3
"""Install SAEKO mod DLL loader.

This is the safer loader path:
- keep translations as loose files,
- load saeko_mod_loader.dll through the normal Windows import loader,
- let the DLL patch Go embed.FS in process memory after ASLR is resolved.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ID = "2492120"
GAME_INSTALL_DIR_NAME = "SAEKO Giantess Dating Sim"
FALLBACK_GAME_DIR = Path(r"L:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim")
DEFAULT_TRANSLATION_DIRS = (ROOT / "translation", ROOT / "pl")
DEFAULT_DLL = ROOT / "dll_loader" / "target" / "release" / "saeko_mod_loader.dll"
DEFAULT_CONFIG = ROOT / "saeko_mod_loader.ini"
DEFAULT_MODS_DIR = ROOT / "mods"
CONFIG_FILE = "saeko_mod_loader.ini"
DLL_NAME = "saeko_mod_loader.dll"
LEGACY_DLL_NAMES = ("saeko_pl_loader.dll",)
LEGACY_ARTIFACT_NAMES = ("saeko_pl_loader.log", "set_saeko_lang.ps1")
IMPORT_FUNC = "SaekoModLoaderInit"
LOADER_SECTION = ".plldr"
OLD_PACK_SECTION = ".plmod"
SECTION_LOADER = 0xE0000060
VERSION_NEEDLE = "V2.1.3"
DEFAULT_MODDED_LABEL = "modded"
DEFAULT_GAME_TRANSLATION_DIR = "saeko_mod_loader/lang"
MODS_FOLDER = Path("saeko_mod_loader") / "mods"
TEXTURE_PACKS_FOLDER = Path("saeko_mod_loader") / "texture_packs"


@dataclass(frozen=True)
class Section:
    name: str
    header_offset: int
    virtual_size: int
    virtual_address: int
    raw_size: int
    raw_start: int

    @property
    def virtual_end(self) -> int:
        return self.virtual_address + max(self.virtual_size, self.raw_size)


@dataclass(frozen=True)
class PeInfo:
    pe_offset: int
    optional_offset: int
    optional_size: int
    section_table_offset: int
    number_of_sections: int
    address_of_entrypoint: int
    section_alignment: int
    file_alignment: int
    size_of_headers: int
    sections: list[Section]


@dataclass(frozen=True)
class ModConfig:
    language_code: str
    language_label: str
    translation_dir: Path
    version_label: str


def version_label_for_language(language_code: str) -> str:
    return f"{VERSION_NEEDLE} {DEFAULT_MODDED_LABEL}"


def read_mod_config(path: Path | None) -> ModConfig:
    values: dict[str, str] = {}
    if path and path.exists():
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", ";", "[")):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip().lower()] = value.strip().strip('"').strip("'")

    language_code = values.get("language_code") or values.get("target_lang") or "custom"
    language_label = values.get("language_label") or values.get("label") or "Custom"
    game_translation_dir = values.get("translation_dir") or DEFAULT_GAME_TRANSLATION_DIR
    version_label = version_label_for_language(language_code)

    return ModConfig(
        language_code=language_code.lower(),
        language_label=language_label,
        translation_dir=Path(game_translation_dir),
        version_label=version_label,
    )


def align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def parse_pe(data: bytes | bytearray) -> PeInfo:
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ValueError("Not a PE/MZ executable")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("PE signature not found")

    number_of_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    optional_offset = pe_offset + 24
    magic = struct.unpack_from("<H", data, optional_offset)[0]
    if magic != 0x20B:
        raise ValueError(f"Expected PE32+, got optional magic 0x{magic:x}")

    section_alignment = struct.unpack_from("<I", data, optional_offset + 32)[0]
    file_alignment = struct.unpack_from("<I", data, optional_offset + 36)[0]
    size_of_headers = struct.unpack_from("<I", data, optional_offset + 60)[0]
    section_table_offset = optional_offset + optional_size
    address_of_entrypoint = struct.unpack_from("<I", data, optional_offset + 16)[0]

    sections: list[Section] = []
    for index in range(number_of_sections):
        header_offset = section_table_offset + index * 40
        name = data[header_offset : header_offset + 8].rstrip(b"\0").decode("latin1", "replace")
        virtual_size, virtual_address, raw_size, raw_start = struct.unpack_from(
            "<IIII", data, header_offset + 8
        )
        sections.append(
            Section(
                name=name,
                header_offset=header_offset,
                virtual_size=virtual_size,
                virtual_address=virtual_address,
                raw_size=raw_size,
                raw_start=raw_start,
            )
        )

    return PeInfo(
        pe_offset=pe_offset,
        optional_offset=optional_offset,
        optional_size=optional_size,
        section_table_offset=section_table_offset,
        number_of_sections=number_of_sections,
        address_of_entrypoint=address_of_entrypoint,
        section_alignment=section_alignment,
        file_alignment=file_alignment,
        size_of_headers=size_of_headers,
        sections=sections,
    )


def rva_to_offset(pe: PeInfo, rva: int) -> int | None:
    for section in pe.sections:
        if section.virtual_address <= rva < section.virtual_end:
            offset = section.raw_start + (rva - section.virtual_address)
            if section.raw_start <= offset < section.raw_start + section.raw_size:
                return offset
    return None


def has_section(exe: Path, name: str) -> bool:
    data = exe.read_bytes()
    pe = parse_pe(data)
    return any(section.name == name for section in pe.sections)


def steam_roots() -> list[Path]:
    roots: list[Path] = []
    for env_name in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        value = os.environ.get(env_name)
        if value:
            roots.append(Path(value) / "Steam")
    roots.extend(
        [
            Path(r"C:\Program Files (x86)\Steam"),
            Path(r"C:\Program Files\Steam"),
        ]
    )

    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).lower()
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def parse_steam_libraryfolders(path: Path) -> list[Path]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    libraries: list[Path] = []
    for match in re.finditer(r'"path"\s+"([^"]+)"', text):
        libraries.append(Path(match.group(1).replace("\\\\", "\\")))
    return libraries


def detect_game_dir() -> Path | None:
    candidates: list[Path] = [FALLBACK_GAME_DIR]
    for steam_root in steam_roots():
        if steam_root.exists():
            candidates.append(steam_root / "steamapps" / "common" / GAME_INSTALL_DIR_NAME)
        candidates.extend(
            library / "steamapps" / "common" / GAME_INSTALL_DIR_NAME
            for library in parse_steam_libraryfolders(steam_root / "steamapps" / "libraryfolders.vdf")
        )

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if (candidate / "saeko_win64.exe").exists():
            return candidate
    return None


def resolve_game_dir(game_dir: Path | None) -> Path:
    if game_dir is not None:
        return game_dir.resolve()
    detected = detect_game_dir()
    if detected is None:
        raise SystemExit(
            "Could not auto-detect SAEKO install dir. Re-run with "
            '--game-dir "X:\\SteamLibrary\\steamapps\\common\\SAEKO Giantess Dating Sim"'
        )
    return detected.resolve()


def next_section_va(pe: PeInfo) -> int:
    return align_up(max(section.virtual_end for section in pe.sections), pe.section_alignment)


def append_section(data: bytearray, pe: PeInfo, name: str, blob: bytes) -> None:
    if any(section.name == name for section in pe.sections):
        raise ValueError(f"EXE already has section {name}")
    raw_name = name.encode("ascii")
    if not raw_name or len(raw_name) > 8:
        raise ValueError("section name must be 1-8 ASCII bytes")

    header_end = pe.section_table_offset + (pe.number_of_sections + 1) * 40
    first_raw = min(section.raw_start for section in pe.sections if section.raw_start)
    if header_end > min(first_raw, pe.size_of_headers):
        raise ValueError("No free PE header room for an extra section")

    raw_start = align_up(len(data), pe.file_alignment)
    if len(data) < raw_start:
        data.extend(b"\0" * (raw_start - len(data)))
    raw_size = align_up(len(blob), pe.file_alignment)
    virtual_address = next_section_va(pe)
    virtual_size = len(blob)

    header_offset = pe.section_table_offset + pe.number_of_sections * 40
    struct.pack_into(
        "<8sIIIIIIHHI",
        data,
        header_offset,
        raw_name.ljust(8, b"\0"),
        virtual_size,
        virtual_address,
        raw_size,
        raw_start,
        0,
        0,
        0,
        0,
        SECTION_LOADER,
    )

    struct.pack_into("<H", data, pe.pe_offset + 6, pe.number_of_sections + 1)
    old_initialized = struct.unpack_from("<I", data, pe.optional_offset + 8)[0]
    struct.pack_into("<I", data, pe.optional_offset + 8, old_initialized + raw_size)
    struct.pack_into(
        "<I",
        data,
        pe.optional_offset + 56,
        align_up(virtual_address + virtual_size, pe.section_alignment),
    )
    struct.pack_into("<I", data, pe.optional_offset + 64, 0)

    data.extend(blob)
    if len(blob) < raw_size:
        data.extend(b"\0" * (raw_size - len(blob)))


def import_directory_info(data: bytes | bytearray, pe: PeInfo) -> tuple[int, int, bytes, int]:
    import_dir_offset = pe.optional_offset + 112 + 8
    import_rva, import_size = struct.unpack_from("<II", data, import_dir_offset)
    if import_rva == 0:
        return import_dir_offset, 0, b"", 0

    import_offset = rva_to_offset(pe, import_rva)
    if import_offset is None:
        raise ValueError("Could not map original import directory")

    count = 0
    while True:
        descriptor = data[import_offset + count * 20 : import_offset + count * 20 + 20]
        if len(descriptor) != 20:
            raise ValueError("Import descriptor table is truncated")
        if descriptor == b"\0" * 20:
            break
        count += 1
        if count > 256:
            raise ValueError("Import descriptor table is unexpectedly large")

    return import_dir_offset, import_size, bytes(data[import_offset : import_offset + count * 20]), count


def rel32(from_next_rva: int, to_rva: int) -> int:
    value = to_rva - from_next_rva
    if not -(2**31) <= value < 2**31:
        raise ValueError(f"RIP-relative jump/call is out of range: {value}")
    return value


def build_loader_import_blob(
    data: bytes | bytearray,
    pe: PeInfo,
    version_label: str,
) -> tuple[bytes, int, int, int]:
    import_dir_offset, _old_size, old_descriptors, old_count = import_directory_info(data, pe)
    section_rva = next_section_va(pe)

    descriptor_block_size = (old_count + 2) * 20
    blob = bytearray(old_descriptors)
    new_descriptor_offset = len(blob)
    blob.extend(b"\0" * 40)

    def add_bytes(payload: bytes, alignment: int = 1) -> int:
        while len(blob) % alignment:
            blob.append(0)
        rva = section_rva + len(blob)
        blob.extend(payload)
        return rva

    dll_name_rva = add_bytes(DLL_NAME.encode("ascii") + b"\0")
    import_by_name_rva = add_bytes(struct.pack("<H", 0) + IMPORT_FUNC.encode("ascii") + b"\0", 2)
    int_rva = add_bytes(struct.pack("<QQ", import_by_name_rva, 0), 8)
    iat_rva = add_bytes(struct.pack("<QQ", import_by_name_rva, 0), 8)

    while len(blob) % 16:
        blob.append(0)
    stub_rva = section_rva + len(blob)
    call_next_rva = stub_rva + 10
    jump_next_rva = stub_rva + 19
    blob.extend(
        b"\x48\x83\xEC\x28"
        b"\xFF\x15"
        + struct.pack("<i", rel32(call_next_rva, iat_rva))
        + b"\x48\x83\xC4\x28"
        + b"\xE9"
        + struct.pack("<i", rel32(jump_next_rva, pe.address_of_entrypoint))
    )
    add_bytes(version_label.encode("utf-8") + b"\0", 16)

    struct.pack_into(
        "<IIIII",
        blob,
        new_descriptor_offset,
        int_rva,
        0,
        0,
        dll_name_rva,
        iat_rva,
    )

    return bytes(blob), import_dir_offset, descriptor_block_size, stub_rva


def patch_import_table(source_exe: Path, output_exe: Path, config: ModConfig) -> None:
    data = bytearray(source_exe.read_bytes())
    pe = parse_pe(data)
    if any(section.name in {LOADER_SECTION, OLD_PACK_SECTION} for section in pe.sections):
        raise ValueError(f"Use a clean source EXE without {LOADER_SECTION} or {OLD_PACK_SECTION}")

    blob, import_dir_offset, import_size, stub_rva = build_loader_import_blob(
        data,
        pe,
        config.version_label,
    )
    import_rva = next_section_va(pe)
    append_section(data, pe, LOADER_SECTION, blob)
    struct.pack_into("<II", data, import_dir_offset, import_rva, import_size)
    struct.pack_into("<I", data, pe.optional_offset + 16, stub_rva)

    temp = output_exe.with_name(output_exe.name + ".tmp")
    if temp.exists():
        temp.unlink()
    temp.write_bytes(data)
    try:
        if not has_section(temp, LOADER_SECTION):
            raise ValueError("Patched EXE verification failed: loader section missing")
        temp.replace(output_exe)
    finally:
        if temp.exists():
            temp.unlink()


def copy_translation(translation_dir: Path, game_dir: Path, config: ModConfig) -> Path:
    target = (game_dir / config.translation_dir).resolve()
    game_root = game_dir.resolve()
    if game_root != target and game_root not in target.parents:
        raise ValueError(f"Refusing to copy outside game dir: {target}")
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(translation_dir, target)
    for csv_path in target.rglob("*.csv"):
        data = csv_path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            csv_path.write_bytes(data[3:])
    return target


def ensure_mods_folder(game_dir: Path) -> Path:
    mods_dir = game_dir / MODS_FOLDER
    mods_dir.mkdir(parents=True, exist_ok=True)
    readme = mods_dir / "README.txt"
    if not readme.exists():
        readme.write_text(
            "\n".join(
                [
                    "SAEKO Mod Loader mods folder",
                    "",
                    "Put extra mod DLL files here.",
                    "Optional config files can use the same base name, for example:",
                    "  ExampleMod.dll",
                    "  ExampleMod.ini",
                    "",
                    "Disable a DLL by renaming it to:",
                    "  ExampleMod.dll.disabled",
                    "",
                    "Config-only INI files are shown in the Mods menu status panel but are not toggled.",
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )
    return mods_dir


def copy_optional_mods(source: Path | None, target: Path) -> int:
    if source is None or not source.exists():
        return 0
    copied = 0
    for item in source.iterdir():
        if item.name.lower() == "readme.txt" or not item.is_file():
            continue
        lower = item.name.lower()
        if not (
            lower.endswith(".dll")
            or lower.endswith(".dll.disabled")
            or lower.endswith(".ini")
        ):
            continue
        dst = target / item.name
        if dst.exists() and dst.read_bytes() == item.read_bytes():
            continue
        shutil.copy2(item, dst)
        copied += 1
    return copied


def ensure_texture_packs_folder(game_dir: Path) -> Path:
    packs_dir = game_dir / TEXTURE_PACKS_FOLDER
    packs_dir.mkdir(parents=True, exist_ok=True)
    readme = packs_dir / "README.txt"
    if not readme.exists():
        readme.write_text(
            "\n".join(
                [
                    "SAEKO texture_packs folder",
                    "",
                    "Use the in-game Mods popup button \"Generate textures\" to export vanilla PNG files to:",
                    "  default/",
                    "",
                    "Create a sibling folder, edit PNG files there, then set active_packs in:",
                    "  saeko_mod_loader/mods/saeko_texture_packs.ini",
                    "",
                    "Do not redistribute the generated default folder unless you have rights to the game assets.",
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )
    return packs_dir


def copy_optional_texture_packs(source: Path | None, target: Path) -> int:
    if source is None or not source.exists():
        return 0
    copied = 0
    for item in source.iterdir():
        if item.name.lower() == "default":
            continue
        dst = target / item.name
        if item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
            copied += 1
        elif item.is_file():
            if dst.exists() and dst.read_bytes() == item.read_bytes():
                continue
            shutil.copy2(item, dst)
            copied += 1
    return copied


def write_saeko_lang(lang: str) -> Path | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    settings_dir = Path(appdata) / "SAEKO"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_path = settings_dir / "settings.json"

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8-sig"))
            if not isinstance(settings, dict):
                settings = {}
        except (OSError, json.JSONDecodeError):
            settings = {}
    else:
        settings = {}

    defaults: dict[str, object] = {
        "Fullscreen": True,
        "Lang": lang,
        "FXVolume": 5,
        "MusicVolume": 5,
        "VibrateMagnitude": 0,
        "Resolution": "1920x1080",
        "WindowedResolution": "1280x720",
        "AnswerSpeed": "speed_normal",
    }
    for key, value in defaults.items():
        settings.setdefault(key, value)
    settings["Lang"] = lang
    settings_path.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return settings_path


def find_steam_app_id(game_dir: Path) -> str | None:
    if game_dir.parent.name.lower() != "common":
        return None
    steamapps = game_dir.parent.parent
    for manifest in steamapps.glob("appmanifest_*.acf"):
        text = manifest.read_text(encoding="utf-8", errors="ignore")
        if f'"installdir"\t\t"{game_dir.name}"' in text or f'"installdir"\t"{game_dir.name}"' in text:
            stem = manifest.stem
            if stem.startswith("appmanifest_"):
                return stem.removeprefix("appmanifest_")
    return APP_ID


def write_launcher(game_dir: Path, lang: str) -> Path:
    launcher = game_dir / "run_saeko_mod_loader.bat"
    ps_script = game_dir / "set_saeko_mod_lang.ps1"
    ps_script.write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"$targetLang = '{lang}'",
                "$settingsDir = Join-Path $env:APPDATA 'SAEKO'",
                "[System.IO.Directory]::CreateDirectory($settingsDir) | Out-Null",
                "$settingsPath = Join-Path $settingsDir 'settings.json'",
                "$settings = $null",
                "if (Test-Path -LiteralPath $settingsPath) {",
                "  try { $settings = (Get-Content -Raw -LiteralPath $settingsPath).TrimStart([char]0xFEFF) | ConvertFrom-Json } catch { $settings = $null }",
                "}",
                "if ($null -eq $settings) { $settings = [pscustomobject]@{} }",
                "if ($settings.PSObject.Properties.Name -contains 'Lang') { $settings.Lang = $targetLang } else { Add-Member -InputObject $settings -MemberType NoteProperty -Name Lang -Value $targetLang }",
                "$json = $settings | ConvertTo-Json -Depth 50",
                "$encoding = New-Object System.Text.UTF8Encoding -ArgumentList $false",
                "[System.IO.File]::WriteAllText($settingsPath, $json + [Environment]::NewLine, $encoding)",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )

    app_id = find_steam_app_id(game_dir)
    launch_line = f'start "" "steam://rungameid/{app_id}"' if app_id else 'start "" "%~dp0saeko_win64.exe"'
    launcher.write_text(
        "\n".join(
            [
                "@echo off",
                "setlocal",
                'cd /d "%~dp0"',
                'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0set_saeko_mod_lang.ps1"',
                "if errorlevel 1 exit /b 1",
                launch_line,
                "",
            ]
        ),
        encoding="ascii",
        newline="\r\n",
    )
    return launcher


def resolve_translation_dir(args: argparse.Namespace, config: ModConfig) -> Path | None:
    if args.no_translation_copy:
        return None

    if args.translation_dir is not None:
        translation_dir = args.translation_dir.resolve()
        if not translation_dir.exists():
            raise SystemExit(f"Missing translation dir passed with --translation-dir: {translation_dir}")
        return translation_dir

    candidates = [ROOT / config.language_code, *DEFAULT_TRANSLATION_DIRS]
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if resolved.exists():
            return resolved
    return None


def install(args: argparse.Namespace) -> int:
    game_dir = resolve_game_dir(args.game_dir)
    live_exe = game_dir / "saeko_win64.exe"
    backup_exe = (args.backup_exe or (game_dir / "saeko_win64.original.exe")).resolve()
    dll_path = args.dll.resolve()
    config_path = (args.config or DEFAULT_CONFIG).resolve()
    config = read_mod_config(config_path)
    translation_dir = resolve_translation_dir(args, config)
    copy_language_files = translation_dir is not None

    if not live_exe.exists():
        raise SystemExit(f"Missing game EXE: {live_exe}")
    if not dll_path.exists():
        raise SystemExit(f"Missing DLL: {dll_path}\nRun build_dll_loader.bat first.")

    live_has_loader = has_section(live_exe, LOADER_SECTION) or has_section(live_exe, OLD_PACK_SECTION)
    if not backup_exe.exists():
        if live_has_loader:
            raise SystemExit(f"Live EXE is already patched and backup is missing: {backup_exe}")
        if not args.dry_run:
            shutil.copy2(live_exe, backup_exe)

    source_exe = backup_exe if backup_exe.exists() else live_exe
    print(f"Source EXE:      {source_exe}")
    print(f"Output EXE:      {live_exe}")
    print(f"DLL:             {dll_path}")
    print(f"Config:          {config_path if config_path.exists() else '(defaults)'}")
    print(f"Language:        {config.language_code} ({config.language_label})")
    print(f"Version label:   {config.version_label}")
    print(f"Game CSV dir:    {config.translation_dir}")
    print(f"Translation dir: {translation_dir if copy_language_files else '(disabled)'}")

    if args.dry_run:
        print("Dry-run OK: no files were written.")
        return 0

    try:
        patch_import_table(source_exe, live_exe, config)
    except PermissionError as err:
        raise SystemExit(
            f"Could not patch {live_exe}: access denied. "
            "Close SAEKO/Steam's running game process and run the installer again."
        ) from err
    shutil.copy2(dll_path, game_dir / DLL_NAME)
    for legacy_name in LEGACY_DLL_NAMES + LEGACY_ARTIFACT_NAMES:
        legacy_path = game_dir / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()
    if config_path.exists():
        shutil.copy2(config_path, game_dir / CONFIG_FILE)
    copied_translation = copy_translation(translation_dir, game_dir, config) if translation_dir else None
    mods_dir = ensure_mods_folder(game_dir)
    copied_mods = copy_optional_mods(args.mods_dir.resolve() if args.mods_dir else None, mods_dir)
    texture_packs_dir = ensure_texture_packs_folder(game_dir)
    texture_source = (
        args.texture_packs_dir.resolve()
        if args.texture_packs_dir
        else (args.mods_dir.resolve().parent / "texture_packs" if args.mods_dir else None)
    )
    copied_texture_packs = copy_optional_texture_packs(texture_source, texture_packs_dir)
    settings_language = config.language_code if copy_language_files else "en"
    settings = write_saeko_lang(settings_language)
    launcher = write_launcher(game_dir, settings_language)

    print("Install OK.")
    print(f"Copied DLL:      {game_dir / DLL_NAME}")
    if config_path.exists():
        print(f"Copied config:   {game_dir / CONFIG_FILE}")
    print(f"Copied CSV:      {copied_translation if copied_translation else '(skipped)'}")
    print(f"Mods folder:     {mods_dir}")
    print(f"Copied mods:     {copied_mods}")
    print(f"Texture packs:   {texture_packs_dir}")
    print(f"Copied packs:    {copied_texture_packs}")
    if settings:
        print(f"Settings Lang:   {settings_language} ({settings})")
    print(f"Launcher:        {launcher}")
    return 0


def uninstall(args: argparse.Namespace) -> int:
    game_dir = resolve_game_dir(args.game_dir)
    live_exe = game_dir / "saeko_win64.exe"
    backup_exe = (args.backup_exe or (game_dir / "saeko_win64.original.exe")).resolve()
    if not backup_exe.exists():
        raise SystemExit(f"Missing backup EXE: {backup_exe}")

    print(f"Backup EXE:      {backup_exe}")
    print(f"Restore target:  {live_exe}")
    if args.dry_run:
        print("Dry-run OK: no files were written.")
        return 0

    shutil.copy2(backup_exe, live_exe)
    settings = write_saeko_lang("en")
    launcher = write_launcher(game_dir, "en")
    print("Uninstall OK.")
    if settings:
        print(f"Settings Lang:   en ({settings})")
    print(f"Launcher:        {launcher}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-dir", type=Path, default=None)
    parser.add_argument(
        "--translation-dir",
        type=Path,
        default=None,
        help=(
            "Optional local CSV folder to copy into the game. If omitted, installer "
            "looks for ./<language_code>, ./translation, then ./pl; if none exists, "
            "CSV copy is skipped."
        ),
    )
    parser.add_argument("--dll", type=Path, default=DEFAULT_DLL)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--mods-dir", type=Path, default=DEFAULT_MODS_DIR)
    parser.add_argument("--texture-packs-dir", type=Path, default=None)
    parser.add_argument("--backup-exe", type=Path)
    parser.add_argument(
        "--no-translation-copy",
        action="store_true",
        help="Install only the DLL/config/bootstrap/mods and do not copy any CSV folder.",
    )
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.install == args.uninstall:
        raise SystemExit("Use exactly one of --install or --uninstall")
    return install(args) if args.install else uninstall(args)


if __name__ == "__main__":
    raise SystemExit(main())
