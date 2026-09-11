# ASBAR-Parser
Parses [Android SMS Backup and Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore) `.xml` files to extract media and format the text messages.

Creates a "text message bubble" styled format.

## Requirements

This module requires `ffmpeg` to be installed and available in your system's PATH.
Playwright's Chromium browser must also be installed before generating PDFs.

`ghostscript` (`gs`) is optional: when available, a second
`<name>-compressed.pdf` is also generated next to each PDF, with embedded
images downsampled and re-encoded (150 dpi, medium JPEG quality) like
Acrobat's "Compress PDF" action. Without it, the full-size PDF is still
produced and compression is skipped with a notice.

```bash
brew install ghostscript
```

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
and PDF. For example, an image may produce `*-original.png` and
`*-compressed.jpg`. PDF compression runs through Ghostscript by default. To
generate the regular PDF without spending time creating the optional
compressed copy, use:

```bash
asbar --no-compress "input/directory"
```

## Generate test data

A dependency-free fixture generator is included for creating a small Android
SMS Backup and Restore-compatible XML file. It uses reserved `555` phone
numbers, deterministic lorem ipsum-style messages, and embedded PNG MMS
images:

```bash
python scripts/generate_fake_chats.py --output fake-chats.xml
asbar --no-compress .
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
