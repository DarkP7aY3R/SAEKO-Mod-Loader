from __future__ import annotations

import argparse
import hashlib
import math
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
PACK_NAME = "real_world_safe_experiment"


@dataclass
class TextureInfo:
    rel: str
    size: tuple[int, int]
    category: str
    has_alpha: bool
    mode: str


def resolve_default_root(value: str | None) -> Path:
    candidates: list[Path] = []
    if value:
        candidates.append(Path(value))
    candidates.append(ROOT / "texture_packs" / "default")
    candidates.extend(detect_installed_default_roots())
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise SystemExit(
        "Could not find texture_packs/default. Generate it from the in-game Mods popup first, "
        "or pass --default-root."
    )


def detect_installed_default_roots() -> list[Path]:
    try:
        from install_dll_loader import TEXTURE_PACKS_FOLDER, resolve_game_dir
    except Exception:
        return []

    roots: list[Path] = []
    for explicit in (None,):
        try:
            game_dir = resolve_game_dir(explicit)
        except Exception:
            continue
        roots.append(game_dir / TEXTURE_PACKS_FOLDER / "default")
    return roots


def classify(rel: str) -> str:
    lower = rel.replace("\\", "/").lower()
    if "/ui/" in lower or "/icons/" in lower or "/soundtrack/" in lower or "/demomenu/" in lower:
        return "ui"
    if "/characters/" in lower:
        return "character"
    if "/faces/" in lower:
        return "face"
    if "/cakes/" in lower:
        return "food_object"
    if "/room/" in lower:
        return "room"
    if "/title/" in lower or "/intro/" in lower or "/ending/" in lower or "/postend/" in lower:
        return "scene"
    if "/night/" in lower or "/midnight/" in lower:
        return "night_scene"
    if "/cutins/" in lower:
        return "cutin"
    if "/effects/" in lower:
        return "effect"
    return "misc"


