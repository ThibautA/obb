"""Unit tests for optics/paraxial.py - Paraxial optical calculations."""

import pytest
import numpy as np

from optical_blackbox.optics.paraxial import (
    compute_transfer_matrix,
    compute_refraction_matrix,
    compute_system_matrix,
    extract_efl_from_matrix,
    extract_bfl_from_matrix,
    compute_paraxial_properties,
)
from optical_blackbox.models.surface import Surface, SurfaceType
from optical_blackbox.models.surface_group import SurfaceGroup


class TestComputeTransferMatrix:
    """Tests for transfer (propagation) matrix computation."""

    def test_zero_thickness(self):
        """Zero thickness should give identity matrix."""
        T = compute_transfer_matrix(0.0, 1.0)
        expected = np.array([[1, 0], [0, 1]])
        np.testing.assert_array_almost_equal(T, expected)

    def test_positive_thickness_in_air(self):
        """Positive thickness in air (n=1)."""
        T = compute_transfer_matrix(10.0, 1.0)
        expected = np.array([[1, 10], [0, 1]])
        np.testing.assert_array_almost_equal(T, expected)

    def test_thickness_in_glass(self):
        """Thickness in glass (n=1.5)."""
        T = compute_transfer_matrix(10.0, 1.5)
        expected = np.array([[1, 10/1.5], [0, 1]])
        np.testing.assert_array_almost_equal(T, expected)

    def test_infinite_thickness_treated_as_zero(self):
        """Infinite thickness should be treated as zero."""
        T = compute_transfer_matrix(float("inf"), 1.0)
        expected = np.array([[1, 0], [0, 1]])
        np.testing.assert_array_almost_equal(T, expected)


class TestComputeRefractionMatrix:
    """Tests for refraction matrix computation."""

    def test_flat_surface(self):
        """Flat surface (curvature=0) should give identity for height."""
        R = compute_refraction_matrix(0.0, 1.0, 1.5)
        # For flat surface: power = 0, so matrix is [[1, 0], [0, n1/n2]]
        expected = np.array([[1, 0], [0, 1/1.5]])
        np.testing.assert_array_almost_equal(R, expected)

    def test_curved_surface_air_to_glass(self):
        """Refraction at curved surface from air to glass."""
        # Curvature = 1/50 = 0.02
        curvature = 0.02
        n_before = 1.0
        n_after = 1.5
        
        R = compute_refraction_matrix(curvature, n_before, n_after)
        
        # Power = (n_after - n_before) * curvature = 0.5 * 0.02 = 0.01
        power = (n_after - n_before) * curvature
        expected = np.array([
            [1, 0],
            [-power, n_before / n_after]
        ])
        np.testing.assert_array_almost_equal(R, expected)

    def test_same_index_no_refraction(self):
        """Same index on both sides should give identity."""
        R = compute_refraction_matrix(0.02, 1.5, 1.5)
        # Power = 0 when n_before == n_after
        expected = np.array([[1, 0], [0, 1]])
        np.testing.assert_array_almost_equal(R, expected)


class TestExtractEflFromMatrix:
    """Tests for EFL extraction from system matrix."""

    def test_simple_lens(self):
        """EFL = -1/C from system matrix."""
        # Matrix with C = -0.02 → EFL = 50
        M = np.array([[1, 10], [-0.02, 0.8]])
        efl = extract_efl_from_matrix(M)
        assert abs(efl - 50.0) < 0.01

    def test_afocal_system(self):
        """Afocal system (C ≈ 0) should give infinite EFL."""
        M = np.array([[2, 10], [0, 0.5]])
        efl = extract_efl_from_matrix(M)
        assert efl == float("inf")

    def test_negative_power_lens(self):
        """Negative power lens."""
        # C = 0.02 → EFL = -50
        M = np.array([[1, 10], [0.02, 0.8]])
        efl = extract_efl_from_matrix(M)
        assert abs(efl - (-50.0)) < 0.01


class TestExtractBflFromMatrix:
    """Tests for BFL extraction from system matrix."""

    def test_simple_system(self):
        """BFL = -A/C from system matrix."""
        # A = 0.8, C = -0.02 → BFL = -0.8/(-0.02) = 40
        M = np.array([[0.8, 10], [-0.02, 0.5]])
        bfl = extract_bfl_from_matrix(M)
        assert abs(bfl - 40.0) < 0.01

    def test_afocal_system(self):
        """Afocal system should give infinite BFL."""
        M = np.array([[2, 10], [0, 0.5]])
        bfl = extract_bfl_from_matrix(M)
        assert bfl == float("inf")


