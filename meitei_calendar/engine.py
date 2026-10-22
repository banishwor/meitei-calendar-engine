"""Astronomy core for the Meitei (Manipuri) calendar.

The rule (reverse-engineered and verified against published sources
over 2002-2030 — see README.md):

- A civil day's Meitei date is the tithi prevailing at sunrise in Imphal,
  where the tithi is the GEOCENTRIC Moon-Sun elongation (classical panchang
  math) and "sunrise" is the moment the Sun's CENTER crosses the geometric
  horizon (altitude 0, no refraction, no upper-limb correction).
- Months are amanta lunations (new moon to new moon), named by the Lahiri
  sidereal sankranti that falls inside the lunation
  (Mesha->Sajibu ... Meena->Lamta). A lunation containing no sankranti is
  adhik (intercalary) and carries the following lunation's name, printed
  first of the pair.
- A tithi that begins and ends between two consecutive sunrises (kshaya)
  never labels a civil day; printed calendars merge it onto the day it
  begins in (the pair-day convention).

Ephemeris: JPL DE421 via Skyfield. The numeric routines are the exact ones
used in the derivation research (gen_predictions.py), unchanged.
"""
from datetime import date, timedelta, timezone
import os

import numpy as np
from skyfield.api import Loader, wgs84

IST = timezone(timedelta(hours=5, minutes=30))
IMPHAL = wgs84.latlon(24.8170, 93.9368)          # Imphal, Manipur
# The JPL ephemeris (de421.bsp, ~17 MB) is downloaded once, on first use,
# into a per-user cache dir (override with $MEITEI_CALENDAR_DATA).
_DATA = (os.environ.get('MEITEI_CALENDAR_DATA')
         or os.path.join(os.path.expanduser('~'), '.cache', 'meitei-calendar'))
os.makedirs(_DATA, exist_ok=True)
_load = Loader(_DATA)
ts = _load.timescale()
eph = _load('de421.bsp')
_sun, _moon, _earth = eph['sun'], eph['moon'], eph['earth']
_obs_geo = _earth
_obs_loc = _earth + IMPHAL

RASHI = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
         'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena']
MONTH_BY_RASHI = {'Mesha': 'SAJIBU', 'Vrishabha': 'KALEN', 'Mithuna': 'INGA',
                  'Karka': 'INGEN', 'Simha': 'THAWAN', 'Kanya': 'LANGBAN',
                  'Tula': 'MERA', 'Vrischika': 'HIYANGEI', 'Dhanu': 'POINU',
                  'Makara': 'WAKCHING', 'Kumbha': 'PHAIREN', 'Meena': 'LAMTA'}
MONTHS = ['SAJIBU', 'KALEN', 'INGA', 'INGEN', 'THAWAN', 'LANGBAN', 'MERA',
          'HIYANGEI', 'POINU', 'WAKCHING', 'PHAIREN', 'LAMTA']


# ---------------------------------------------------------------- sunrises
def _sun_alt(tt):
    return _obs_loc.at(tt).observe(_sun).apparent().altaz()[0].degrees


def sunrises(start: date, end: date) -> dict:
    """Sun-center sunrises at Imphal for every date in [start, end]."""
    out = {}
    d = start
    while d <= end:
        base = ts.utc(d.year, d.month, d.day, -2.5)      # 03:00 IST
        hrs = np.arange(0, 6.51, 5 / 60)
        tt = ts.utc(d.year, d.month, d.day, -2.5 + hrs)
        alt = _sun_alt(tt)
        sr = None
        for i in range(len(hrs) - 1):
            if alt[i] < 0 <= alt[i + 1]:
                lo, hi = float(hrs[i]), float(hrs[i + 1])
                for _ in range(24):
                    mid = (lo + hi) / 2
                    am = _sun_alt(ts.utc(d.year, d.month, d.day, -2.5 + mid))
                    if am < 0:
                        lo = mid
                    else:
                        hi = mid
                sr = ts.utc(d.year, d.month, d.day, -2.5 + (lo + hi) / 2)
                break
        if sr is not None:
            out[d] = sr
        d += timedelta(days=1)
    return out


# ------------------------------------------------------------- elongation
def elongation(t) -> float:
    """Geocentric Moon-Sun elongation in degrees, [0, 360)."""
    _, sl, _ = _obs_geo.at(t).observe(_sun).apparent().ecliptic_latlon()
    _, ml, _ = _obs_geo.at(t).observe(_moon).apparent().ecliptic_latlon()
    return (ml.degrees - sl.degrees) % 360.0


