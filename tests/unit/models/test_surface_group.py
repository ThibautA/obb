"""Unit tests for models/surface_group.py - SurfaceGroup Pydantic model."""

import pytest

from optical_blackbox.models.surface import Surface, SurfaceType
from optical_blackbox.models.surface_group import SurfaceGroup


class TestSurfaceGroupCreation:
    """Tests for SurfaceGroup creation."""

    def test_minimal_creation(self, spherical_surface):
        """Should create with minimum required fields."""
        sg = SurfaceGroup(surfaces=[spherical_surface])
        
        assert sg.num_surfaces == 1
        assert len(sg.surfaces) == 1

    def test_surfaces_required(self):
        """surfaces field is required."""
        with pytest.raises(ValueError):
            SurfaceGroup()

    def test_surfaces_min_length(self):
        """surfaces must have at least 1 element."""
        with pytest.raises(ValueError):
            SurfaceGroup(surfaces=[])

    def test_full_creation(self, simple_lens_surfaces):
        """Should create with all fields."""
        sg = SurfaceGroup(
            surfaces=simple_lens_surfaces,
            stop_surface=1,
            wavelengths_nm=[486.13, 587.56, 656.27],
            primary_wavelength_index=1,
            field_type="angle",
            max_field=5.0,
        )
        
        assert sg.num_surfaces == len(simple_lens_surfaces)
        assert sg.stop_surface == 1
        assert len(sg.wavelengths_nm) == 3


class TestSurfaceGroupComputedFields:
    """Tests for computed fields."""

    def test_num_surfaces(self, sample_surface_group):
        """num_surfaces should return count of surfaces."""
        assert sample_surface_group.num_surfaces == len(sample_surface_group.surfaces)

    def test_total_length_excludes_infinity(self, sample_surface_group):
        """total_length should exclude infinite thicknesses."""
        total = sample_surface_group.total_length
        
        # Should be sum of finite thicknesses
        expected = sum(
            s.thickness for s in sample_surface_group.surfaces[:-1]
            if s.thickness != float("inf")
        )
        assert abs(total - expected) < 0.001

    def test_total_length_excludes_last_surface(self):
        """total_length should exclude last surface thickness."""
        surfaces = [
            Surface(surface_number=0, thickness=10.0),
            Surface(surface_number=1, thickness=5.0),
            Surface(surface_number=2, thickness=100.0),  # Last - should be excluded
        ]
        sg = SurfaceGroup(surfaces=surfaces)
        
        # Total should be 10 + 5 = 15, not 115
        assert sg.total_length == 15.0

    def test_total_length_single_surface(self, spherical_surface):
        """total_length with single surface should be 0."""
        sg = SurfaceGroup(surfaces=[spherical_surface])
        assert sg.total_length == 0.0


class TestSurfaceGroupWavelengths:
    """Tests for wavelength-related properties."""

    def test_default_wavelength(self, spherical_surface):
        """Default wavelength should be d-line (587.56 nm)."""
        sg = SurfaceGroup(surfaces=[spherical_surface])
        assert sg.wavelengths_nm == [587.56]

    def test_primary_wavelength(self, sample_surface_group):
        """primary_wavelength should return correct wavelength."""
        # primary_wavelength_index = 1, wavelengths = [486.13, 587.56, 656.27]
        assert sample_surface_group.primary_wavelength == 587.56

    def test_primary_wavelength_fallback(self):
        """Should fallback to first wavelength if index out of range."""
        surfaces = [Surface(surface_number=1)]
        sg = SurfaceGroup(
            surfaces=surfaces,
            wavelengths_nm=[550.0],
            primary_wavelength_index=10,  # Out of range
        )
        assert sg.primary_wavelength == 550.0

    def test_spectral_range(self, sample_surface_group):
        """spectral_range should return (min, max) wavelengths."""
        min_wl, max_wl = sample_surface_group.spectral_range
        
        assert min_wl == min(sample_surface_group.wavelengths_nm)
        assert max_wl == max(sample_surface_group.wavelengths_nm)

    def test_spectral_range_single_wavelength(self, spherical_surface):
        """spectral_range with single wavelength."""
        sg = SurfaceGroup(surfaces=[spherical_surface], wavelengths_nm=[587.56])
        min_wl, max_wl = sg.spectral_range
        
        assert min_wl == max_wl == 587.56


