"""Glass catalog for refractive index lookup.

Provides refractive index values for common optical glasses.

MVP Limitations:
- Single wavelength only (d-line, 587.56nm)
- Limited catalog (~20 common glasses)
- No dispersion formulas (Sellmeier, etc.)
"""

from typing import Final

from optical_blackbox.core.constants import AIR_INDEX, DEFAULT_UNKNOWN_INDEX


# Refractive indices at d-line (587.56 nm)
# Source: Schott catalog and common manufacturers
GLASS_CATALOG: Final[dict[str, float]] = {
    # Schott Crown glasses
    "N-BK7": 1.5168,
    "N-K5": 1.5224,
    "N-SK16": 1.6204,
    "N-SK2": 1.6074,
    "N-PSK53A": 1.6180,
    "N-SSK8": 1.6177,
    # Schott Flint glasses
    "N-SF11": 1.7847,
    "N-SF6": 1.8052,
    "N-SF5": 1.6727,
    "N-SF1": 1.7174,
    "N-SF2": 1.6477,
    "SF5": 1.6727,
    "F2": 1.6200,
    # Schott Lanthanum glasses
    "N-LAK22": 1.6516,
    "N-LAF2": 1.7440,
    "N-LAK9": 1.6910,
    "N-LAF7": 1.7495,
    # Schott Special glasses
    "N-FK51A": 1.4866,
    "N-PK52A": 1.4970,
    # Common materials
    "SILICA": 1.4585,
    "FUSED_SILICA": 1.4585,
    "FUSEDSILICA": 1.4585,
    "CAF2": 1.4338,
    "SAPPHIRE": 1.7682,
    "MGF2": 1.3777,
    "BAF2": 1.4741,
    "ZNS": 2.3525,
    "ZNSE": 2.4028,
    "GE": 4.0026,
    "SI": 3.4223,
    # Legacy Schott names
    "BK7": 1.5168,
    "SF11": 1.7847,
    "SF6": 1.8052,
    "SK16": 1.6204,
    "LAK22": 1.6516,
}


def get_refractive_index(
    material: str | None,
    wavelength_nm: float = 587.56,
) -> float:
    """Get refractive index for a material.

    Args:
        material: Glass name (None for air)
        wavelength_nm: Wavelength in nm (MVP: only d-line supported)

    Returns:
        Refractive index

    Note:
        MVP ignores wavelength and returns d-line value.
        Unknown materials return default index of 1.5.
    """
    if material is None or material.strip() == "":
        return AIR_INDEX

    # Normalize material name
    material_upper = material.upper().strip().replace(" ", "").replace("-", "")

    # Try exact match first
    if material.upper() in GLASS_CATALOG:
        return GLASS_CATALOG[material.upper()]

    # Try normalized match
    for name, index in GLASS_CATALOG.items():
        if name.replace("-", "").replace(" ", "") == material_upper:
            return index

    # Unknown material - return default
    return DEFAULT_UNKNOWN_INDEX


def is_material_known(material: str) -> bool:
    """Check if a material is in the catalog.

    Args:
        material: Glass name

    Returns:
        True if material is known
    """
    if not material:
        return True  # Air is "known"

    material_upper = material.upper().strip()
    if material_upper in GLASS_CATALOG:
        return True

    # Try normalized
    material_normalized = material_upper.replace("-", "").replace(" ", "")
    for name in GLASS_CATALOG:
        if name.replace("-", "").replace(" ", "") == material_normalized:
            return True

    return False


def list_materials() -> list[str]:
    """List all known materials.

    Returns:
        List of material names
    """
    return list(GLASS_CATALOG.keys())
