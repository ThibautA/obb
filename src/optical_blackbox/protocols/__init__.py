"""Protocol definitions for Optical BlackBox.

Provides extensible interfaces for parsers and calculators.
"""

from optical_blackbox.protocols.parser import DesignFileParser
from optical_blackbox.protocols.optical_calculator import OpticalCalculator

__all__ = [
    "DesignFileParser",
    "OpticalCalculator",
]
