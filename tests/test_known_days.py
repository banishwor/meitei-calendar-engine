"""Fast checks of the astronomy primitives against independently published
values (manipuri calendar site tithi end-times), plus an optional slow
full-year smoke test.

Run the fast tests:   python -m pytest tests/ -q
Run everything:       MEITEI_SLOW_TESTS=1 python -m pytest tests/ -q
"""
import os
from datetime import date, datetime, timedelta, timezone

from meitei_calendar import engine

IST = timezone(timedelta(hours=5, minutes=30))


def _ist(t):
    return t.utc_datetime().astimezone(IST)


def test_conjunction_march_2026():
    # manipuricalendar.in prints Amavasya ending 2026-03-19 06:53:29 IST.
    conjs = engine.conjunctions(date(2026, 3, 15), date(2026, 3, 25))
    assert len(conjs) == 1
    got = _ist(conjs[0])
    want = datetime(2026, 3, 19, 6, 53, 29, tzinfo=IST)
    assert abs((got - want).total_seconds()) < 180


def test_tithi_2_begins_before_sunrise_march_2026():
    # The site prints Sajibu 1 ending 2026-03-20 04:52:48 IST — before that
    # day's sunrise, which is what makes 19 Mar 2026 a [30, 1] pair day.
    bounds = engine.tithi_boundaries(date(2026, 3, 19), date(2026, 3, 21))
    starts = [_ist(t) for t, tithi, _ in bounds if tithi == 2]
    assert len(starts) == 1
    want = datetime(2026, 3, 20, 4, 52, 48, tzinfo=IST)
    assert abs((starts[0] - want).total_seconds()) < 180


def test_sunrise_is_sun_center():
    # Sun-center sunrise at Imphal on 2026-03-19 is ~05:23 IST — minutes
    # later than the civil (upper-limb + refraction) sunrise.
    sr = engine.sunrises(date(2026, 3, 19), date(2026, 3, 19))
    got = _ist(sr[date(2026, 3, 19)])
    assert got.hour == 5 and 22 <= got.minute <= 24


def test_mesha_sankranti_april_2026():
    sank = engine.sankrantis(date(2026, 4, 1), date(2026, 4, 30))
    mesha = [t for name, t in sank if name == 'Mesha']
    assert len(mesha) == 1
    d = mesha[0].utc_datetime().date()
    assert date(2026, 4, 13) <= d <= date(2026, 4, 15)


import pytest

@pytest.mark.skipif(not os.environ.get('MEITEI_SLOW_TESTS'),
                    reason='full-year generation takes a minute or two')
def test_full_year_2029_adhik_sajibu_and_pair_days():
    from meitei_calendar import generate_year
    recs = {r['gregorian']: r for r in generate_year(2029)}
    # adhik Sajibu in spring 2029
    assert recs['2029-04-01']['month'] == 'SAJIBU'
    assert recs['2029-04-01']['intercalary'] is True
    # Sajibu 1 fell in a kshaya merge on 16 Mar 2029 (adhik month) ...
    assert recs['2029-03-16']['merged']
    # ... and labels two consecutive sunrises in the regular month
    assert recs['2029-04-14']['day'] == 1
    assert recs['2029-04-15']['day'] == 1
