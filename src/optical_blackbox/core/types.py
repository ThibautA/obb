"""Core type aliases for Optical BlackBox.

Centralized type definitions for consistent typing across the codebase.
"""

from pathlib import Path
from typing import Union, TypeAlias

# Path types
PathLike: TypeAlias = Union[str, Path]

# PEM-encoded key strings
PEMString: TypeAlias = str

# Binary data
Bytes: TypeAlias = bytes

# Numeric types for optical calculations
Radius: TypeAlias = float  # mm, can be inf for flat surfaces
Thickness: TypeAlias = float  # mm
SemiDiameter: TypeAlias = float  # mm
Wavelength: TypeAlias = float  # nm
RefractiveIndex: TypeAlias = float

# Coefficients
ConicConstant: TypeAlias = float
AsphericCoefficient: TypeAlias = float

# Identifiers
VendorId: TypeAlias = str
ComponentName: TypeAlias = str
