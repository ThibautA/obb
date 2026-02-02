"""Unit tests for parsers/zemax/zmx_surface_mapper.py - Surface mapping."""

import pytest

from optical_blackbox.parsers.zemax.zmx_surface_mapper import (
    map_surface_type,
    parse_radius_from_curvature,
    parse_thickness,
    build_aspheric_coeffs,
    build_surface,
)
from optical_blackbox.models.surface import Surface, SurfaceType
from optical_blackbox.exceptions import UnsupportedSurfaceTypeError


class TestMapSurfaceType:
    """Tests for surface type mapping."""

    @pytest.mark.parametrize("zemax_type,expected", [
        ("STANDARD", SurfaceType.STANDARD),
        ("standard", SurfaceType.STANDARD),
        ("Standard", SurfaceType.STANDARD),
        ("EVENASPH", SurfaceType.EVENASPH),
        ("evenasph", SurfaceType.EVENASPH),
    ])
    def test_valid_surface_types(self, zemax_type, expected):
        """Should map valid Zemax types to OBB types."""
        result = map_surface_type(zemax_type)
        assert result == expected

    def test_unsupported_type_raises_error(self):
        """Unsupported surface type should raise error."""
        with pytest.raises(UnsupportedSurfaceTypeError):
            map_surface_type("UNKNOWN_TYPE")

    def test_unsupported_zernike_raises_error(self):
        """Zernike surfaces not yet supported."""
        with pytest.raises(UnsupportedSurfaceTypeError):
            map_surface_type("ZERNIKE")


class TestParseRadiusFromCurvature:
    """Tests for curvature to radius conversion."""

    def test_positive_curvature(self):
        """Positive curvature should give positive radius."""
        # Curvature 0.02 → Radius 50.0
        result = parse_radius_from_curvature(0.02)
        assert abs(result - 50.0) < 1e-10

    def test_negative_curvature(self):
        """Negative curvature should give negative radius."""
        # Curvature -0.04 → Radius -25.0
        result = parse_radius_from_curvature(-0.04)
        assert abs(result - (-25.0)) < 1e-10

    def test_zero_curvature(self):
        """Zero curvature should give infinite radius."""
        result = parse_radius_from_curvature(0.0)
        assert result == float("inf")

    def test_very_small_curvature(self):
        """Very small curvature should give infinite radius."""
        result = parse_radius_from_curvature(1e-20)
        assert result == float("inf")


class TestParseThickness:
    """Tests for thickness parsing."""

    @pytest.mark.parametrize("value,expected", [
        ("5.0", 5.0),
        ("0.0", 0.0),
        ("-10.5", -10.5),
        ("1.2e-3", 1.2e-3),
    ])
    def test_numeric_values(self, value, expected):
        """Should parse numeric thickness values."""
        result = parse_thickness(value)
        assert abs(result - expected) < 1e-15

    @pytest.mark.parametrize("value", [
        "INFINITY",
        "infinity",
        "Infinity",
        "INF",
        "inf",
        "1.0E+10",
        "1E+10",
        "1E10",
    ])
    def test_infinity_values(self, value):
        """Should parse infinity thickness values."""
        result = parse_thickness(value)
        assert result == float("inf")

    def test_whitespace_stripped(self):
        """Should strip whitespace."""
        result = parse_thickness("  INFINITY  ")
        assert result == float("inf")


class TestBuildAsphericCoeffs:
    """Tests for aspheric coefficient building."""

    def test_empty_parm_returns_none(self):
        """Empty PARM dict should return None."""
        result = build_aspheric_coeffs({})
        assert result is None

    def test_single_coefficient(self):
        """Should build single coefficient."""
        parm = {2: 1.2e-5}  # PARM 2 → A4
        result = build_aspheric_coeffs(parm)
        
        assert result is not None
        assert "A4" in result
        assert abs(result["A4"] - 1.2e-5) < 1e-15

    def test_multiple_coefficients(self):
        """Should build multiple coefficients."""
        parm = {
            1: 0.0,      # PARM 1 → A2 (will be skipped if zero)
            2: 1.2e-5,   # PARM 2 → A4
            3: -3.4e-8,  # PARM 3 → A6
        }
        result = build_aspheric_coeffs(parm)
        
        assert result is not None
        assert "A4" in result
        assert "A6" in result

    def test_negligible_values_skipped(self):
        """Should skip negligible coefficient values."""
        parm = {2: 1e-35}  # Very small, effectively zero
        result = build_aspheric_coeffs(parm)
        
        # Should return None since all values are negligible
        assert result is None

    def test_parm_index_mapping(self):
        """Should correctly map PARM indices to coefficient names."""
        # PARM 1 → A2, PARM 2 → A4, PARM 3 → A6, etc.
        parm = {
            1: 1.0,
            2: 2.0,
            3: 3.0,
            4: 4.0,
        }
        result = build_aspheric_coeffs(parm)
        
        assert "A2" in result
        assert "A4" in result
        assert "A6" in result
        assert "A8" in result


class TestBuildSurface:
    """Tests for Surface object building."""

    def test_build_standard_surface(self):
        """Should build standard surface from data dict."""
        data = {
            "number": 1,
            "type": "STANDARD",
            "curvature": 0.02,  # Radius = 50
            "thickness": 5.0,
            "material": "N-BK7",
            "semi_diameter": 12.7,
            "conic": 0.0,
            "parm": {},
            "decenter_x": 0.0,
            "decenter_y": 0.0,
            "tilt_x": 0.0,
            "tilt_y": 0.0,
        }
        
        result = build_surface(data)
        
        assert isinstance(result, Surface)
        assert result.surface_number == 1
        assert result.surface_type == SurfaceType.STANDARD
        assert abs(result.radius - 50.0) < 0.01
        assert result.thickness == 5.0
        assert result.material == "N-BK7"

    def test_build_asphere_surface(self):
        """Should build asphere surface with coefficients."""
        data = {
            "number": 2,
            "type": "EVENASPH",
            "curvature": 0.04,
            "thickness": 3.0,
            "material": "N-SF11",
            "semi_diameter": 10.0,
            "conic": -0.5,
            "parm": {2: 1.2e-5, 3: -3.4e-8},
            "decenter_x": 0.0,
            "decenter_y": 0.0,
            "tilt_x": 0.0,
            "tilt_y": 0.0,
        }
        
        result = build_surface(data)
        
        assert result.surface_type == SurfaceType.EVENASPH
        assert result.conic == -0.5
        assert result.aspheric_coeffs is not None
        assert "A4" in result.aspheric_coeffs

    def test_build_flat_surface(self):
        """Should build flat surface (zero curvature)."""
        data = {
            "number": 0,
            "type": "STANDARD",
            "curvature": 0.0,
            "thickness": float("inf"),
            "material": None,
            "semi_diameter": 0.0,
            "conic": 0.0,
            "parm": {},
            "decenter_x": 0.0,
            "decenter_y": 0.0,
            "tilt_x": 0.0,
            "tilt_y": 0.0,
        }
        
        result = build_surface(data)
        
        assert result.is_flat
        assert result.is_air

    def test_build_surface_with_decenter(self):
        """Should include decenter values."""
        data = {
            "number": 1,
            "type": "STANDARD",
            "curvature": 0.02,
            "thickness": 5.0,
            "material": None,
            "semi_diameter": 12.7,
            "conic": 0.0,
            "parm": {},
            "decenter_x": 1.5,
            "decenter_y": -0.5,
            "tilt_x": 0.0,
            "tilt_y": 0.0,
        }
        
        result = build_surface(data)
        
        assert result.decenter_x == 1.5
        assert result.decenter_y == -0.5
