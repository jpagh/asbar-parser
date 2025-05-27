# ASBAR-Parser
Parses [Android SMS Backup and Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore) .xml files to extract media and format the text messages.

Creates a "text message bubble" styled format.

## Requirements

This Python script requires the following font, programs, and modules:
 - Arial-Emoji.ttf
    - `included`
 - wkhtmltopdf.exe
    - `"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"`
 - ffmpeg.exe
    - `"C:\Program Files\ffmpeg\bin\ffmpeg.exe"`
 - just-heic
    - `pip install just-heic`
 - lxml
    - `pip install lxml`
 - pdfkit
    - `pip install pdfkit`

## Usage
```bash
asbar "input/directory"
```
