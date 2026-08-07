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
