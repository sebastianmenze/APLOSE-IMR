#!/usr/bin/env python3
"""
Copy APLOSE dataset snippets (WAV + PNG + JSON) whose start time falls
within a buffer window around full-hour marks.

Examples
--------
# Dry-run: every hour, ±40 s buffer
python copy_hourly_snippets.py /data/src /data/dst --dry-run

# Copy snippets near 00:00, 01:00, 02:00 ... with ±40 s window
python copy_hourly_snippets.py /data/src /data/dst

# Copy snippets near 00:00, 02:00, 04:00 ... (every 2 h) with ±60 s window
python copy_hourly_snippets.py /data/src /data/dst --interval 2 --buffer 60
"""

import argparse
import glob
import os
import re
import shutil
import sys
from datetime import datetime

DATETIME_RE = re.compile(r"(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})")
DATETIME_FMT = "%Y_%m_%d_%H_%M_%S"


def parse_datetime(path: str) -> datetime | None:
    m = DATETIME_RE.search(os.path.basename(path))
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), DATETIME_FMT)
    except ValueError:
        return None


def near_hour_mark(dt: datetime, interval_h: int, buffer_s: float) -> bool:
    """True if dt is within buffer_s seconds of any (interval_h)-hourly mark."""
    seconds_since_midnight = dt.hour * 3600 + dt.minute * 60 + dt.second
    interval_s = interval_h * 3600
    remainder = seconds_since_midnight % interval_s        # distance past last mark
    distance = min(remainder, interval_s - remainder)      # distance to nearest mark
    return distance <= buffer_s


def associated_files(wav_path: str) -> list[str]:
    """Return the WAV file plus any matching PNG / JSON spectrogram files."""
    stem = os.path.splitext(wav_path)[0]
    files = [wav_path]
    files += glob.glob(stem + "_fft*_data.png")
    files += glob.glob(stem + "_fft*_data.json")
    return files


def run(src: str, dst: str, interval_h: int, buffer_s: float, dry_run: bool) -> None:
    wav_files = sorted(glob.glob(os.path.join(src, "**", "*.wav"), recursive=True))
    if not wav_files:
        print(f"No WAV files found in {src}")
        return

    snippet_count = 0
    file_count = 0

    for wav in wav_files:
        dt = parse_datetime(wav)
        if dt is None:
            print(f"[SKIP] No datetime in filename: {os.path.basename(wav)}")
            continue

        if not near_hour_mark(dt, interval_h, buffer_s):
            continue

        files = associated_files(wav)
        snippet_count += 1

        # Mirror relative sub-directory structure into dst
        rel_dir = os.path.relpath(os.path.dirname(wav), src)
        out_dir = os.path.normpath(os.path.join(dst, rel_dir))

        tag = "DRY RUN" if dry_run else "COPY"
        print(f"\n[{tag}] {dt:%Y-%m-%d %H:%M:%S}  →  {os.path.basename(wav)}")
        for f in files:
            print(f"  {os.path.basename(f)}  ({os.path.getsize(f) / 1024:.1f} KB)")
            if not dry_run:
                os.makedirs(out_dir, exist_ok=True)
                shutil.copy2(f, os.path.join(out_dir, os.path.basename(f)))
            file_count += 1

    verb = "Would copy" if dry_run else "Copied"
    print(f"\n{verb} {file_count} file(s) from {snippet_count} matching snippet(s).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy APLOSE snippets near full-hour marks."
    )
    parser.add_argument("src", help="Source APLOSE dataset folder")
    parser.add_argument("dst", help="Destination folder")
    parser.add_argument(
        "--interval", type=int, default=1, choices=[1, 2],
        help="Hour interval: 1 = every hour, 2 = every 2 h (default: 1)",
    )
    parser.add_argument(
        "--buffer", type=float, default=40.0,
        help="Buffer in seconds around the hour mark (default: 40)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview without copying anything",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.src):
        print(f"Error: '{args.src}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Source      : {args.src}")
    print(f"Destination : {args.dst}")
    print(f"Interval    : every {args.interval} h")
    print(f"Buffer      : ±{args.buffer} s around hour mark")
    print(f"Mode        : {'DRY RUN' if args.dry_run else 'LIVE COPY'}\n")

    run(args.src, args.dst, args.interval, args.buffer, args.dry_run)


if __name__ == "__main__":
    main()
