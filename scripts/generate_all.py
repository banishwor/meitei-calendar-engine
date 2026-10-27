#!/usr/bin/env python3
"""Generate pre-computed calendar JSON files for a range of years.

Generates one PWA/Android-format file per year:

    data/calendar_<year>.json

Each file is a list of {"gregorian", "month", "day"} records, where a
pair day carries a 2-element "day" list, e.g.:

    [
      {"gregorian": "2020-01-01", "month": "WAKCHING", "day": 6},
      {"gregorian": "2026-03-19", "month": "SAJIBU", "day": [30, 1]}
    ]

These files are committed to the repository and served to the
Manipuri Calendar Android app and PWA on demand via GitHub Raw and
the jsDelivr CDN (see README.md, "Hosted calendar data").

Usage:
    python scripts/generate_all.py                  # 2020-2035 -> data/
    python scripts/generate_all.py --start 2024 --end 2030
    python scripts/generate_all.py --years 2026 2027
    python scripts/generate_all.py --skip-existing  # resume an interrupted run

Generation takes a minute or two per year (full ephemeris scan).
"""
import argparse
import json
import sys
from pathlib import Path

# Allow running from the repository root without installing the package.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from meitei_calendar import generate_year          # noqa: E402
from meitei_calendar.generator import to_pwa       # noqa: E402

DEFAULT_START = 2020
DEFAULT_END = 2035


def generate_one(year: int, out_dir: Path) -> Path:
    records = generate_year(year)
    payload = to_pwa(records)
    out_path = out_dir / f"calendar_{year}.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=1)
        f.write("\n")
    pairs = sum(1 for r in payload if isinstance(r["day"], list))
    print(f"{year}: {len(payload)} days, {pairs} pair days -> {out_path}",
          flush=True)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="generate_all",
        description="Generate data/calendar_<year>.json for a range of years.")
    ap.add_argument("--start", type=int, default=DEFAULT_START,
                    help=f"first year (default {DEFAULT_START})")
    ap.add_argument("--end", type=int, default=DEFAULT_END,
                    help=f"last year, inclusive (default {DEFAULT_END})")
    ap.add_argument("--years", type=int, nargs="*", default=None,
                    help="explicit years to generate (overrides --start/--end)")
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "data"),
                    help="output directory (default <repo>/data)")
    ap.add_argument("--skip-existing", action="store_true",
                    help="skip years whose output file already exists")
    a = ap.parse_args(argv)

    years = a.years if a.years else list(range(a.start, a.end + 1))
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for year in years:
        out_path = out_dir / f"calendar_{year}.json"
        if a.skip_existing and out_path.exists():
            print(f"{year}: already exists, skipping -> {out_path}",
                  flush=True)
            continue
        generate_one(year, out_dir)

    print(f"Done: {len(years)} year(s) in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
