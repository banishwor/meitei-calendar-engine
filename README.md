# meitei-calendar-engine

Generate any year of the **Meitei (Manipuri) lunisolar calendar** from
astronomy — no lookup tables, no bundled date data. Give it a Gregorian
year and it computes every day's Meitei month and thaban (day number),
including adhik (leap) months and pair days, for any year the ephemeris
covers — past or future.

```bash
pip install git+https://github.com/banishwor/meitei-calendar-engine
meitei-calendar 2028            # writes calendar_2028.json
meitei-calendar 2029 --rich     # full records: adhik flags, merged tithis
```

```python
from meitei_calendar import generate_year

for day in generate_year(2029):
    print(day["gregorian"], day["month"], day["day"])
```

On first use the JPL DE421 ephemeris (~17 MB) is downloaded once into
`~/.cache/meitei-calendar/` (override with `$MEITEI_CALENDAR_DATA`).
Generating one year takes a minute or two — it is a full ephemeris scan,
not a table lookup.

## Output

Each day record: `gregorian` date, `month` (SAJIBU … LAMTA), `day`
(1–30). The default JSON matches the format used by the
[Manipuri Calendar PWA](https://github.com/banishwor/manipuri-calendar-pwa):
on pair days, `day` is a two-element list like `[30, 1]`. With `--rich`
you also get `intercalary` (the day belongs to an adhik month) and
`merged` (the kshaya tithis merged into that civil day).

## The rule

The engine implements the traditional rule, reverse-engineered from
published calendars and verified day-by-day (scorecard below):

1. **Months are amanta lunations** (new moon to new moon). Each lunation
   is named by the Lahiri sidereal sankranti that falls inside it:
   Mesha→Sajibu, Vrishabha→Kalen, Mithuna→Inga, Karka→Ingen,
   Simha→Thawan, Kanya→Langban, Tula→Mera, Vrischika→Hiyangei,
   Dhanu→Poinu, Makara→Wakching, Kumbha→Phairen, Meena→Lamta.
2. **A lunation with no sankranti is adhik** (intercalary): it repeats the
   following lunation's name and is printed first of the pair
   (e.g. adhik Inga, May–June 2026; adhik Sajibu, March–April 2029).
3. **A day's number is the tithi at sunrise in Imphal**
   (24.817° N, 93.937° E), where the tithi is the **geocentric**
   Moon–Sun elongation (classical panchang math) and "sunrise" is the
   moment the **Sun's centre** crosses the geometric horizon — not the
   civil sunrise. This convention, not an approximation of it, is what
   published Meitei calendars actually use; both details matter and each
   was found by measurement, not assumed.
4. **Pair days:** a tithi that begins and ends between two sunrises
   (kshaya) never labels a day of its own; it merges onto the civil day
   it begins in — e.g. 19 March 2026 is Lamta 30 + Sajibu 1, shown as
   `[30, 1]`. A tithi still running at the next sunrise labels two days
   alike (Sajibu 1 on both 14 and 15 April 2029).

## Validation

The rule was tested against four independent sources, ~7,300 days,
2002–2030, before this library was packaged:

| Source | Range | Days | Exact match |
|---|---|---|---|
| manipuricalendar.in (computed panchang) | 2024–2028 | 1,827 | **100%** |
| Kumsing app (Kangla Labs) bundled database | 2024–2030 | 2,557 | 99.57% |
| e-pao printed calendar archives | 2002–2010 | 3,287 | 91.85% |
| Author's PWA tables | 2026–2027 | 730 | except 3 slips in those tables |

Notes on the differences, because they are the interesting part:

- **Kumsing:** all 11 differing days are ±1 within a ~4-minute window
  around sunrise — Kumsing reads the tithi at the earlier civil sunrise.
  On the 6 days where Kumsing and manipuricalendar.in disagree with each
  other, this engine sides with the website every time.
- **Printed calendars (2002–2010):** the residue is ±1 noise in both
  directions (era table and rounding differences). The engine reproduces
  every structural feature of the print era: all three adhik months
  (Thawan 2004, Inga 2007, Kalen 2010), every month sequence, and the
  Cheiraoba pair-day convention in 7 of 9 years.
- There is **no month-sequence failure anywhere** in 2002–2030.

## Known limitations

- A lunation containing *two* sankrantis (kshaya masa, a skipped month)
  does not occur anywhere in 2002–2030. The engine implements the naming
  rule for it but flags such a month `KSHAYA?` — that path is untested.
- Sankranti times are resolved on a 2-hour grid. Month naming only needs
  to know which lunation contains an ingress, so this is sufficient —
  but don't use this library for precise sankranti *times*.
- Printed calendars occasionally deviate from the computed rule by a day
  (their own tables and rounding). This engine follows the computed
  convention throughout, which is what modern published sources use.

## License

LGPL-3.0-or-later. You may use this library in your own applications,
including commercial and closed-source ones. If you modify the engine
itself, share those modifications under the same license.

## Author

**Banishwor Athokpam** — Thoubal, Manipur.
Derived from, and verified against, the author's
[Manipuri Calendar PWA](https://github.com/banishwor/manipuri-calendar-pwa)
data and the printed Meitei calendar tradition.
