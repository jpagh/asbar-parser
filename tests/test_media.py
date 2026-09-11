import base64
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import lxml.etree as etree
from PIL import Image

from asbar.main import transform
from asbar.media import prepare_image_parts, prepare_video_thumbnails


class MediaPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        self.media_directory = Path(self.temp_directory.name) / "media"

    def tearDown(self):
        self.temp_directory.cleanup()

    @staticmethod
    def image_bytes(mode, size, image_format):
        color = (25, 100, 200, 128) if mode == "RGBA" else (25, 100, 200)
        image = Image.new(mode, size, color)
        output = BytesIO()
        image.save(output, format=image_format)
        return output.getvalue()

    @staticmethod
    def message_tree(parts, message_type="mms"):
        root = etree.Element("smses")
        if message_type == "mms":
            message = etree.SubElement(
                root,
                "mms",
                {
                    "date": "1736931600000",
                    "msg_box": "1",
                    "address": "+12025550101",
                    "contact_name": "Fixture Contact",
                    "readable_date": "Jan 15, 2025 09:00:00",
                },
            )
            parts_element = etree.SubElement(message, "parts")
        else:
            parts_element = root

        for sequence, content_type, data in parts:
            etree.SubElement(
                parts_element,
                "part",
                {
                    "seq": str(sequence),
                    "ct": content_type,
                    "cl": "source.bin",
                    "data": base64.b64encode(data).decode("ascii"),
                },
            )
        return etree.ElementTree(root)

    def test_image_parts_keep_originals_and_create_smaller_derivatives(self):
        original_png = self.image_bytes("RGB", (2400, 1200), "PNG")
        original_rgba = self.image_bytes("RGBA", (500, 300), "PNG")
        parsed_xml = self.message_tree(
            [
                (0, "image/png", original_png),
                (1, "image/png", original_rgba),
            ]
        )

        assets = prepare_image_parts(
            parsed_xml, self.media_directory, max_dimension=1600, jpeg_quality=80
        )

        self.assertEqual(len(assets), 2)
        parts = list(parsed_xml.iter("part"))
        self.assertEqual(
            (
                parts[0].get("asbar_original_filename"),
                parts[0].get("asbar_compressed_filename"),
            ),
            (assets[0].original_filename, assets[0].compressed_filename),
        )
        self.assertEqual(
            (
                parts[1].get("asbar_original_filename"),
                parts[1].get("asbar_compressed_filename"),
            ),
            (assets[1].original_filename, assets[1].compressed_filename),
        )

        original_path = self.media_directory / assets[0].original_filename
        compressed_path = self.media_directory / assets[0].compressed_filename
        self.assertEqual(original_path.read_bytes(), original_png)
        self.assertEqual(compressed_path.suffix, ".jpg")
        self.assertLess(compressed_path.stat().st_size, original_path.stat().st_size)
        with Image.open(compressed_path) as compressed:
            self.assertEqual(compressed.size, (1600, 800))

        transparent_path = self.media_directory / assets[1].compressed_filename
        self.assertEqual(transparent_path.suffix, ".png")
        with Image.open(transparent_path) as compressed:
            self.assertEqual(compressed.size, (500, 300))
            self.assertEqual(compressed.mode, "RGBA")

    def test_html_references_every_compressed_image_not_the_originals(self):
        first_image = self.image_bytes("RGB", (800, 400), "PNG")
        second_image = self.image_bytes("RGB", (600, 300), "PNG")
        parsed_xml = self.message_tree(
            [
                (0, "image/png", first_image),
                (1, "image/png", second_image),
            ]
        )
        assets = prepare_image_parts(parsed_xml, self.media_directory)
        html_path = Path(self.temp_directory.name) / "messages.html"

        transform(
            parsed_xml,
            "src/asbar/__assets__/asbar.xslt",
            str(html_path),
        )
        html = html_path.read_text(encoding="utf-8")

        for asset in assets:
            self.assertIn(f"media/{asset.compressed_filename}", html)
            self.assertNotIn(asset.original_filename, html)
        self.assertNotIn("data:image/", html)
        self.assertEqual(html.count("<img"), 2)

    def test_video_thumbnail_keeps_original_and_creates_derivative(self):
        original_thumbnail = self.image_bytes("RGB", (1920, 1080), "JPEG")
        self.media_directory.mkdir(parents=True)
        original_path = self.media_directory / "clip.mp4.jpg"
        original_path.write_bytes(original_thumbnail)
        parsed_xml = self.message_tree([], message_type="video")
        part = etree.SubElement(
            parsed_xml.getroot(),
            "part",
            {"ct": "video/mp4", "cl": "clip.mp4"},
        )

        assets = prepare_video_thumbnails(parsed_xml, self.media_directory)

        self.assertEqual(len(assets), 1)
        self.assertEqual(original_path.read_bytes(), original_thumbnail)
        compressed_path = self.media_directory / assets[0].compressed_filename
        self.assertEqual(assets[0].original_filename, "clip.mp4.jpg")
        self.assertEqual(assets[0].compressed_filename, "clip.mp4-compressed.jpg")
        self.assertTrue(compressed_path.is_file())
        self.assertEqual(
            part.get("asbar_compressed_filename"), assets[0].compressed_filename
        )
        with Image.open(compressed_path) as compressed:
            self.assertEqual(compressed.size, (1600, 900))


if __name__ == "__main__":
    unittest.main()