def seed_for(rel: str) -> int:
    digest = hashlib.blake2b(rel.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little")


def safe_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def collect_infos(default_root: Path) -> list[TextureInfo]:
    infos: list[TextureInfo] = []
    for path in sorted(default_root.rglob("*.png")):
        rel = safe_rel(path, default_root)
        with Image.open(path) as image:
            has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
            infos.append(
                TextureInfo(
                    rel=rel,
                    size=image.size,
                    category=classify(rel),
                    has_alpha=has_alpha,
                    mode=image.mode,
                )
            )
    return infos


def resize_noise(rng: np.random.Generator, width: int, height: int, cell: int) -> np.ndarray:
    small_w = max(1, math.ceil(width / cell))
    small_h = max(1, math.ceil(height / cell))
    small = (rng.random((small_h, small_w)) * 255).astype(np.uint8)
    image = Image.fromarray(small, "L").resize((width, height), Image.Resampling.BICUBIC)
    return np.asarray(image, dtype=np.float32) / 255.0


def fractal_noise(width: int, height: int, seed: int, category: str) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = np.zeros((height, width), dtype=np.float32)
    weights = [0.48, 0.26, 0.16, 0.10]
    cells = [max(2, min(width, height) // 3), 24, 9, 3]
    if category in {"ui", "effect"}:
        weights = [0.55, 0.25, 0.14, 0.06]
        cells = [32, 16, 8, 4]
    for weight, cell in zip(weights, cells):
        noise += resize_noise(rng, width, height, max(1, cell)) * weight
    noise -= noise.min()
    max_value = float(noise.max())
    if max_value > 0:
        noise /= max_value
    return noise


def category_strength(category: str, area: int) -> float:
    base = {
        "ui": 0.22,
        "effect": 0.30,
        "face": 0.38,
        "character": 0.46,
        "food_object": 0.58,
        "room": 0.64,
        "scene": 0.66,
        "night_scene": 0.60,
        "cutin": 0.48,
        "misc": 0.42,
    }.get(category, 0.42)
    if area <= 32 * 32:
        base *= 0.55
    elif area <= 96 * 96:
        base *= 0.78
    return base


def category_grade(rgb: np.ndarray, category: str) -> np.ndarray:
    if category in {"room", "scene", "night_scene"}:
        grade = np.array([1.08, 1.03, 0.95], dtype=np.float32)
    elif category == "food_object":
        grade = np.array([1.12, 1.02, 0.90], dtype=np.float32)
    elif category in {"character", "face", "cutin"}:
        grade = np.array([1.06, 1.00, 0.96], dtype=np.float32)
    elif category == "ui":
        grade = np.array([0.98, 1.00, 1.05], dtype=np.float32)
    else:
        grade = np.array([1.03, 1.02, 0.98], dtype=np.float32)
    return np.clip(rgb * grade.reshape(1, 1, 3), 0.0, 1.0)


def material_palette(category: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    palettes = {
        "ui": ([0.08, 0.09, 0.10], [0.48, 0.52, 0.56], [0.92, 0.94, 0.96]),
        "effect": ([0.08, 0.10, 0.12], [0.28, 0.35, 0.45], [0.75, 0.85, 1.00]),
        "face": ([0.42, 0.27, 0.20], [0.78, 0.56, 0.43], [0.98, 0.78, 0.62]),
        "character": ([0.22, 0.18, 0.17], [0.57, 0.42, 0.36], [0.92, 0.72, 0.56]),
        "food_object": ([0.22, 0.12, 0.06], [0.72, 0.45, 0.25], [1.00, 0.86, 0.62]),
        "room": ([0.06, 0.045, 0.035], [0.30, 0.20, 0.12], [0.68, 0.50, 0.32]),
        "scene": ([0.05, 0.05, 0.05], [0.24, 0.22, 0.18], [0.72, 0.68, 0.55]),
        "night_scene": ([0.02, 0.025, 0.04], [0.12, 0.15, 0.22], [0.45, 0.48, 0.60]),
        "cutin": ([0.04, 0.04, 0.045], [0.34, 0.30, 0.28], [0.84, 0.72, 0.62]),
        "misc": ([0.08, 0.08, 0.08], [0.34, 0.32, 0.28], [0.78, 0.72, 0.62]),
    }
    values = palettes.get(category, palettes["misc"])
    return tuple(np.array(value, dtype=np.float32) for value in values)  # type: ignore[return-value]


def photo_mix_for(category: str, area: int) -> float:
    mix = {
        "ui": 0.34,
        "effect": 0.45,
        "face": 0.52,
        "character": 0.58,
        "food_object": 0.76,
        "room": 0.82,
        "scene": 0.84,
        "night_scene": 0.78,
        "cutin": 0.66,
        "misc": 0.55,
    }.get(category, 0.55)
    if area <= 32 * 32:
        mix *= 0.50
    elif area <= 96 * 96:
        mix *= 0.72
    return mix


def material_texture(
    width: int,
    height: int,
    category: str,
    seed: int,
    original_rgb: np.ndarray,
) -> np.ndarray:
    dark, mid, light = material_palette(category)
    coarse = fractal_noise(width, height, seed ^ 0x13579BDF, category)
    fine = fractal_noise(width, height, seed ^ 0x2468ACE0, "ui")
    grain = np.clip(coarse * 0.76 + fine * 0.24, 0.0, 1.0)

    material = np.empty((height, width, 3), dtype=np.float32)
    lower = grain < 0.52
    upper = ~lower
    lower_t = np.clip(grain / 0.52, 0.0, 1.0)
    upper_t = np.clip((grain - 0.52) / 0.48, 0.0, 1.0)
    material[lower] = dark * (1.0 - lower_t[lower, None]) + mid * lower_t[lower, None]
    material[upper] = mid * (1.0 - upper_t[upper, None]) + light * upper_t[upper, None]

    tint = np.mean(original_rgb.reshape(-1, 3), axis=0)
    if float(np.max(tint)) > 0.02:
        tint = np.clip(tint / max(float(np.max(tint)), 0.2), 0.0, 1.0)
        material = np.clip(material * 0.70 + tint.reshape(1, 1, 3) * 0.30, 0.0, 1.0)

    if category in {"room", "scene", "night_scene"}:
        yy, xx = np.mgrid[0:height, 0:width]
        bands = np.sin((xx * 0.045) + coarse * 5.5) * 0.035
        pores = (fine - 0.5) * 0.12
        material = np.clip(material + bands[..., None] + pores[..., None], 0.0, 1.0)
    elif category == "food_object":
        cream = np.clip((fine - 0.4) * 0.20, -0.05, 0.18)
        material = np.clip(material + cream[..., None] * np.array([1.0, 0.82, 0.55]), 0.0, 1.0)
    elif category in {"character", "face", "cutin"}:
        skin_pores = (fine - 0.5) * 0.08
        material = np.clip(material + skin_pores[..., None], 0.0, 1.0)
    elif category == "ui":
        yy = np.linspace(0.0, 1.0, height, dtype=np.float32).reshape(height, 1, 1)
        gloss = np.clip(0.18 - np.abs(yy - 0.25) * 0.45, 0.0, 0.12)
        material = np.clip(material + gloss, 0.0, 1.0)

    return material


def de_pixelate_rgba(image: Image.Image, category: str, rel: str) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    area = width * height
    if width <= 2 or height <= 2:
        return rgba

    scale = 4 if max(width, height) <= 512 else 2
    large = rgba.resize((width * scale, height * scale), Image.Resampling.NEAREST)
    large = large.filter(ImageFilter.SMOOTH_MORE)
    large = large.filter(ImageFilter.GaussianBlur(radius=0.55 * scale))
    large = ImageEnhance.Sharpness(large).enhance(1.8)
    base = large.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")

    arr = np.asarray(base, dtype=np.float32) / 255.0
    original = np.asarray(rgba, dtype=np.float32) / 255.0
    alpha = original[..., 3:4]
    rgb = arr[..., :3]
    original_rgb = original[..., :3]

    strength = category_strength(category, area)
    rgb = rgb * (0.72 + strength * 0.18) + original_rgb * (0.28 - strength * 0.08)
    seed = seed_for(rel)
    material = material_texture(width, height, category, seed, original_rgb)
    photo_mix = photo_mix_for(category, area)
    rgb = np.clip(rgb * (1.0 - photo_mix) + material * photo_mix, 0.0, 1.0)
    rgb = category_grade(rgb, category)

    noise = fractal_noise(width, height, seed, category)
    fine = fractal_noise(width, height, seed ^ 0xA5A55A5A, "ui")

    luma = np.clip(
        rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114,
        0.0,
        1.0,
    )
    gy, gx = np.gradient(luma)
    normal_light = np.clip(1.0 - gx * 2.4 - gy * 1.6, 0.55, 1.45)
    material = 0.84 + noise * 0.28 + fine * 0.10
    shade = normal_light * material

    if category in {"room", "scene", "night_scene"}:
        yy, xx = np.mgrid[0:height, 0:width]
        cx = (xx / max(1, width - 1) - 0.5) ** 2
        cy = (yy / max(1, height - 1) - 0.5) ** 2
        vignette = np.clip(1.12 - (cx + cy) * 0.65, 0.72, 1.12)
        shade *= vignette
    elif category in {"character", "face", "cutin"}:
        shade = 0.92 + (shade - 0.92) * 0.65
    elif category == "ui":
        shade = 0.96 + (shade - 0.96) * 0.35

    rgb = np.clip(rgb * shade[..., None], 0.0, 1.0)

    if category == "food_object":
        spec = np.clip((noise - 0.63) * 2.8, 0.0, 1.0)
        rgb = np.clip(rgb + spec[..., None] * np.array([0.14, 0.10, 0.05]), 0.0, 1.0)
    elif category in {"room", "scene"}:
        spec = np.clip((fine - 0.70) * 1.8, 0.0, 1.0)
        rgb = np.clip(rgb + spec[..., None] * 0.06, 0.0, 1.0)

    edge_image = rgba.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.8))
    edge = np.asarray(edge_image, dtype=np.float32) / 255.0
    edge_strength = 0.09 if category != "ui" else 0.04
    rgb = np.clip(rgb * (1.0 - edge[..., None] * edge_strength), 0.0, 1.0)

    out = np.zeros((height, width, 4), dtype=np.uint8)
    out[..., :3] = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(alpha[..., 0] * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def safe_real_world_rgba(image: Image.Image, category: str, rel: str) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    if width <= 2 or height <= 2:
        return rgba

    # Text, logos, tiny UI glyphs, and icon sprites should stay mostly intact.
    lower = rel.replace("\\", "/").lower()
    area = width * height
    conservative = (
        category == "ui"
        or "/gamelogo/" in lower
        or "/glyphs/" in lower
        or "/icons/" in lower
        or area <= 48 * 48
    )

    scale = 3 if max(width, height) <= 512 else 2
    up = rgba.resize((width * scale, height * scale), Image.Resampling.LANCZOS)
    up = up.filter(ImageFilter.SMOOTH_MORE)
    up = up.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))
    smooth = up.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")

    original = np.asarray(rgba, dtype=np.float32) / 255.0
    smoothed = np.asarray(smooth, dtype=np.float32) / 255.0
    alpha = original[..., 3:4]
    original_rgb = original[..., :3]
    smooth_rgb = smoothed[..., :3]

    if conservative:
        blend = 0.18
        grain_amount = 0.012
    elif category in {"character", "face", "cutin"}:
        blend = 0.38
        grain_amount = 0.020
    elif category in {"room", "scene", "night_scene", "food_object"}:
        blend = 0.46
        grain_amount = 0.028
    else:
        blend = 0.30
        grain_amount = 0.018

    rgb = original_rgb * (1.0 - blend) + smooth_rgb * blend
    rgb = category_grade(rgb, category)

    seed = seed_for(rel)
    fine = fractal_noise(width, height, seed ^ 0xBAD5AFE, "ui")
    coarse = fractal_noise(width, height, seed ^ 0xC0FFEE, category)
    texture = (fine - 0.5) * grain_amount

    if category in {"room", "scene", "night_scene", "food_object"} and not conservative:
        # Add mild photographic surface variation but keep original luminance and scene layout.
        luma = np.clip(
            original_rgb[..., 0] * 0.299
            + original_rgb[..., 1] * 0.587
            + original_rgb[..., 2] * 0.114,
            0.0,
            1.0,
        )
        detail_mask = np.clip(0.25 + luma * 0.75, 0.0, 1.0)
        warm = np.array([1.035, 1.010, 0.970], dtype=np.float32)
        rgb = np.clip(rgb * warm.reshape(1, 1, 3), 0.0, 1.0)
        rgb = np.clip(rgb + ((coarse - 0.5) * grain_amount * 1.4 * detail_mask)[..., None], 0.0, 1.0)
    elif category in {"character", "face", "cutin"} and not conservative:
        # Smooth skin/clothing blocks a little, but preserve the original drawing.
        rgb = np.clip(rgb + texture[..., None] * np.array([1.0, 0.82, 0.72]), 0.0, 1.0)
    else:
        rgb = np.clip(rgb + texture[..., None], 0.0, 1.0)

    # Preserve ink/edge readability. This is the opposite of the previous corrupted pass:
    # lines from the original image remain the dominant structure.
    edge = np.asarray(
        rgba.convert("L")
        .filter(ImageFilter.FIND_EDGES)
        .filter(ImageFilter.GaussianBlur(0.55 if conservative else 0.85)),
        dtype=np.float32,
    ) / 255.0
    edge_strength = 0.05 if conservative else 0.09
    rgb = np.clip(rgb * (1.0 - edge[..., None] * edge_strength), 0.0, 1.0)

    out = np.zeros((height, width, 4), dtype=np.uint8)
    out[..., :3] = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(alpha[..., 0] * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def write_analysis(output_root: Path, infos: list[TextureInfo]) -> None:
    category_counts = Counter(info.category for info in infos)
    dim_counts = Counter(info.size for info in infos)
    alpha_counts = Counter("alpha" if info.has_alpha else "opaque" for info in infos)

    manifest = output_root / "_manifest.tsv"
    with manifest.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("path\twidth\theight\tcategory\talpha\tmode\n")
        for info in infos:
            handle.write(
                f"{info.rel}\t{info.size[0]}\t{info.size[1]}\t{info.category}\t"
                f"{int(info.has_alpha)}\t{info.mode}\n"
            )

    ai_manifest = output_root / "_AI_PROMPT_MANIFEST.tsv"
    with ai_manifest.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("path\twidth\theight\tcategory\tprompt\n")
        for info in infos:
            handle.write(
                f"{info.rel}\t{info.size[0]}\t{info.size[1]}\t{info.category}\t"
                f"{ai_prompt_for(info)}\n"
            )

    lines = [
        "# SAEKO Real World Experiment",
        "",
        "Generated local experimental texture pack.",
        "Do not redistribute this folder if it was generated from a local game install.",
        "",
        f"Total PNG files: {len(infos)}",
        "",
        "## Categories",
    ]
    for category, count in category_counts.most_common():
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Alpha", ""])
    for kind, count in alpha_counts.most_common():
        lines.append(f"- {kind}: {count}")
    lines.extend(["", "## Common dimensions", ""])
    for (width, height), count in dim_counts.most_common(20):
        lines.append(f"- {width}x{height}: {count}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Every output PNG keeps the original file name, dimensions, and alpha channel.",
            "- This safe pass preserves original composition, dimensions, alpha, text, and outlines.",
            "- It uses mild smoothing, color grading, and subtle photographic grain.",
            "- It avoids the older aggressive material replacement that made textures look corrupted.",
            "- This is not a true AI photoreal remake. Use the manifest as a base for manual/AI work.",
            "- `_AI_PROMPT_MANIFEST.tsv` contains per-texture image-to-image prompts for a future real AI pass.",
        ]
    )
    (output_root / "_README_REAL_WORLD_EXPERIMENT.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def ai_prompt_for(info: TextureInfo) -> str:
    common = (
        "image-to-image; preserve exact crop, silhouette, object positions, alpha mask, "
        "transparent areas, and readable UI/text; no new objects; no watermark"
    )
    category_prompt = {
        "ui": "clean real-world tactile game UI material, subtle glass/ink surface, keep labels and borders unchanged",
        "effect": "realistic light/smoke/particle effect, preserve shape and timing frame",
        "face": "photoreal close-up face material study, natural skin texture, preserve expression and line placement",
        "character": "photoreal character sprite pass, natural skin, cloth fibers, hair strands, preserve pose and expression",
        "food_object": "real-world tabletop macro photo material, food/cake/hand/object texture, preserve composition",
        "room": "photoreal dark room/desk/drawer environment, wood grain and low interior light, preserve perspective",
        "scene": "photoreal cinematic scene background, realistic materials and lighting, preserve composition",
        "night_scene": "photoreal night scene, low-key lighting, realistic dark surfaces, preserve composition",
        "cutin": "photoreal cut-in illustration pass, preserve drawing silhouette, expression, frame and alpha",
        "misc": "photoreal material pass, preserve original composition and transparency",
    }.get(info.category, "photoreal material pass, preserve original composition and transparency")
    return f"{category_prompt}; {common}"


def create_pack(default_root: Path, output_root: Path, overwrite: bool, max_files: int | None) -> None:
    infos = collect_infos(default_root)
    if overwrite and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    failed = 0
    for index, info in enumerate(infos, start=1):
        if max_files is not None and written >= max_files:
            break
        src = default_root / info.rel
        dst = output_root / info.rel
        if dst.exists() and not overwrite:
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(src) as image:
                out = safe_real_world_rgba(image, info.category, info.rel)
                out.save(dst, "PNG", optimize=True)
            written += 1
            if written == 1 or written % 250 == 0:
                print(f"[{written}/{len(infos)}] {info.rel}")
        except Exception as err:
            failed += 1
            print(f"FAILED {info.rel}: {err}")

    marker = output_root / "_SAEKO_REAL_WORLD_EXPERIMENT.txt"
    marker.write_text(
        "SAEKO real_world_safe_experiment texture pack.\n"
        "Generated locally from texture_packs/default.\n"
        "Keep this local unless you have rights to redistribute the source game assets.\n",
        encoding="utf-8",
    )
    write_analysis(output_root, infos)
    print(f"Done. written={written} skipped={skipped} failed={failed}")
    print(f"Output: {output_root}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an experimental de-pixelated real-world style SAEKO texture pack."
    )
    parser.add_argument("--default-root", help="Path to texture_packs/default.")
    parser.add_argument(
        "--output-root",
        help="Output pack folder. Defaults to sibling real_world_safe_experiment next to default.",
    )
    parser.add_argument("--pack-name", default=PACK_NAME)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--max-files", type=int, help="Debug limit.")
    args = parser.parse_args()

    default_root = resolve_default_root(args.default_root)
    output_root = (
        Path(args.output_root).resolve()
        if args.output_root
        else default_root.parent / args.pack_name
    )
    create_pack(default_root, output_root, args.overwrite, args.max_files)


if __name__ == "__main__":
    main()
