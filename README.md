# meitei-calendar-engine

This library builds the **Meitei (Manipuri) calendar** for any year
from the real positions of the Sun and Moon. It does not copy any
printed table. Give it a year, and it works out the Meitei month and
thaban (day number) of every day — including leap months and pair
days. Past and future years both work.

```bash
pip install git+https://github.com/banishwor/meitei-calendar-engine
meitei-calendar 2028            # writes calendar_2028.json
meitei-calendar 2029 --rich     # full records: leap-month flags, merged days
```

```python
from meitei_calendar import generate_year

for day in generate_year(2029):
    print(day["gregorian"], day["month"], day["day"])
```

On first use, it downloads NASA's DE421 data file (~17 MB) once into
`~/.cache/meitei-calendar/` (override with `$MEITEI_CALENDAR_DATA`).
One year takes a minute or two to generate, because every day is
calculated, not looked up.

## The author's apps

- **Android:** [Manipuri Calendar](https://play.google.com/store/apps/details?id=com.manipurcalendar) on Google Play
- **Web (PWA):** [Manipuri Calendar — open the live app](https://banishwor.github.io/manipuri-calendar-pwa/)

## Output

Each day record: `gregorian` date, `month` (SAJIBU … LAMTA), `day`
(1–30). The default JSON matches the format used by the
[Manipuri Calendar PWA](https://github.com/banishwor/manipuri-calendar-pwa):
on pair days, `day` is a two-element list like `[30, 1]`. With `--rich`
you also get `intercalary` (the day belongs to a leap month) and
`merged` (extra lunar days merged into that civil day).

## Hosted calendar data

Pre-computed calendar files for **1950–2099** live in this repository's
[`data/`](data/) directory — one JSON file per Gregorian year, in the
PWA/Android format described under [Output](#output) above:

```
data/calendar_1950.json
data/calendar_1951.json
...
data/calendar_2099.json
```

The [Manipuri Calendar Android app](https://play.google.com/store/apps/details?id=com.manipurcalendar)
and the [PWA](https://banishwor.github.io/manipuri-calendar-pwa/) fetch
a year on demand instead of bundling tables, so past and future years
stay available and can be corrected in one place. Each raw file is
accessible at:

- **GitHub Raw:**
  `https://raw.githubusercontent.com/banishwor/meitei-calendar-engine/main/data/calendar_{year}.json`
- **jsDelivr CDN:**
  `https://cdn.jsdelivr.net/gh/banishwor/meitei-calendar-engine@main/data/calendar_{year}.json`

For example, the 2026 file is at
`https://raw.githubusercontent.com/banishwor/meitei-calendar-engine/main/data/calendar_2026.json`
and at
`https://cdn.jsdelivr.net/gh/banishwor/meitei-calendar-engine@main/data/calendar_2026.json`.

To regenerate the hosted files (or extend the range), run:

```bash
python scripts/generate_all.py                    # 1950–2099 into data/
python scripts/generate_all.py --start 2100 --end 2105
```

## How the dates are calculated (in simple words)

You only need three things: the Moon, the Sun, and sunrise in Imphal.

1. **A Meitei month starts at new moon.** Each month runs from one new
   moon to the next — about 29 or 30 days.
2. **The month takes its name from the Sun.** During one moon cycle,
   the Sun moves into a new sign of the zodiac. This sign is called a
   *rashi*, and the rashi gives the month its name:
   Mesha → Sajibu, Vrishabha → Kalen, Mithuna → Inga, Karka → Ingen,
   Simha → Thawan, Kanya → Langban, Tula → Mera, Vrischika → Hiyangei,
   Dhanu → Poinu, Makara → Wakching, Kumbha → Phairen, Meena → Lamta.
3. **The day number (thaban) is the Moon's phase at sunrise.** The
   Moon's cycle is divided into 30 lunar days. Whichever lunar day is
   running at sunrise in Imphal becomes that date's number.
4. **Sometimes two numbers share one date.** If a lunar day starts and
   finishes between two sunrises, it never gets a date of its own, so
   both numbers are written together — like `[30, 1]`. These are called
   pair days. The opposite also happens: a long lunar day can cover two
   sunrises, so two dates carry the same number.
5. **Some years have an extra month.** Twelve moon cycles are about
   11 days shorter than one full round of the Sun, so the two slowly
   drift apart. Every two or three years, a moon cycle passes with no
   sign change inside it; that cycle simply repeats the next month's
   name. The year then has 13 months — for example, 2026 has two Inga
   months.
6. **Very rarely, two months merge into one.** If the Sun changes sign
   twice inside a single moon cycle, the two names join into one month
   and one name is skipped that year. This happens about once in a
   century — in the winter of 1982–83, Poinu and Wakching merged, shown
   in the data as `POINU-WAKCHING`.
7. **The year begins with Sajibu.** Sajibu 1 is Cheiraoba, the Meitei
   New Year.

Everything is computed from the real positions of the Sun and Moon
(NASA's DE421 ephemeris). No printed table is copied.

## The rule (technical version)

The engine implements the traditional rule, reverse-engineered from
published calendars and verified day-by-day (scorecard below):

1. **Months run from new moon to new moon.** Each month is named by the
   Sun's sign change (sankranti, Lahiri sidereal) that falls inside it:
   Mesha→Sajibu, Vrishabha→Kalen, Mithuna→Inga, Karka→Ingen,
   Simha→Thawan, Kanya→Langban, Tula→Mera, Vrischika→Hiyangei,
   Dhanu→Poinu, Makara→Wakching, Kumbha→Phairen, Meena→Lamta.
2. **A month with no sign change is a leap month** (adhik): it repeats
   the following month's name and is printed first of the pair
   (e.g. leap Inga, May–June 2026; leap Sajibu, March–April 2029).
3. **A day's number is the lunar day (tithi) at sunrise in Imphal**
   (24.817° N, 93.937° E). The lunar day is measured from the angle
   between the Moon and the Sun, seen from the centre of the Earth.
   "Sunrise" here means the moment the **centre of the Sun** crosses
   the horizon line — not the normal civil sunrise time. Published
   Meitei calendars really use this exact method. Both details matter,
   and each was found by testing, not guessed.
4. **Pair days:** a lunar day that begins and ends between two sunrises
   never labels a day of its own; it merges onto the civil day it
   begins in — e.g. 19 March 2026 is Lamta 30 + Sajibu 1, shown as
   `[30, 1]`. A lunar day still running at the next sunrise labels two
   days alike (Sajibu 1 on both 14 and 15 April 2029).

## Validation

Before publishing, the rule was checked day by day against four
independent calendars, covering 2002–2030:

| Source | Range | Days | Exact match |
|---|---|---|---|
| manipuricalendar.in (computed calendar) | 2024–2028 | 1,827 | **100%** |
| Manipuri Calendar web calendar (publisher's site) | 2026 | 365 | **100%** |
| Kumsing app (Kangla Labs) published dates | 2024–2030 | 2,557 | 99.57% |
| e-pao printed calendar archives | 2002–2010 | 3,287 | 91.85% |

Notes on the differences, because they are the interesting part:

- **Manipuri Calendar web calendar:** all 365 day labels of 2026 match.
  Its month grids mark 14 pair days where this engine finds 16. On the
  two extra days, the date labels are still the same — only the marking
  differs, not the dates. (On 23 May 2026 it shows a pair day that
  Kumsing's data lacks, agreeing with this engine.)
- **Kumsing:** all 11 days that differ are off by one day, and all sit
  inside a ~4-minute window around sunrise: Kumsing takes the lunar
  day at the earlier civil sunrise. On the 6 days where Kumsing and
  manipuricalendar.in disagree with each other, this engine matches
  the website every time.
- **Printed calendars (2002–2010):** the remaining differences are one
  day here or there, in both directions (old tables and rounding). The
  engine reproduces every structural feature of the print era: all
  three leap months (Thawan 2004, Inga 2007, Kalen 2010), every month
  sequence, and the Cheiraoba pair-day convention in 7 of 9 years.
- There is **no month-sequence failure anywhere** in 2002–2030.

## Known limitations

- A moon cycle containing *two* sign changes (a merged month — one
  month name is skipped) does not occur anywhere in 2002–2030, and the
  engine flags such a month `KSHAYA?`. Exactly one occurs in the hosted
  1950–2099 data: 16 Dec 1982 – 14 Jan 1983, in which the Sun enters
  both Dhanu and Makara. In the hosted data that month is
  named `POINU-WAKCHING` — the two month names joined together. If you
  regenerate the data, the engine restores the `KSHAYA?` flag for that
  month; rename it the same way afterwards.
- The Sun's sign-change times are resolved on a 2-hour grid. Month
  naming only needs to know which month contains a sign change, so
  this is sufficient — but don't use this library for precise
  sign-change *times*.
- Printed calendars sometimes differ from the calculated rule by one
  day, because of their own tables and rounding. This engine follows
  the calculation throughout — the same way modern published calendars
  do.

## License

LGPL-3.0-or-later. You may use this library in your own applications,
including commercial and closed-source ones. If you modify the engine
itself, share those modifications under the same license.

## Author

**Banishwor Athokpam** — Thoubal, Manipur.
Derived from, and verified against, the author's
[Manipuri Calendar PWA](https://github.com/banishwor/manipuri-calendar-pwa)
data and the printed Meitei calendar tradition.
