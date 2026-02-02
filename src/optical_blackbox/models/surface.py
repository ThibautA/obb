"""Surface model for optical elements.

Defines a single optical surface with all its properties.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, field_serializer


# Sentinel value for infinity in JSON (since JSON doesn't support inf)
INFINITY_SENTINEL = 1e99


class SurfaceType(str, Enum):
    """Supported surface types.

    MVP supports:
    - STANDARD: Spherical/conic surface
    - EVENASPH: Even asphere (A2, A4, A6, ...)
    - ODDASPH: Odd asphere (A1, A3, A5, ...)
    - TOROIDAL: Toroidal surface

    Future types will be added to the SurfaceRepresentation protocol.
    """

    STANDARD = "standard"
    EVENASPH = "evenasph"
    ODDASPH = "oddasph"
    TOROIDAL = "toroidal"


class SurfaceVisibility(str, Enum):
    """Visibility level for selective encryption.

    - PUBLIC: Surface data is stored in clear text
    - ENCRYPTED: Surface data is encrypted
    - REDACTED: Surface exists but all data is hidden (metadata only)
    """

    PUBLIC = "public"
    ENCRYPTED = "encrypted"
    REDACTED = "redacted"


class Surface(BaseModel):
    """Single optical surface in a sequential system.

    Represents one surface with its geometric and material properties.
    Surfaces are numbered sequentially starting from 0 (object) or 1.

    Attributes:
        surface_number: Sequential index in the optical system
        surface_type: Type of surface (standard, asphere, etc.)
        radius: Radius of curvature in mm (inf for flat)
        thickness: Distance to next surface in mm
        material: Glass name (None for air)
        semi_diameter: Semi-diameter (half clear aperture) in mm
        conic: Conic constant (0=sphere, -1=parabola)
        aspheric_coeffs: Dict of aspheric coefficients {"A4": 1.2e-5, ...}
        decenter_x: X decenter in mm
        decenter_y: Y decenter in mm
        tilt_x: X tilt in degrees
        tilt_y: Y tilt in degrees

    Example:
        >>> surface = Surface(
        ...     surface_number=1,
        ...     radius=25.84,
        ...     thickness=6.0,
        ...     material="N-BK7",
        ...     semi_diameter=12.7,
        ... )
    """

    surface_number: int = Field(..., ge=0, description="Surface index in system")
    surface_type: SurfaceType = Field(
        default=SurfaceType.STANDARD,
        description="Type of optical surface",
    )

    # Geometry
    radius: float = Field(
        default=float("inf"),
        description="Radius of curvature in mm (use float('inf') for flat)",
    )
    thickness: float = Field(
        default=0.0,
        description="Distance to next surface in mm",
    )

    @field_validator("radius", mode="before")
    @classmethod
    def parse_radius(cls, v: Any) -> float:
        """Convert None or large values to infinity."""
        if v is None:
            return float("inf")
        if isinstance(v, (int, float)) and abs(v) >= INFINITY_SENTINEL:
            return float("inf")
        return float(v)

    @field_serializer("radius")
    def serialize_radius(self, value: float) -> float | None:
        """Serialize infinity as sentinel value for JSON compatibility."""
        if value == float("inf") or value == float("-inf") or abs(value) >= INFINITY_SENTINEL:
            return INFINITY_SENTINEL if value > 0 else -INFINITY_SENTINEL
        return value
    semi_diameter: float = Field(
        default=0.0,
        ge=0,
        description="Semi-diameter (half aperture) in mm",
    )
    conic: float = Field(
        default=0.0,
        description="Conic constant (0=sphere, -1=parabola, <-1=hyperbola)",
    )

    # Material
    material: Optional[str] = Field(
        default=None,
        description="Glass material name (None for air)",
    )

    # Aspheric coefficients
    aspheric_coeffs: Optional[dict[str, float]] = Field(
        default=None,
        description="Aspheric coefficients, e.g. {'A4': 1.2e-5, 'A6': 3.4e-8}",
    )

    # Decentration and tilt
    decenter_x: float = Field(default=0.0, description="X decenter in mm")
    decenter_y: float = Field(default=0.0, description="Y decenter in mm")
    tilt_x: float = Field(default=0.0, description="X tilt in degrees")
    tilt_y: float = Field(default=0.0, description="Y tilt in degrees")

    # Visibility for selective encryption
    visibility: SurfaceVisibility = Field(
        default=SurfaceVisibility.PUBLIC,
        description="Visibility level for selective encryption",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "surface_number": 1,
                "surface_type": "standard",
                "radius": 25.84,
                "thickness": 6.0,
                "material": "N-BK7",
                "semi_diameter": 12.7,
                "conic": 0.0,
            }
        }
    }

    @property
    def is_flat(self) -> bool:
        """Check if surface is flat (infinite radius)."""
        return abs(self.radius) == float("inf") or abs(self.radius) > 1e10

    @property
    def is_air(self) -> bool:
        """Check if material after surface is air."""
        return self.material is None

    @property
    def curvature(self) -> float:
        """Get curvature (1/radius). Returns 0 for flat surfaces."""
        if self.is_flat:
            return 0.0
        return 1.0 / self.radius

    @property
    def diameter(self) -> float:
        """Get full diameter (2 * semi_diameter)."""
        return 2.0 * self.semi_diameter

    @property
    def has_aspheric_terms(self) -> bool:
        """Check if surface has non-zero aspheric coefficients."""
        if self.aspheric_coeffs is None:
            return False
        return any(abs(v) > 1e-20 for v in self.aspheric_coeffs.values())

    @property
    def is_decentered(self) -> bool:
        """Check if surface has any decentration or tilt."""
        return (
            abs(self.decenter_x) > 1e-10
            or abs(self.decenter_y) > 1e-10
            or abs(self.tilt_x) > 1e-10
            or abs(self.tilt_y) > 1e-10
        )