def _elong_unwrapped(tt):
    return np.unwrap(np.radians(elongation(tt)))


def _bisect_elong(s0: date, lo_h: float, hi_h: float, target_deg: float):
    """Refine the hour bracket [lo_h, hi_h] on day-chunk origin s0 to the
    moment the (unwrapped) elongation crosses target_deg."""
    def g(h):
        e = elongation(ts.utc(s0.year, s0.month, s0.day, h))
        return target_deg + ((e - target_deg + 180) % 360 - 180) - target_deg
    lo, hi = lo_h, hi_h
    for _ in range(40):
        mid = (lo + hi) / 2
        if g(mid) < 0:
            lo = mid
        else:
            hi = mid
    return ts.utc(s0.year, s0.month, s0.day, (lo + hi) / 2)


def tithi_boundaries(start: date, end: date):
    """Every tithi boundary in [start, end]: list of (time, tithi_beginning,
    lunation_index) where tithi_beginning is 1..30 and lunation_index counts
    conjunctions from an arbitrary epoch (only differences matter)."""
    out = []
    ndays = (end - start).days
    for chunk in range(0, ndays, 365):
        seg = min(365, ndays - chunk)
        s0 = start + timedelta(days=chunk)
        hrs = np.arange(0, seg * 24 + 1, 1.0)
        tt = ts.utc(s0.year, s0.month, s0.day, hrs)
        el = np.degrees(_elong_unwrapped(tt))
        for i in range(len(hrs) - 1):
            a, b = el[i], el[i + 1]
            tgt = (int(a // 12) + 1) * 12
            while tgt <= b:
                t = _bisect_elong(s0, float(hrs[i]), float(hrs[i + 1]), tgt)
                out.append((t, (tgt // 12) % 30 + 1, tgt // 360))
                tgt += 12
    return out


def conjunctions(start: date, end: date):
    """New moons (elongation crossing 0) in [start, end]."""
    return [t for t, tithi, _ in tithi_boundaries(start, end) if tithi == 1]


# ------------------------------------------------------------- sankrantis
def _ayanamsa_arr(tt):
    yrs = np.array([x.year + x.timetuple().tm_yday / 365.25
                    for x in tt.utc_datetime()])
    return 23.853056 + (yrs - 2000.0) * 0.0139697


def _sid_sun_arr(tt):
    _, sl, _ = _obs_geo.at(tt).observe(_sun).apparent().ecliptic_latlon()
    return (sl.degrees - _ayanamsa_arr(tt)) % 360.0


def sankrantis(start: date, end: date):
    """Sidereal (Lahiri) sign ingresses: list of (rashi_name, approx_time).
    Times are grid-resolution (2 h) — sufficient for month naming, which only
    needs to know which lunation contains the ingress."""
    out = []
    ndays = (end - start).days
    for chunk in range(0, ndays, 365):
        seg = min(365, ndays - chunk)
        s0 = start + timedelta(days=chunk)
        hrs = np.arange(0, seg * 24 + 1, 2.0)
        tt = ts.utc(s0.year, s0.month, s0.day, hrs)
        deg = np.degrees(np.unwrap(np.radians(_sid_sun_arr(tt))))
        for i in range(len(hrs) - 1):
            a, b = deg[i], deg[i + 1]
            for target in range(int(a // 30) * 30 + 30,
                                int(b // 30) * 30 + 31, 30):
                if a < target <= b:
                    out.append((RASHI[(target // 30) % 12], tt[i]))
    return out


# ---------------------------------------------------------- lunation names
def name_lunations(conj, sank):
    """Given conjunction times and sankrantis, return a list of
    [conj_start, conj_end, MONTH_NAME, is_adhik] per lunation.
    A lunation with no sankranti is adhik and takes the NEXT lunation's
    name (it is printed first of the resulting pair). A lunation with two
    sankrantis would skip a month name (kshaya masa) — not observed
    anywhere in 2002-2030; it is named 'KSHAYA?' and flagged."""
    names = []
    for j in range(len(conj) - 1):
        inside = [r for r, when in sank if conj[j].tt < when.tt < conj[j + 1].tt]
        if len(inside) == 1:
            names.append([conj[j], conj[j + 1], MONTH_BY_RASHI[inside[0]], False])
        elif len(inside) == 0:
            names.append([conj[j], conj[j + 1], None, True])
        else:
            names.append([conj[j], conj[j + 1], 'KSHAYA?', False])
    for j in range(len(names)):
        if names[j][3]:
            names[j][2] = names[j + 1][2]
    return names
