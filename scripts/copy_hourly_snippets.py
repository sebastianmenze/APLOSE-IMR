#!/usr/bin/env python3
"""
Copy APLOSE dataset snippets (WAV + PNG + JSON) whose start time falls
within a buffer window around periodic time marks.

The marks are defined by a start time (HH:MM) and an interval in hours.
Example: --start 00:30 --interval 2  →  marks at 00:30, 02:30, 04:30, …

Examples
--------
# Default: marks every 1 h from 00:00 (i.e. 00:00, 01:00, …), ±40 s buffer
python copy_hourly_snippets.py /data/src /data/dst --dry-run

# Marks at 00:30, 01:30, 02:30 … with ±40 s buffer
python copy_hourly_snippets.py /data/src /data/dst --start 00:30

# Marks at 00:30, 02:30, 04:30 … with ±60 s buffer
python copy_hourly_snippets.py /data/src /data/dst --start 00:30 --interval 2 --buffer 60
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


def parse_start_time(value: str) -> int:
    """Parse 'HH:MM' into total seconds since midnight."""
    try:
        h, m = value.split(":")
        return int(h) * 3600 + int(m) * 60
    except (ValueError, AttributeError):
        raise argparse.ArgumentTypeError(f"Invalid time format '{value}', expected HH:MM")


def near_mark(dt: datetime, start_s: int, interval_s: int, buffer_s: float) -> bool:
    """True if dt is within buffer_s seconds of any periodic mark.

    Marks occur at  start_s, start_s + interval_s, start_s + 2*interval_s, …
    (wrapping around midnight every 24 h).
    """
    seconds_since_midnight = dt.hour * 3600 + dt.minute * 60 + dt.second
    # Shift so that marks land on multiples of interval_s
    shifted = (seconds_since_midnight - start_s) % 86400
    remainder = shifted % interval_s          # seconds past the last mark
    distance = min(remainder, interval_s - remainder)  # distance to nearest mark
    return distance <= buffer_s


def associated_files(wav_path: str) -> list[str]:
    """Return the WAV file plus any matching PNG / JSON spectrogram files."""
    stem = os.path.splitext(wav_path)[0]
    files = [wav_path]
    files += glob.glob(stem + "_fft*_data.png")
    files += glob.glob(stem + "_fft*_data.json")
    return files


def run(src: str, dst: str, start_s: int, interval_h: float, buffer_s: float, dry_run: bool) -> None:
    interval_s = int(interval_h * 3600)
    wav_files = sorted(glob.glob(os.path.join(src, "**", "*.wav"), recursive=True))
    if not wav_files:
        print(f"No WAV files found in {src}")
        return

    snippet_count = 0
    file_count = 0

    print(wav_files)

    for wav in wav_files:
        dt = parse_datetime(wav)
        if dt is None:
            print(f"[SKIP] No datetime in filename: {os.path.basename(wav)}")
            continue

        if not near_mark(dt, start_s, interval_s, buffer_s):
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
        description="Copy APLOSE snippets near periodic time marks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Every hour from 00:00 (default):\n"
            "    %(prog)s src/ dst/\n\n"
            "  Marks at 00:30, 01:30, 02:30 …:\n"
            "    %(prog)s src/ dst/ --start 00:30\n\n"
            "  Marks at 00:30, 02:30, 04:30 … with ±60 s buffer:\n"
            "    %(prog)s src/ dst/ --start 00:30 --interval 2 --buffer 60\n"
        ),
    )
    parser.add_argument("src", help="Source APLOSE dataset folder")
    parser.add_argument("dst", help="Destination folder")
    parser.add_argument(
        "--start", default="00:00", metavar="HH:MM",
        help="First mark time of day, e.g. 00:30 (default: 00:00)",
    )
    parser.add_argument(
        "--interval", type=float, default=1.0,
        help="Interval between marks in hours, e.g. 2 or 0.5 (default: 1)",
    )
    parser.add_argument(
        "--buffer", type=float, default=40.0,
        help="Buffer in seconds either side of each mark (default: 40)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview without copying anything",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.src):
        print(f"Error: '{args.src}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    start_s = parse_start_time(args.start)
    interval_s = int(args.interval * 3600)

    # Build a human-readable list of the first few marks for confirmation
    marks = []
    t = start_s
    while len(marks) < 6:
        marks.append(f"{t // 3600:02d}:{(t % 3600) // 60:02d}")
        t = (t + interval_s) % 86400
    marks_preview = ", ".join(marks) + ", …"

    print(f"Source      : {args.src}")
    print(f"Destination : {args.dst}")
    print(f"Marks       : {marks_preview}")
    print(f"Interval    : every {args.interval} h")
    print(f"Buffer      : ±{args.buffer} s around each mark")
    print(f"Mode        : {'DRY RUN' if args.dry_run else 'LIVE COPY'}\n")

    run(args.src, args.dst, start_s, args.interval, args.buffer, args.dry_run)


if __name__ == "__main__":
    main()
