"""Unit tests for optics/glass_catalog.py - Glass refractive index lookup."""

import pytest

from optical_blackbox.optics.glass_catalog import (
    get_refractive_index,
    is_material_known,
    list_materials,
    GLASS_CATALOG,
)
from optical_blackbox.core.constants import AIR_INDEX, DEFAULT_UNKNOWN_INDEX


class TestGetRefractiveIndex:
    """Tests for refractive index lookup."""

    def test_air_returns_one(self):
        """Air (None) should return 1.0."""
        assert get_refractive_index(None) == AIR_INDEX
        assert get_refractive_index("") == AIR_INDEX
        assert get_refractive_index("   ") == AIR_INDEX

    def test_nbk7_index(self):
        """N-BK7 should return correct index at d-line."""
        n = get_refractive_index("N-BK7")
        assert abs(n - 1.5168) < 0.001

    def test_case_insensitive(self):
        """Lookup should be case insensitive."""
        n_upper = get_refractive_index("N-BK7")
        n_lower = get_refractive_index("n-bk7")
        n_mixed = get_refractive_index("N-Bk7")
        
        assert n_upper == n_lower == n_mixed

    def test_legacy_name_matching(self):
        """Should match legacy names without prefix."""
        # BK7 should match N-BK7
        n_legacy = get_refractive_index("BK7")
        n_full = get_refractive_index("N-BK7")
        
        assert n_legacy == n_full

    def test_normalized_matching(self):
        """Should match with hyphens/spaces removed."""
        # NBK7 should match N-BK7
        n_no_hyphen = get_refractive_index("NBK7")
        n_with_hyphen = get_refractive_index("N-BK7")
        
        assert n_no_hyphen == n_with_hyphen

    def test_unknown_material_returns_default(self):
        """Unknown material should return default index."""
        n = get_refractive_index("UNKNOWN_GLASS_XYZ")
        assert n == DEFAULT_UNKNOWN_INDEX  # 1.5

    def test_wavelength_ignored_in_mvp(self):
        """MVP ignores wavelength (always returns d-line value)."""
        # Different wavelengths should return same value in MVP
        n_visible = get_refractive_index("N-BK7", wavelength_nm=587.56)
        n_blue = get_refractive_index("N-BK7", wavelength_nm=486.13)
        n_red = get_refractive_index("N-BK7", wavelength_nm=656.27)
        
        # MVP returns same value for all wavelengths
        assert n_visible == n_blue == n_red

    @pytest.mark.parametrize("material,expected_n", [
        ("N-BK7", 1.5168),
        ("N-SF11", 1.7847),
        ("N-SF6", 1.8052),
        ("SILICA", 1.4585),
        ("FUSED_SILICA", 1.4585),
        ("CAF2", 1.4338),
        ("SAPPHIRE", 1.7682),
        ("F2", 1.6200),
    ])
    def test_common_glasses(self, material, expected_n):
        """Test common glass materials."""
        n = get_refractive_index(material)
        assert abs(n - expected_n) < 0.001


class TestIsMaterialKnown:
    """Tests for material existence check."""

    def test_known_material(self):
        """Known materials should return True."""
        assert is_material_known("N-BK7") is True
        assert is_material_known("SILICA") is True

    def test_unknown_material(self):
        """Unknown materials should return False."""
        assert is_material_known("UNKNOWN_GLASS") is False
        assert is_material_known("XYZ123") is False

    def test_case_insensitive(self):
        """Check should be case insensitive."""
        assert is_material_known("n-bk7") is True
        assert is_material_known("N-BK7") is True


class TestListMaterials:
    """Tests for listing available materials."""

    def test_returns_list(self):
        """Should return a list."""
        materials = list_materials()
        assert isinstance(materials, list)

    def test_not_empty(self):
        """Should contain materials."""
        materials = list_materials()
        assert len(materials) > 0

    def test_contains_common_glasses(self):
        """Should contain common optical glasses."""
        materials = list_materials()
        
        # Check for some common glasses (case may vary)
        material_upper = [m.upper() for m in materials]
        assert "N-BK7" in material_upper
        assert "SILICA" in material_upper


class TestGlassCatalogCompleteness:
    """Tests for glass catalog completeness."""

    def test_schott_crown_glasses(self):
        """Catalog should include Schott crown glasses."""
        crown_glasses = ["N-BK7", "N-K5", "N-SK16"]
        for glass in crown_glasses:
            assert glass in GLASS_CATALOG, f"{glass} missing from catalog"

    def test_schott_flint_glasses(self):
        """Catalog should include Schott flint glasses."""
        flint_glasses = ["N-SF11", "N-SF6", "SF5", "F2"]
        for glass in flint_glasses:
            assert glass in GLASS_CATALOG, f"{glass} missing from catalog"

    def test_common_materials(self):
        """Catalog should include common optical materials."""
        materials = ["SILICA", "CAF2", "SAPPHIRE"]
        for mat in materials:
            assert mat in GLASS_CATALOG, f"{mat} missing from catalog"

    def test_all_indices_positive(self):
        """All indices should be positive."""
        for name, index in GLASS_CATALOG.items():
            assert index > 0, f"{name} has non-positive index"

    def test_all_indices_reasonable(self):
        """All indices should be within reasonable range (1.3-4.5)."""
        for name, index in GLASS_CATALOG.items():
            assert 1.3 <= index <= 4.5, f"{name} has unusual index {index}"
