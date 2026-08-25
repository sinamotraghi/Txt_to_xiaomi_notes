#!/usr/bin/env python3
# Samsung Notes TXT -> Xiaomi Notes importer
# Requires: Windows + Python 3 + Android platform-tools (ADB)
# IMPORTANT: Test with --limit 1 first.

import argparse, subprocess, time, zipfile, tempfile, os, re, shlex
from pathlib import Path

def run(*args, check=True):
    p = subprocess.run(
        args,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace"
    )
    if check and p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p

# Always use the adb.exe that sits next to this script.
# This avoids PATH/Windows quoting issues.
ADB = str(Path(__file__).resolve().parent / "adb.exe")

def adb(*args, check=True):
    if not os.path.isfile(ADB):
        raise FileNotFoundError(
            f"adb.exe not found next to this script: {ADB}"
        )
    return run(ADB, *args, check=check)

def connected():
    p = adb("devices", check=False)
    if p.returncode != 0:
        return []

    devices = []
    for line in p.stdout.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("list of devices"):
            continue

        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])

    return devices

def send_text_via_share(text):
    # ACTION_SEND -> Xiaomi Notes. This is the cleanest way if the installed
    # Xiaomi Notes version accepts shared plain text.
    #
    # NOTE: an earlier version of this function pushed the text to the phone
    # as base64 and decoded it into a temp file on /sdcard before sending the
    # intent. That temp file was never actually read by anything below - the
    # intent always used the `text` variable directly - so it was dead code.
    # It's also what was hanging: "adb shell sh -c '... > /sdcard/...'"
    # deadlocks on this device. Removed; we just send `text` directly.
    #
    # IMPORTANT: adb joins every "adb shell" argument into a single string
    # and re-parses it with /system/bin/sh on the device. So a `text` value
    # containing spaces/newlines/quotes gets split into multiple words by
    # the phone's shell unless we quote it ourselves (Python's own argv
    # handling on the Windows side doesn't help with this, since it happens
    # after adb reassembles the command remotely). shlex.quote() wraps the
    # value in POSIX-safe single quotes.
    try:
        quoted_text = shlex.quote(text)
        p = adb("shell", "am", "start",
                "-a", "android.intent.action.SEND",
                "-t", "text/plain",
                "--es", "android.intent.extra.TEXT", quoted_text,
                "-p", "com.miui.notes", check=False)
        return p.returncode == 0
    except Exception as e:
        print("  Error sending intent:", e)
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zip", help="Path to texts.zip")
    ap.add_argument("--limit", type=int, default=0,
                    help="Import only first N files (use 1 for testing)")
    ap.add_argument("--pause", type=float, default=2.0)
    args = ap.parse_args()

    try:
        devices = connected()
    except Exception as e:
        print("Could not start ADB:", e)
        return 2

    if not devices:
        print("No ADB device found.")
        print("Run .\\adb.exe devices to verify the phone is connected.")
        print("Enable USB debugging and accept the RSA prompt on the phone.")
        return 2

    if len(devices) > 1:
        print("More than one Android device is connected:", devices)
        print("Leave only the Xiaomi connected.")
        return 2

    print(f"ADB device: {devices[0]}")

    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(args.zip) as z:
            z.extractall(td)
        files = sorted(Path(td).rglob("*.txt"))
        if args.limit:
            files = files[:args.limit]

        print(f"Found {len(files)} TXT files.")
        for n, f in enumerate(files, 1):
            raw = f.read_text(encoding="utf-8-sig", errors="replace")
            title = f.stem.replace("_", " ")
            # Put title at top; Xiaomi Notes can use it as the first line if
            # its share receiver doesn't expose a separate title field.
            payload = title + "\n\n" + raw
            print(f"[{n}/{len(files)}] {f.name}")
            ok = send_text_via_share(payload)
            if not ok:
                print("  Could not launch Xiaomi Notes share receiver.")
                print("  Stop here; your TXT files are untouched.")
                return 1
            print("  Opened Xiaomi Notes. Save the note if a Save screen appears.")
            time.sleep(args.pause)

    print("Done.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
