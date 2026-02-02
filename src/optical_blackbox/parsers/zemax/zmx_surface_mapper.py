"""Zemax surface type mapper.

Maps Zemax surface types and properties to OBB model format.
"""

from typing import Any

from optical_blackbox.models.surface import Surface, SurfaceType
from optical_blackbox.parsers.zemax.zmx_tokens import (
    SURFACE_TYPE_MAP,
    SUPPORTED_SURFACE_TYPES,
    parm_index_to_coeff_name,
)
from optical_blackbox.exceptions import UnsupportedSurfaceTypeError


def map_surface_type(zemax_type: str) -> SurfaceType:
    """Map Zemax surface type string to OBB SurfaceType.

    Args:
        zemax_type: Zemax surface type (e.g., "STANDARD", "EVENASPH")

    Returns:
        OBB SurfaceType enum value

    Raises:
        UnsupportedSurfaceTypeError: If type is not supported
    """
    zemax_type_upper = zemax_type.upper()

    if zemax_type_upper not in SUPPORTED_SURFACE_TYPES:
        raise UnsupportedSurfaceTypeError(zemax_type)

    obb_type_name = SURFACE_TYPE_MAP.get(zemax_type_upper, "standard")

    return SurfaceType(obb_type_name)


def parse_radius_from_curvature(curvature: float) -> float:
    """Convert Zemax curvature to radius.

    Args:
        curvature: Curvature value (1/mm)

    Returns:
        Radius in mm (inf for flat)
    """
    if abs(curvature) < 1e-15:
        return float("inf")
    return 1.0 / curvature


def parse_thickness(value: str) -> float:
    """Parse thickness value, handling INFINITY.

    Args:
        value: Thickness string

    Returns:
        Thickness in mm (inf for infinite)
    """
    value_upper = value.upper().strip()
    if value_upper in {"INFINITY", "INF", "1.0E+10", "1E+10", "1E10"}:
        return float("inf")
    return float(value)


def build_aspheric_coeffs(parm_values: dict[int, float]) -> dict[str, float] | None:
    """Build aspheric coefficient dictionary from PARM values.

    Args:
        parm_values: Dict mapping PARM index to value

    Returns:
        Dict of coefficient names to values, or None if empty
    """
    if not parm_values:
        return None

    coeffs = {}
    for index, value in parm_values.items():
        if abs(value) > 1e-30:  # Skip negligible values
            coeff_name = parm_index_to_coeff_name(index)
            coeffs[coeff_name] = value

    return coeffs if coeffs else None


def build_surface(surface_data: dict[str, Any]) -> Surface:
    """Build an OBB Surface from parsed Zemax data.

    Args:
        surface_data: Dictionary of parsed surface properties

    Returns:
        OBB Surface object
    """
    # Map surface type
    zemax_type = surface_data.get("type", "STANDARD")
    try:
        surface_type = map_surface_type(zemax_type)
    except UnsupportedSurfaceTypeError:
        # Fall back to standard for unsupported types
        surface_type = SurfaceType.STANDARD

    # Parse radius from curvature
    curvature = surface_data.get("curvature", 0.0)
    radius = parse_radius_from_curvature(curvature)

    # Build aspheric coefficients
    parm_values = surface_data.get("parm", {})
    aspheric_coeffs = build_aspheric_coeffs(parm_values)

    return Surface(
        surface_number=surface_data.get("number", 0),
        surface_type=surface_type,
        radius=radius,
        thickness=surface_data.get("thickness", 0.0),
        material=surface_data.get("material"),
        semi_diameter=surface_data.get("semi_diameter", 0.0),
        conic=surface_data.get("conic", 0.0),
        aspheric_coeffs=aspheric_coeffs,
        decenter_x=surface_data.get("decenter_x", 0.0),
        decenter_y=surface_data.get("decenter_y", 0.0),
        tilt_x=surface_data.get("tilt_x", 0.0),
        tilt_y=surface_data.get("tilt_y", 0.0),
    )
