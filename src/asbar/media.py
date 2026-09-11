"""Extract and optimize image assets used by generated message documents."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from just_heic import convert_file as convert_heic
from PIL import Image, ImageOps

DEFAULT_IMAGE_MAX_DIMENSION = 1600
DEFAULT_JPEG_QUALITY = 85


@dataclass(frozen=True, slots=True)
class ImageAsset:
    """The original and presentation filenames for one image asset."""

    original_filename: str
    compressed_filename: str


def _content_type(part: Any) -> str:
    return (part.get("ct") or "").split(";", 1)[0].strip().lower()


def _source_extension(content_type: str) -> str:
    subtype = content_type.partition("/")[2]
    extension = {
        "jpeg": "jpg",
        "jpg": "jpg",
        "heic": "heic",
    }.get(subtype, subtype)
    safe_extension = "".join(
        character for character in extension if character.isalnum()
    )
    return f".{safe_extension or 'img'}"


def _decode_image_data(part: Any) -> bytes:
    data = part.get("data")
    if not data or data == "null":
        raise ValueError("Image part is missing base64 data")
    try:
        return base64.b64decode("".join(data.split()), validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("Image part contains invalid base64 data") from error


def _read_image(source_path: Path) -> Image.Image:
    with Image.open(source_path) as source:
        image = ImageOps.exif_transpose(source)
        image.load()
        return image.copy()


def _read_image_for_processing(source_path: Path) -> Image.Image:
    if source_path.suffix.lower() != ".heic":
        return _read_image(source_path)

    with TemporaryDirectory(prefix="asbar-heic-") as temporary_directory:
        converted_path = Path(temporary_directory) / "converted.jpg"
        convert_heic(str(source_path), str(converted_path))
        return _read_image(converted_path)


def _has_transparency(image: Image.Image) -> bool:
    if image.mode in ("RGBA", "LA"):
        alpha_min = cast(tuple[int, int], image.getchannel("A").getextrema())[0]
        return alpha_min < 255
    if image.mode == "P" and "transparency" in image.info:
        alpha = image.convert("RGBA").getchannel("A")
        alpha_min = cast(tuple[int, int], alpha.getextrema())[0]
        return alpha_min < 255
    return False


def optimize_image_file(
    source_path: Path | str,
    output_directory: Path | str,
    output_stem: str,
    max_dimension: int = DEFAULT_IMAGE_MAX_DIMENSION,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> str:
    """Write an optimized derivative and return its filename.

    Images without transparency are written as optimized JPEGs. Images with
    transparency remain PNGs so the presentation copy does not change their
    appearance against the message bubble.
    """
    if max_dimension < 1:
        raise ValueError("max_dimension must be at least 1")
    if not 1 <= jpeg_quality <= 100:
        raise ValueError("jpeg_quality must be between 1 and 100")

    source_path = Path(source_path)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    image = _read_image_for_processing(source_path)
    try:
        image.thumbnail(
            (max_dimension, max_dimension),
            Image.Resampling.LANCZOS,
        )
        if _has_transparency(image):
            output_filename = f"{output_stem}.png"
            image.convert("RGBA").save(
                output_directory / output_filename,
                format="PNG",
                optimize=True,
                compress_level=9,
            )
        else:
            output_filename = f"{output_stem}.jpg"
            image.convert("RGB").save(
                output_directory / output_filename,
                format="JPEG",
                quality=jpeg_quality,
                optimize=True,
                progressive=True,
            )
    finally:
        image.close()

    return output_filename


def prepare_image_parts(
    parsed_xml: Any,
    output_directory: Path | str,
    max_dimension: int = DEFAULT_IMAGE_MAX_DIMENSION,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> list[ImageAsset]:
    """Extract every MMS image and attach its optimized filename metadata."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    assets = []

    for mms_number, mms in enumerate(parsed_xml.iter("mms"), start=1):
        parts = mms.find("parts")
        if parts is None:
            continue
        for part_number, part in enumerate(parts.findall("part")):
            content_type = _content_type(part)
            if not content_type.startswith("image/"):
                continue

            asset_stem = f"mms-{mms_number:06d}-part-{part_number:02d}"
            original_filename = (
                f"{asset_stem}-original{_source_extension(content_type)}"
            )
            original_path = output_directory / original_filename
            original_path.write_bytes(_decode_image_data(part))
            compressed_filename = optimize_image_file(
                original_path,
                output_directory,
                f"{asset_stem}-compressed",
                max_dimension=max_dimension,
                jpeg_quality=jpeg_quality,
            )

            part.set("asbar_original_filename", original_filename)
            part.set("asbar_compressed_filename", compressed_filename)
            assets.append(ImageAsset(original_filename, compressed_filename))

    return assets


def prepare_video_thumbnails(
    parsed_xml: Any,
    output_directory: Path | str,
    max_dimension: int = DEFAULT_IMAGE_MAX_DIMENSION,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> list[ImageAsset]:
    """Create optimized copies of thumbnails already extracted from videos."""
    output_directory = Path(output_directory)
    assets = []

    for part in parsed_xml.iter("part"):
        if _content_type(part) not in {"video/3gpp", "video/mp4"}:
            continue
        filename = part.get("cl")
        if not filename or filename == "null":
            continue

        original_filename = f"{filename}.jpg"
        original_path = output_directory / original_filename
        if not original_path.is_file():
            continue
        compressed_filename = optimize_image_file(
            original_path,
            output_directory,
            f"{filename}-compressed",
            max_dimension=max_dimension,
            jpeg_quality=jpeg_quality,
        )
        part.set("asbar_original_filename", original_filename)
        part.set("asbar_compressed_filename", compressed_filename)
        assets.append(ImageAsset(original_filename, compressed_filename))

    return assets
