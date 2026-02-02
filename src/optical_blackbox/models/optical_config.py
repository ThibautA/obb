"""Optical configuration model.

Defines wavelength, field, and aperture configuration for optical systems.
"""

from typing import Literal
from pydantic import BaseModel, Field

from optical_blackbox.core.constants import DEFAULT_WAVELENGTH_NM


class WavelengthConfig(BaseModel):
    """Wavelength configuration for an optical system.

    Attributes:
        wavelengths_nm: List of wavelengths in nanometers
        primary_index: Index of primary (reference) wavelength
        weights: Optional weights for each wavelength
    """

    wavelengths_nm: list[float] = Field(
        default=[DEFAULT_WAVELENGTH_NM],
        min_length=1,
        description="Design wavelengths in nanometers",
    )
    primary_index: int = Field(
        default=0,
        ge=0,
        description="Index of primary wavelength",
    )
    weights: list[float] | None = Field(
        default=None,
        description="Optional weights for each wavelength",
    )

    @property
    def primary_wavelength(self) -> float:
        """Get primary wavelength in nm."""
        if 0 <= self.primary_index < len(self.wavelengths_nm):
            return self.wavelengths_nm[self.primary_index]
        return self.wavelengths_nm[0]

    @property
    def num_wavelengths(self) -> int:
        """Number of wavelengths."""
        return len(self.wavelengths_nm)


class FieldConfig(BaseModel):
    """Field configuration for an optical system.

    Attributes:
        field_type: Type of field specification
        field_points: List of field values (degrees or mm)
        weights: Optional weights for each field point
    """

    field_type: Literal["angle", "height", "real_height"] = Field(
        default="angle",
        description="Field specification type",
    )
    field_points: list[float] = Field(
        default=[0.0],
        min_length=1,
        description="Field values (degrees for angle, mm for height)",
    )
    weights: list[float] | None = Field(
        default=None,
        description="Optional weights for each field point",
    )

    @property
    def max_field(self) -> float:
        """Get maximum field value."""
        return max(abs(f) for f in self.field_points) if self.field_points else 0.0


class ApertureConfig(BaseModel):
    """Aperture configuration for an optical system.

    Attributes:
        aperture_type: Type of aperture specification
        value: Aperture value (interpretation depends on type)
        stop_surface: Index of aperture stop surface
    """

    aperture_type: Literal["EPD", "image_f/#", "object_NA", "float_stop"] = Field(
        default="EPD",
        description="Aperture specification type",
    )
    value: float = Field(
        default=10.0,
        gt=0,
        description="Aperture value (mm for EPD, ratio for f/#, etc.)",
    )
    stop_surface: int | None = Field(
        default=None,
        ge=0,
        description="Index of aperture stop surface",
    )


class OpticalConfig(BaseModel):
    """Complete optical configuration.

    Combines wavelength, field, and aperture configurations.
    """

    wavelengths: WavelengthConfig = Field(
        default_factory=WavelengthConfig,
        description="Wavelength configuration",
    )
    fields: FieldConfig = Field(
        default_factory=FieldConfig,
        description="Field configuration",
    )
    aperture: ApertureConfig = Field(
        default_factory=ApertureConfig,
        description="Aperture configuration",
    )
