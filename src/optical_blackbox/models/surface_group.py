"""SurfaceGroup model for optical systems.

Defines a collection of surfaces representing a complete optical element.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, computed_field

from optical_blackbox.models.surface import Surface


class SurfaceGroup(BaseModel):
    """Collection of sequential optical surfaces.

    Represents a complete optical element (lens, doublet, etc.) with all
    its surfaces in order from object to image.

    Attributes:
        surfaces: List of Surface objects in order
        stop_surface: Index of aperture stop surface (if defined)
        wavelengths_nm: Design wavelengths in nanometers
        primary_wavelength_index: Index of primary wavelength in list
        field_type: Type of field specification ('angle' or 'height')
        max_field: Maximum field value (degrees or mm)

    Example:
        >>> doublet = SurfaceGroup(
        ...     surfaces=[surface1, surface2, surface3, surface4],
        ...     wavelengths_nm=[486.13, 587.56, 656.27],
        ...     primary_wavelength_index=1,
        ... )
    """

    surfaces: list[Surface] = Field(
        ...,
        min_length=1,
        description="List of surfaces in order from object to image",
    )

    stop_surface: Optional[int] = Field(
        default=None,
        ge=0,
        description="Index of aperture stop surface",
    )

    # Wavelength configuration
    wavelengths_nm: list[float] = Field(
        default=[587.56],
        min_length=1,
        description="Design wavelengths in nanometers",
    )
    primary_wavelength_index: int = Field(
        default=0,
        ge=0,
        description="Index of primary wavelength in wavelengths_nm list",
    )

    # Field configuration
    field_type: Literal["angle", "height"] = Field(
        default="angle",
        description="Field specification type: 'angle' (degrees) or 'height' (mm)",
    )
    max_field: float = Field(
        default=0.0,
        ge=0,
        description="Maximum field value (degrees or mm depending on field_type)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "surfaces": [
                    {"surface_number": 0, "radius": float("inf"), "thickness": float("inf")},
                    {"surface_number": 1, "radius": 25.84, "thickness": 6.0, "material": "N-BK7"},
                ],
                "wavelengths_nm": [587.56],
            }
        }
    }

    @computed_field
    @property
    def num_surfaces(self) -> int:
        """Number of surfaces in the group."""
        return len(self.surfaces)

    @computed_field
    @property
    def total_length(self) -> float:
        """Total axial length (sum of thicknesses except last)."""
        if len(self.surfaces) <= 1:
            return 0.0
        # Sum thicknesses of all surfaces except the last
        return sum(
            s.thickness for s in self.surfaces[:-1]
            if s.thickness != float("inf") and s.thickness != float("-inf")
        )

    @property
    def primary_wavelength(self) -> float:
        """Get primary design wavelength in nm."""
        if self.primary_wavelength_index < len(self.wavelengths_nm):
            return self.wavelengths_nm[self.primary_wavelength_index]
        return self.wavelengths_nm[0]

    @property
    def max_diameter(self) -> float:
        """Get maximum diameter across all surfaces."""
        return max(s.diameter for s in self.surfaces) if self.surfaces else 0.0

    @property
    def spectral_range(self) -> tuple[float, float]:
        """Get spectral range (min, max wavelength in nm)."""
        return (min(self.wavelengths_nm), max(self.wavelengths_nm))

    def get_surface(self, index: int) -> Surface:
        """Get surface by index.

        Args:
            index: Surface index (0-based)

        Returns:
            Surface at the given index

        Raises:
            IndexError: If index is out of range
        """
        return self.surfaces[index]

    def iter_optical_surfaces(self):
        """Iterate over non-object, non-image surfaces.

        Yields:
            Surface objects excluding first (object) and last (image) if infinite
        """
        for surface in self.surfaces:
            # Skip object plane (typically index 0 with infinite thickness)
            if surface.surface_number == 0 and surface.thickness == float("inf"):
                continue
            yield surface

    def get_encrypted_surfaces(self) -> list[Surface]:
        """Get surfaces marked for encryption.

        Returns:
            List of surfaces with visibility=ENCRYPTED
        """
        from optical_blackbox.models.surface import SurfaceVisibility
        return [s for s in self.surfaces if s.visibility == SurfaceVisibility.ENCRYPTED]

    def get_public_surfaces(self) -> list[Surface]:
        """Get publicly visible surfaces.

        Returns:
            List of surfaces with visibility=PUBLIC
        """
        from optical_blackbox.models.surface import SurfaceVisibility
        return [s for s in self.surfaces if s.visibility == SurfaceVisibility.PUBLIC]

    def get_redacted_surfaces(self) -> list[Surface]:
        """Get redacted surfaces (hidden).

        Returns:
            List of surfaces with visibility=REDACTED
        """
        from optical_blackbox.models.surface import SurfaceVisibility
        return [s for s in self.surfaces if s.visibility == SurfaceVisibility.REDACTED]

    def has_selective_encryption(self) -> bool:
        """Check if group uses selective encryption.

        Returns:
            True if any surface has non-PUBLIC visibility
        """
        from optical_blackbox.models.surface import SurfaceVisibility
        return any(s.visibility != SurfaceVisibility.PUBLIC for s in self.surfaces)