class TestSurfaceGroupMaxDiameter:
    """Tests for max_diameter property."""

    def test_max_diameter_returns_largest(self):
        """max_diameter should return largest surface diameter."""
        surfaces = [
            Surface(surface_number=0, semi_diameter=10.0),
            Surface(surface_number=1, semi_diameter=15.0),
            Surface(surface_number=2, semi_diameter=12.0),
        ]
        sg = SurfaceGroup(surfaces=surfaces)
        
        # Max semi_diameter is 15, so diameter is 30
        assert sg.max_diameter == 30.0

    def test_max_diameter_empty_surfaces(self, spherical_surface):
        """max_diameter with zero semi_diameters."""
        sg = SurfaceGroup(surfaces=[Surface(surface_number=0, semi_diameter=0.0)])
        assert sg.max_diameter == 0.0


class TestSurfaceGroupMethods:
    """Tests for SurfaceGroup methods."""

    def test_get_surface_by_index(self, sample_surface_group):
        """get_surface should return surface at index."""
        surface = sample_surface_group.get_surface(0)
        assert surface == sample_surface_group.surfaces[0]

    def test_get_surface_out_of_range(self, sample_surface_group):
        """get_surface with out of range index should raise."""
        with pytest.raises(IndexError):
            sample_surface_group.get_surface(100)

    def test_iter_optical_surfaces_skips_object(self, sample_surface_group):
        """iter_optical_surfaces should skip object plane."""
        optical_surfaces = list(sample_surface_group.iter_optical_surfaces())
        
        # Should skip surface 0 with infinite thickness
        for surface in optical_surfaces:
            # Object plane typically has infinite thickness
            if surface.surface_number == 0:
                assert surface.thickness != float("inf")


class TestSurfaceGroupSerialization:
    """Tests for SurfaceGroup JSON serialization."""

    def test_json_roundtrip_finite_values(self):
        """SurfaceGroup should survive JSON roundtrip with finite values."""
        # Use finite values to avoid JSON infinity issues
        surfaces = [
            Surface(surface_number=0, thickness=0.0),
            Surface(surface_number=1, radius=50.0, thickness=5.0, material="N-BK7"),
            Surface(surface_number=2, radius=-50.0, thickness=10.0, material=None),
        ]
        sg = SurfaceGroup(surfaces=surfaces, wavelengths_nm=[587.56])
        
        json_str = sg.model_dump_json()
        restored = SurfaceGroup.model_validate_json(json_str)
        
        assert restored.num_surfaces == sg.num_surfaces
        assert restored.wavelengths_nm == sg.wavelengths_nm
        assert len(restored.surfaces) == len(sg.surfaces)

    def test_surfaces_preserved_in_json_finite(self):
        """Surface properties should be preserved in JSON with finite values."""
        surfaces = [
            Surface(surface_number=0, thickness=0.0),
            Surface(surface_number=1, radius=100.0, thickness=5.0, material="N-BK7"),
        ]
        sg = SurfaceGroup(surfaces=surfaces, wavelengths_nm=[587.56])
        
        json_str = sg.model_dump_json()
        restored = SurfaceGroup.model_validate_json(json_str)
        
        for orig, rest in zip(sg.surfaces, restored.surfaces):
            assert rest.surface_number == orig.surface_number
            assert rest.material == orig.material

    def test_computed_fields_in_dump(self, sample_surface_group):
        """Computed fields should appear in model_dump."""
        data = sample_surface_group.model_dump()
        
        assert "num_surfaces" in data
        assert "total_length" in data
