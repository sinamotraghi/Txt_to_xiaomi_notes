# Txt_to_xiaomi_notes
# Samsung Notes → Xiaomi Notes Importer

A small Windows/Python script that takes a folder of exported `.txt` notes
(zipped) and imports them into **Xiaomi Notes** on an Android phone, one by
one, via ADB and an Android share (`ACTION_SEND`) intent.

Each note is sent to the phone and Xiaomi Notes opens with the text
pre-filled. You confirm/save it on the phone (Xiaomi Notes may show a save
screen depending on your MIUI version).

## Prerequisites

- **Windows** (the script shells out to `adb.exe` using Windows-style paths)
- **Python 3** (no third-party packages required — only the standard library)
- **Android Platform Tools (ADB)**
  - Download from the [official Android developer site](https://developer.android.com/tools/releases/platform-tools)
  - Place `adb.exe` **in the same folder as the script**. The script always
    runs the `adb.exe` sitting next to it, to avoid PATH issues on Windows.
- **A Xiaomi phone with:**
  - **USB debugging** enabled (Settings → About phone → tap "MIUI version"
    7 times to unlock Developer options → Developer options → USB debugging)
  - The phone connected via USB, with the **RSA/USB debugging prompt
    accepted** on the phone screen
  - **Only one** Android device connected at a time (the script refuses to
    run if it detects more than one)
  - The **Xiaomi Notes** app installed (package `com.miui.notes`)
- Your exported notes as **`.txt` files inside a single `.zip` archive**
  (e.g. `texts.zip`). The script searches the zip recursively for any
  `*.txt` files.

## Setup

1. Download/clone this repo.
2. Download `adb.exe` (and its companion DLLs) from Android Platform Tools
   and copy them into the same folder as `import_xiaomi_notes.py`.
3. Connect your Xiaomi phone via USB, enable USB debugging, and accept the
   RSA prompt.
4. Verify the connection:
   ```
   adb devices
   ```
   You should see your device listed with `device` next to its serial
   number (not `unauthorized` or `offline`).

## Usage

**Always test with a single note first:**

```
python import_xiaomi_notes.py texts.zip --limit 1
```

If that note shows up correctly in Xiaomi Notes, run it on everything:

```
python import_xiaomi_notes.py texts.zip
```

### Options

| Option | Default | Description |
|---|---|---|
| `zip` | *(required)* | Path to the `.zip` file containing your `.txt` notes |
| `--limit N` | `0` (no limit) | Only import the first `N` files — use `1` for testing |
| `--pause SECONDS` | `2.0` | Delay between sending each note, so the phone/app has time to catch up |

### What happens for each note

1. The filename (with underscores turned into spaces) is used as a title
   line at the top of the note.
2. The full note text is sent to the phone as an `ACTION_SEND` intent
   targeting Xiaomi Notes.
3. Xiaomi Notes opens with the content filled in — **save it manually on
   the phone** if a save/confirmation screen appears.
4. The script waits `--pause` seconds, then moves to the next file.

Your original `.txt` files and the zip are never modified — the script only
reads from them.

## Troubleshooting

- **"No ADB device found"** — run `adb devices` yourself first; make sure
  USB debugging is on and the RSA prompt was accepted.
- **"More than one Android device is connected"** — disconnect other
  phones/emulators, or set `ANDROID_SERIAL` if you need to target a
  specific device.
- **"Could not launch Xiaomi Notes share receiver"** — usually means the
  `am start` intent failed on the phone. Try running the intent manually
  to see the phone's actual error:
  ```
  adb shell am start -a android.intent.action.SEND -t text/plain --es android.intent.extra.TEXT test -p com.miui.notes
  ```
- If notes are missing content or arriving truncated, it may be worth
  checking `adb shell am start ... --es android.intent.extra.TEXT` command
  length limits for very long notes.

## Notes on how this works

The script connects to `adb.exe` next to it and drives everything through
`adb shell am start`. Text is quoted with Python's `shlex.quote()` before
being sent, because `adb shell` flattens all arguments into one string that
gets re-parsed by the phone's shell — without quoting, notes containing
spaces or special characters would get corrupted or split incorrectly.
