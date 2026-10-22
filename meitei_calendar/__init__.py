"""meitei_calendar — generate Meitei (Manipuri) calendar years from astronomy.

Implements the verified Meitei calendar rule (see README.md): geocentric
tithi at sun-center sunrise in Imphal; amanta months named by the Lahiri
sidereal sankranti inside the lunation; adhik months repeat by rule;
kshaya tithis merge onto the day they begin in (printed pair days).
"""
from .generator import generate_year, generate_range, to_pwa

__all__ = ['generate_year', 'generate_range', 'to_pwa']
__version__ = '1.0.0'
