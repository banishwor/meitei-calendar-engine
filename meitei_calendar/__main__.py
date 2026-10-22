"""CLI: python -m meitei_calendar YEAR [--rich] [--out PATH]

Writes calendar_YEAR.json in the PWA format (default) or, with --rich,
the full records including intercalary flags and merged (pair) tithis.
Generation takes a minute or two per year (full ephemeris scan)."""
import argparse, json, sys

from .generator import generate_year, to_pwa


def main(argv=None):
    ap = argparse.ArgumentParser(prog='meitei_calendar')
    ap.add_argument('year', type=int)
    ap.add_argument('--rich', action='store_true',
                    help='full records instead of PWA format')
    ap.add_argument('--out', help='output path (default calendar_YEAR.json)')
    a = ap.parse_args(argv)

    records = generate_year(a.year)
    payload = records if a.rich else to_pwa(records)
    out = a.out or f'calendar_{a.year}.json'
    with open(out, 'w') as f:
        json.dump(payload, f, indent=1)
    pairs = sum(1 for r in records if r['merged'])
    adhik = sorted({r['month'] for r in records if r['intercalary']})
    print(f'{a.year}: {len(records)} days, {pairs} pair days, '
          f'adhik months: {adhik or "none"} -> {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
