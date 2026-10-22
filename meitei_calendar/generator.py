"""Assemble Meitei calendar days from the astronomy core.

A DayRecord is a dict:
  gregorian     'YYYY-MM-DD'
  month         'SAJIBU' .. 'LAMTA'  (month of the sunrise tithi)
  day           1..30                (tithi at sunrise)
  intercalary   True when the day's lunation is adhik (double month)
  merged        [{'month': ..., 'day': ...}, ...] — kshaya tithis that
                begin and end inside this civil day and so never label a
                day of their own; printed calendars show them merged onto
                this day (pair days like [30, 1] or [7, 8]).
"""
from datetime import date, timedelta

from . import engine


def _window(year: int):
    return date(year - 1, 12, 1), date(year + 1, 2, 15)


def generate_range(first: date, last: date):
    """DayRecords for every Gregorian date in [first, last]."""
    w0 = date(first.year - 1, 12, 1) if first.month < 12 else date(first.year, 11, 1)
    w1 = date(last.year + 1, 2, 15)
    sr = engine.sunrises(w0, w1)
    bounds = engine.tithi_boundaries(w0, w1)
    conj = [t for t, tithi, _ in bounds if tithi == 1]
    sank = engine.sankrantis(w0, w1)
    lunations = engine.name_lunations(conj, sank)

    def lunation_at(t):
        for start, end, name, adhik in lunations:
            if start.tt <= t.tt < end.tt:
                return name, adhik
        return None, False

    # kshaya detection: a tithi whose span contains no sunrise merges onto
    # the civil day in which it begins.
    sr_sorted = sorted(sr.items())                      # [(date, ts), ...]
    sr_times = [t for _, t in sr_sorted]
    merged_on = {}
    for i in range(len(bounds) - 1):
        t0, tithi, _ = bounds[i]
        t1 = bounds[i + 1][0]
        # first sunrise strictly after the tithi begins
        nxt = next((t for t in sr_times if t.tt > t0.tt), None)
        if nxt is not None and nxt.tt >= t1.tt:
            # the day this tithi begins in: last sunrise <= t0
            day = max(d for d, t in sr_sorted if t.tt <= t0.tt)
            name, _ = lunation_at(t0)
            merged_on.setdefault(day, []).append({'month': name, 'day': tithi})

    out = []
    d = first
    while d <= last:
        s = sr.get(d)
        if s is None:
            d += timedelta(days=1)
            continue
        tithi = int(engine.elongation(s) // 12) + 1
        name, adhik = lunation_at(s)
        out.append({
            'gregorian': d.isoformat(),
            'month': name,
            'day': tithi,
            'intercalary': adhik,
            'merged': merged_on.get(d, []),
        })
        d += timedelta(days=1)
    return out


def generate_year(year: int):
    return generate_range(date(year, 1, 1), date(year, 12, 31))


# ---------------------------------------------------------------- exports
def to_pwa(records):
    """The PWA's calendar_<year>.json format: a list of
    {"gregorian", "month", "day"} where a pair day carries a 2-element
    "day" list [sunrise_day, merged_day] and, when the pair crosses a
    month boundary, "month" is the incoming month (his convention, e.g.
    Sajibu for [30, 1]). Festivals/events are not generated."""
    out = []
    for r in records:
        if not r['merged']:
            out.append({'gregorian': r['gregorian'], 'month': r['month'],
                        'day': r['day']})
        elif len(r['merged']) == 1:
            m = r['merged'][0]
            out.append({'gregorian': r['gregorian'], 'month': m['month'],
                        'day': [r['day'], m['day']]})
        else:  # never observed in 2002-2030; kept for completeness
            last = r['merged'][-1]
            out.append({'gregorian': r['gregorian'], 'month': last['month'],
                        'day': [r['day']] + [m['day'] for m in r['merged']]})
    return out
