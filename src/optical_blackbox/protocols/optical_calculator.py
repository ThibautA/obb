"""Protocol definitions for optical calculators.

Defines the contract for optical property calculators, allowing
different implementations (paraxial, real raytracing, etc.).
"""

from typing import Protocol, runtime_checkable

from optical_blackbox.models.surface_group import SurfaceGroup


@runtime_checkable
class OpticalCalculator(Protocol):
    """Protocol for optical property calculators.

    Implementations can use different methods:
    - Paraxial (ABCD matrices) - fast, approximate
    - Real raytracing - accurate, slower
    - Aberration analysis - detailed

    Example:
        >>> class ParaxialCalculator:
        ...     def compute_efl(self, surfaces: SurfaceGroup, wavelength_nm: float) -> float:
        ...         # ABCD matrix calculation
        ...         ...
    """

    def compute_efl(self, surfaces: SurfaceGroup, wavelength_nm: float) -> float:
        """Calculate effective focal length.

        Args:
            surfaces: SurfaceGroup to analyze
            wavelength_nm: Wavelength in nanometers

        Returns:
            Effective focal length in mm (can be inf for afocal)
        """
        ...

    def compute_bfl(self, surfaces: SurfaceGroup, wavelength_nm: float) -> float:
        """Calculate back focal length.

        Args:
            surfaces: SurfaceGroup to analyze
            wavelength_nm: Wavelength in nanometers

        Returns:
            Back focal length in mm
        """
        ...

    def compute_na(self, surfaces: SurfaceGroup, wavelength_nm: float) -> float:
        """Calculate numerical aperture.

        Args:
            surfaces: SurfaceGroup to analyze
            wavelength_nm: Wavelength in nanometers

        Returns:
            Numerical aperture (0 < NA <= 1)
        """
        ...

    def compute_all(
        self, surfaces: SurfaceGroup, wavelength_nm: float
    ) -> dict[str, float]:
        """Calculate all optical properties.

        Args:
            surfaces: SurfaceGroup to analyze
            wavelength_nm: Wavelength in nanometers

        Returns:
            Dictionary with keys: 'efl_mm', 'bfl_mm', 'na'
        """
        ...
