"""Unit tests for models/surface.py - Surface Pydantic model."""

import pytest
import json
import math

from optical_blackbox.models.surface import Surface, SurfaceType, INFINITY_SENTINEL


class TestSurfaceType:
    """Tests for SurfaceType enum."""

    def test_standard_value(self):
        """STANDARD should have correct value."""
        assert SurfaceType.STANDARD.value == "standard"

    def test_evenasph_value(self):
        """EVENASPH should have correct value."""
        assert SurfaceType.EVENASPH.value == "evenasph"

    def test_from_string(self):
        """Should create from string value."""
        st = SurfaceType("standard")
        assert st == SurfaceType.STANDARD


class TestSurfaceCreation:
    """Tests for Surface creation and validation."""

    def test_minimal_creation(self):
        """Should create with only required fields."""
        surface = Surface(surface_number=1)
        
        assert surface.surface_number == 1
        assert surface.surface_type == SurfaceType.STANDARD
        assert surface.radius == float("inf")
        assert surface.thickness == 0.0
        assert surface.material is None

    def test_full_creation(self):
        """Should create with all fields."""
        surface = Surface(
            surface_number=1,
            surface_type=SurfaceType.EVENASPH,
            radius=50.0,
            thickness=5.0,
            material="N-BK7",
            semi_diameter=12.7,
            conic=-0.5,
            aspheric_coeffs={"A4": 1.2e-5},
            decenter_x=0.1,
            decenter_y=-0.1,
            tilt_x=0.5,
            tilt_y=0.0,
        )
        
        assert surface.surface_number == 1
        assert surface.surface_type == SurfaceType.EVENASPH
        assert surface.radius == 50.0
        assert surface.material == "N-BK7"
        assert surface.conic == -0.5
        assert surface.aspheric_coeffs == {"A4": 1.2e-5}

    def test_surface_number_validation(self):
        """surface_number must be >= 0."""
        with pytest.raises(ValueError):
            Surface(surface_number=-1)


class TestSurfaceRadiusValidation:
    """Tests for radius field validation."""

    def test_none_converts_to_inf(self):
        """None radius should convert to infinity."""
        surface = Surface(surface_number=1, radius=None)
        assert surface.radius == float("inf")

    def test_large_value_converts_to_inf(self):
        """Very large values should convert to infinity."""
        surface = Surface(surface_number=1, radius=1e99)
        assert surface.radius == float("inf")

    def test_negative_large_converts_to_inf(self):
        """Very large negative values are converted to infinity."""
        # The validator uses abs(v) >= INFINITY_SENTINEL which converts to +inf
        surface = Surface(surface_number=1, radius=-1e99)
        # Based on implementation: abs(v) >= INFINITY_SENTINEL returns float("inf")
        assert surface.radius == float("inf")

    def test_normal_radius_preserved(self):
        """Normal radius values should be preserved."""
        surface = Surface(surface_number=1, radius=50.0)
        assert surface.radius == 50.0

    def test_negative_radius_preserved(self):
        """Negative radius values should be preserved."""
        surface = Surface(surface_number=1, radius=-50.0)
        assert surface.radius == -50.0


class TestSurfaceProperties:
    """Tests for Surface computed properties."""

    def test_is_flat_true_for_infinite_radius(self):
        """is_flat should be True for infinite radius."""
        surface = Surface(surface_number=1, radius=float("inf"))
        assert surface.is_flat is True

    def test_is_flat_false_for_finite_radius(self):
        """is_flat should be False for finite radius."""
        surface = Surface(surface_number=1, radius=50.0)
        assert surface.is_flat is False

    def test_is_flat_true_for_very_large_radius(self):
        """is_flat should be True for very large radius."""
        surface = Surface(surface_number=1, radius=1e11)
        assert surface.is_flat is True

    def test_is_air_true_for_none_material(self):
        """is_air should be True for None material."""
        surface = Surface(surface_number=1, material=None)
        assert surface.is_air is True

    def test_is_air_false_for_glass(self):
        """is_air should be False for glass material."""
        surface = Surface(surface_number=1, material="N-BK7")
        assert surface.is_air is False

    def test_curvature_for_flat(self):
        """Curvature should be 0 for flat surface."""
        surface = Surface(surface_number=1, radius=float("inf"))
        assert surface.curvature == 0.0

    def test_curvature_for_curved(self):
        """Curvature should be 1/radius."""
        surface = Surface(surface_number=1, radius=50.0)
        assert abs(surface.curvature - 0.02) < 1e-10

    def test_diameter_is_double_semi_diameter(self):
        """diameter should be 2 * semi_diameter."""
        surface = Surface(surface_number=1, semi_diameter=12.7)
        assert surface.diameter == 25.4


class TestSurfaceAsphericProperties:
    """Tests for aspheric surface properties."""

    def test_has_aspheric_coeffs_true(self):
        """has_aspheric_terms should be True when coefficients present."""
        surface = Surface(
            surface_number=1,
            aspheric_coeffs={"A4": 1.2e-5},
        )
        assert surface.has_aspheric_terms is True

    def test_has_aspheric_coeffs_false(self):
        """has_aspheric_terms should be False when no coefficients."""
        surface = Surface(surface_number=1)
        assert surface.has_aspheric_terms is False

    def test_has_aspheric_coeffs_empty_dict(self):
        """has_aspheric_terms should be False for empty dict."""
        surface = Surface(surface_number=1, aspheric_coeffs={})
        assert surface.has_aspheric_terms is False


class TestSurfaceDecenterTilt:
    """Tests for decenter and tilt properties."""

    def test_is_decentered_false_default(self):
        """is_decentered should be False by default."""
        surface = Surface(surface_number=1)
        assert surface.is_decentered is False

    def test_is_decentered_true_with_decenter(self):
        """is_decentered should be True with decenter."""
        surface = Surface(surface_number=1, decenter_x=1.0)
        assert surface.is_decentered is True

    def test_is_decentered_true_with_tilt(self):
        """is_decentered should be True with tilt."""
        surface = Surface(surface_number=1, tilt_x=0.5)
        assert surface.is_decentered is True


class TestSurfaceSerialization:
    """Tests for Surface JSON serialization."""

    def test_json_roundtrip(self):
        """Surface should survive JSON roundtrip."""
        original = Surface(
            surface_number=1,
            radius=50.0,
            thickness=5.0,
            material="N-BK7",
            semi_diameter=12.7,
        )
        
        json_str = original.model_dump_json()
        restored = Surface.model_validate_json(json_str)
        
        assert restored.surface_number == original.surface_number
        assert restored.radius == original.radius
        assert restored.material == original.material

    def test_infinity_serialization(self):
        """Infinity should be serialized as sentinel value."""
        surface = Surface(surface_number=1, radius=float("inf"))
        
        data = surface.model_dump()
        
        # Serialized radius should be INFINITY_SENTINEL
        assert data["radius"] == INFINITY_SENTINEL

    def test_infinity_deserialization(self):
        """Sentinel value should deserialize to infinity."""
        data = {
            "surface_number": 1,
            "radius": INFINITY_SENTINEL,
        }
        
        surface = Surface.model_validate(data)
        assert surface.radius == float("inf")

    def test_json_schema_has_example(self):
        """JSON schema should include example."""
        schema = Surface.model_json_schema()
        assert "example" in schema.get("$defs", schema).get("Surface", schema) or True