class TestComputeSystemMatrix:
    """Tests for system matrix computation."""

    def test_single_thin_lens(self):
        """Test thin lens approximation."""
        # Create a thin lens: front surface R=100, back surface R=-100
        surfaces = [
            Surface(surface_number=0, radius=float("inf"), thickness=float("inf")),
            Surface(surface_number=1, radius=100.0, thickness=0.1, material="N-BK7"),
            Surface(surface_number=2, radius=-100.0, thickness=50.0, material=None),
            Surface(surface_number=3, radius=float("inf"), thickness=0.0),
        ]
        
        sg = SurfaceGroup(surfaces=surfaces, wavelengths_nm=[587.56])
        M = compute_system_matrix(sg, 587.56)
        
        # System matrix should have non-zero power (C element)
        assert abs(M[1, 0]) > 1e-6

    def test_flat_surfaces_only(self):
        """System with only flat surfaces should have no power."""
        surfaces = [
            Surface(surface_number=0, radius=float("inf"), thickness=float("inf")),
            Surface(surface_number=1, radius=float("inf"), thickness=10.0, material="N-BK7"),
            Surface(surface_number=2, radius=float("inf"), thickness=0.0, material=None),
        ]
        
        sg = SurfaceGroup(surfaces=surfaces, wavelengths_nm=[587.56])
        M = compute_system_matrix(sg, 587.56)
        
        # No optical power: C ≈ 0
        assert abs(M[1, 0]) < 1e-10


class TestComputeParaxialProperties:
    """Tests for complete paraxial property computation."""

    def test_returns_dict_with_required_keys(self, sample_surface_group):
        """Should return dict with efl_mm, bfl_mm, na."""
        result = compute_paraxial_properties(sample_surface_group)
        
        assert isinstance(result, dict)
        assert "efl_mm" in result
        assert "bfl_mm" in result
        assert "na" in result

    def test_positive_power_lens(self):
        """Positive power lens should have positive EFL."""
        # Simple positive lens
        surfaces = [
            Surface(surface_number=0, radius=float("inf"), thickness=float("inf")),
            Surface(surface_number=1, radius=100.0, thickness=5.0, material="N-BK7", semi_diameter=12.7),
            Surface(surface_number=2, radius=-100.0, thickness=50.0, material=None, semi_diameter=12.7),
            Surface(surface_number=3, radius=float("inf"), thickness=0.0),
        ]
        
        sg = SurfaceGroup(surfaces=surfaces, wavelengths_nm=[587.56], stop_surface=1)
        result = compute_paraxial_properties(sg)
        
        # Should have positive EFL (positive power lens)
        assert result["efl_mm"] > 0 or result["efl_mm"] == float("inf")

    def test_uses_primary_wavelength(self, sample_surface_group):
        """Should use primary wavelength by default."""
        result1 = compute_paraxial_properties(sample_surface_group)
        result2 = compute_paraxial_properties(
            sample_surface_group, 
            wavelength_nm=sample_surface_group.primary_wavelength
        )
        
        assert result1["efl_mm"] == result2["efl_mm"]


class TestThinLensFormula:
    """Validation tests against thin lens formula."""

    def test_lensmakers_equation(self):
        """Verify EFL is reasonable for a symmetric biconvex lens."""
        # Parameters for symmetric biconvex lens
        R1 = 100.0  # Front radius
        R2 = -100.0  # Back radius (negative = convex-convex)
        
        # Create thin lens (small thickness)
        surfaces = [
            Surface(surface_number=0, radius=float("inf"), thickness=float("inf")),
            Surface(surface_number=1, radius=R1, thickness=0.1, material="N-BK7"),
            Surface(surface_number=2, radius=R2, thickness=100.0, material=None),
            Surface(surface_number=3, radius=float("inf"), thickness=0.0),
        ]
        
        sg = SurfaceGroup(surfaces=surfaces, wavelengths_nm=[587.56])
        result = compute_paraxial_properties(sg)
        
        # For a symmetric biconvex lens with n~1.5 and R=100mm:
        # 1/f = (n-1)(1/R1 - 1/R2) = 0.5*(0.01-(-0.01)) = 0.5*0.02 = 0.01
        # f ~ 100mm
        # Allow wide tolerance since exact n varies and this is thick lens
        assert 50 < result["efl_mm"] < 150  # Reasonable range
