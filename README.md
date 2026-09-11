# ASBAR-Parser
Parses [Android SMS Backup and Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore) `.xml` files to extract media and format the text messages.

Creates a "text message bubble" styled format.

## Requirements

This module requires `ffmpeg` to be installed and available in your system's PATH.
Playwright's Chromium browser must also be installed before generating PDFs.

```bash
asbar install-browsers
```

If running the package directly with `uv`, use:

```bash
uv tool run --from asbar-parser asbar install-browsers
```

## Usage
Run `asbar` in the directory that has your Android SMS Backup and Restore `.xml` file(s), or provide the directory path as an argument.

```bash
asbar "input/directory"
```

Images are extracted into the output `media/` directory twice: the original
asset is preserved, while a resized/compressed derivative is used by the HTML
and PDF. Derivatives default to a maximum dimension of 800 pixels and JPEG
quality 75. For example, an image may produce `*-original.png` and
`*-compressed.jpg`. PDF-level Ghostscript compression is no longer performed;
the previously supported `--no-compress` flag is accepted for compatibility but
is no longer needed.

## Generate test data

A dependency-free fixture generator is included for creating a small Android
SMS Backup and Restore-compatible XML file. It uses reserved `555` phone
numbers, deterministic lorem ipsum-style messages, and embedded PNG MMS
images:

```bash
python scripts/generate_fake_chats.py --output fake-chats.xml
asbar .
```

The generator accepts `--conversations`, `--messages`, `--images`,
`--image-width`, `--image-height`, and `--seed` options. It creates four
640x400 images per conversation by default; use `--images 10` to attach an
image to every message in a ten-message conversation. For example,
`--conversations 3 --messages 25 --images 8 --image-width 1200 --image-height 800 --seed 7`
creates a larger, repeatable fixture. The seed affects message text and image
colors, not the number or dimensions of images. PNG images are embedded in the
XML, so no media files need to be prepared separately. The parser preserves
each original image next to its `-compressed` presentation copy.
