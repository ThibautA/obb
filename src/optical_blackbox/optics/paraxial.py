"""Paraxial optical calculations.

Provides ABCD matrix raytracing for computing EFL, BFL, and NA.
"""

import numpy as np
from numpy.typing import NDArray

from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.optics.glass_catalog import get_refractive_index


def compute_transfer_matrix(thickness: float, n: float) -> NDArray[np.floating]:
    """Compute transfer (propagation) matrix.

    Args:
        thickness: Distance in mm
        n: Refractive index of medium

    Returns:
        2x2 transfer matrix
    """
    if thickness == float("inf") or thickness == float("-inf"):
        thickness = 0.0  # Treat infinite thickness as zero for matrix calc

    return np.array([
        [1.0, thickness / n],
        [0.0, 1.0],
    ], dtype=np.float64)


def compute_refraction_matrix(
    curvature: float,
    n_before: float,
    n_after: float,
) -> NDArray[np.floating]:
    """Compute refraction matrix at a surface.

    Args:
        curvature: Surface curvature (1/radius) in 1/mm
        n_before: Refractive index before surface
        n_after: Refractive index after surface

    Returns:
        2x2 refraction matrix
    """
    power = (n_after - n_before) * curvature

    return np.array([
        [1.0, 0.0],
        [-power, n_before / n_after],
    ], dtype=np.float64)


def compute_system_matrix(
    surface_group: SurfaceGroup,
    wavelength_nm: float,
) -> NDArray[np.floating]:
    """Compute the system ABCD matrix.

    Traces through all surfaces from first to last.

    Args:
        surface_group: Optical surfaces
        wavelength_nm: Wavelength in nm

    Returns:
        2x2 system matrix [[A, B], [C, D]]
    """
    # Start with identity matrix
    M = np.eye(2, dtype=np.float64)

    n_current = 1.0  # Start in air

    surfaces = surface_group.surfaces

    for i, surface in enumerate(surfaces):
        # Get refractive index after this surface
        n_next = get_refractive_index(surface.material, wavelength_nm)

        # Refraction at surface
        curvature = surface.curvature
        R = compute_refraction_matrix(curvature, n_current, n_next)
        M = R @ M

        # Transfer to next surface (if not the last one)
        if i < len(surfaces) - 1:
            thickness = surface.thickness
            T = compute_transfer_matrix(thickness, n_next)
            M = T @ M

        n_current = n_next

    return M


def extract_efl_from_matrix(M: NDArray[np.floating]) -> float:
    """Extract effective focal length from system matrix.

    EFL = -1/C where M = [[A, B], [C, D]]

    Args:
        M: 2x2 system matrix

    Returns:
        Effective focal length in mm (inf for afocal)
    """
    C = M[1, 0]

    if abs(C) < 1e-15:
        return float("inf")

    return -1.0 / C


def extract_bfl_from_matrix(M: NDArray[np.floating]) -> float:
    """Extract back focal length from system matrix.

    BFL = -A/C where M = [[A, B], [C, D]]

    Args:
        M: 2x2 system matrix

    Returns:
        Back focal length in mm
    """
    A = M[0, 0]
    C = M[1, 0]

    if abs(C) < 1e-15:
        return float("inf")

    return -A / C


def compute_paraxial_properties(
    surface_group: SurfaceGroup,
    wavelength_nm: float | None = None,
) -> dict[str, float]:
    """Compute all paraxial optical properties.

    Args:
        surface_group: Optical surfaces
        wavelength_nm: Wavelength in nm (default: primary wavelength)

    Returns:
        Dictionary with keys: 'efl_mm', 'bfl_mm', 'na'
    """
    if wavelength_nm is None:
        wavelength_nm = surface_group.primary_wavelength

    # Compute system matrix
    M = compute_system_matrix(surface_group, wavelength_nm)

    # Extract properties
    efl = extract_efl_from_matrix(M)
    bfl = extract_bfl_from_matrix(M)

    # Compute NA from entrance pupil and EFL
    # NA ≈ (entrance diameter / 2) / |EFL|
    entrance_diameter = surface_group.surfaces[0].diameter if surface_group.surfaces else 0.0

    if abs(efl) > 1e-10 and efl != float("inf"):
        na = entrance_diameter / (2.0 * abs(efl))
        na = min(na, 1.0)  # Cap at 1.0
    else:
        na = 0.0

    return {
        "efl_mm": round(efl, 4) if efl != float("inf") else float("inf"),
        "bfl_mm": round(bfl, 4) if bfl != float("inf") else float("inf"),
        "na": round(na, 4),
    }


class ParaxialCalculator:
    """Calculator for paraxial optical properties.

    Implements the OpticalCalculator protocol.
    """

    def compute_efl(self, surfaces: SurfaceGroup, wavelength_nm: float) -> float:
        """Compute effective focal length."""
        M = compute_system_matrix(surfaces, wavelength_nm)
        return extract_efl_from_matrix(M)

    def compute_bfl(self, surfaces: SurfaceGroup, wavelength_nm: float) -> float:
        """Compute back focal length."""
        M = compute_system_matrix(surfaces, wavelength_nm)
        return extract_bfl_from_matrix(M)

    def compute_na(self, surfaces: SurfaceGroup, wavelength_nm: float) -> float:
        """Compute numerical aperture."""
        props = compute_paraxial_properties(surfaces, wavelength_nm)
        return props["na"]

    def compute_all(
        self,
        surfaces: SurfaceGroup,
        wavelength_nm: float,
    ) -> dict[str, float]:
        """Compute all optical properties."""
        return compute_paraxial_properties(surfaces, wavelength_nm)
