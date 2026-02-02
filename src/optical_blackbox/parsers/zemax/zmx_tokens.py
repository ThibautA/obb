"""Zemax file format token definitions.

Defines keywords and tokens used in Zemax .zmx files.
"""

from typing import Final

# =============================================================================
# Surface Keywords
# =============================================================================

# Surface definition
SURF: Final[str] = "SURF"

# Surface properties
TYPE: Final[str] = "TYPE"
CURV: Final[str] = "CURV"  # Curvature (1/radius)
THIC: Final[str] = "THIC"  # Thickness
GLAS: Final[str] = "GLAS"  # Glass/material
DIAM: Final[str] = "DIAM"  # Semi-diameter
CONI: Final[str] = "CONI"  # Conic constant
STOP: Final[str] = "STOP"  # Aperture stop marker

# Aspheric parameters
PARM: Final[str] = "PARM"  # Parameter (aspheric coefficients)
XDAT: Final[str] = "XDAT"  # Extra data

# Decentration/tilt
DECX: Final[str] = "DECX"  # Decenter X
DECY: Final[str] = "DECY"  # Decenter Y
TILTX: Final[str] = "TILTX"  # Tilt about X
TILTY: Final[str] = "TILTY"  # Tilt about Y

# =============================================================================
# Surface Types
# =============================================================================

# Mapping of Zemax surface types to OBB types
SURFACE_TYPE_MAP: Final[dict[str, str]] = {
    "STANDARD": "standard",
    "EVENASPH": "evenasph",
    "ODDASPH": "oddasph",
    "TOROIDAL": "toroidal",
    "PARAXIAL": "standard",  # Treat as standard
    "COORDBRK": "standard",  # Coordinate break (handle separately)
}

# Surface types supported in MVP
SUPPORTED_SURFACE_TYPES: Final[set[str]] = {
    "STANDARD",
    "EVENASPH",
    "ODDASPH",
    "TOROIDAL",
    "PARAXIAL",
}

# =============================================================================
# System Keywords
# =============================================================================

# Wavelength
WAVM: Final[str] = "WAVM"  # Wavelength definition
WAVL: Final[str] = "WAVL"  # Alternative wavelength format

# Field
FTYP: Final[str] = "FTYP"  # Field type
XFLN: Final[str] = "XFLN"  # X field
YFLN: Final[str] = "YFLN"  # Y field

# Aperture
ENPD: Final[str] = "ENPD"  # Entrance pupil diameter
FLOA: Final[str] = "FLOA"  # Floating aperture

# System
MODE: Final[str] = "MODE"  # System mode (SEQ/NSC)
UNIT: Final[str] = "UNIT"  # Units

# =============================================================================
# Special Values
# =============================================================================

# Infinity representation
INFINITY_STRINGS: Final[set[str]] = {"INFINITY", "INF", "1.0E+10", "1E+10", "1E10"}

# =============================================================================
# Keywords to Ignore (MVP)
# =============================================================================

# These are parsed but not used in MVP
IGNORED_KEYWORDS: Final[set[str]] = {
    "COAT",  # Coatings
    "SQAP",  # Square aperture
    "OBSC",  # Obscuration
    "MIRR",  # Mirror
    "CONF",  # Configuration
    "MOFF",  # Multi-config operand
    "MAZH",  # Merit function
    "OPDX",  # OPD
    "COMM",  # Comment
    "NAME",  # Surface name
    "HIDE",  # Hide surface
    "SLAB",  # Surface label
}

# =============================================================================
# Parameter Mapping
# =============================================================================

# Zemax PARM index to aspheric coefficient name
# PARM 1 = A2, PARM 2 = A4, etc.
def parm_index_to_coeff_name(index: int) -> str:
    """Convert Zemax PARM index to coefficient name.

    Args:
        index: PARM index (1, 2, 3, ...)

    Returns:
        Coefficient name ("A2", "A4", "A6", ...)
    """
    return f"A{index * 2}"
