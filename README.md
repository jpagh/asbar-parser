# ASBAR-Parser
Parses [Android SMS Backup and Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore) `.xml` files to extract media and format the text messages.

Creates a "text message bubble" styled format.

## Requirements

This module requires `ffmpeg` to be installed and available in your system's PATH.

## Usage
Run `asbar` in the directory that has your Android SMS Backup and Restore `.xml` file(s), or provide the directory path as an argument.

```bash
asbar "input/directory"
```
