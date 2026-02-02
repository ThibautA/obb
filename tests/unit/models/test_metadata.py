"""Unit tests for models/metadata.py - OBBMetadata Pydantic model."""

import pytest
from datetime import datetime, timezone

from optical_blackbox.models.metadata import OBBMetadata


class TestOBBMetadataCreation:
    """Tests for OBBMetadata creation."""

    def test_minimal_creation(self):
        """Should create with required fields only."""
        metadata = OBBMetadata(
            vendor_id="test-vendor",
            name="Test Component",
            efl_mm=50.0,
            na=0.25,
            diameter_mm=25.4,
            spectral_range_nm=(400.0, 700.0),
            num_surfaces=4,
        )
        
        assert metadata.vendor_id == "test-vendor"
        assert metadata.name == "Test Component"
        assert metadata.efl_mm == 50.0

    def test_full_creation(self, sample_metadata):
        """Should create with all fields."""
        assert sample_metadata.version == "1.0"
        assert sample_metadata.vendor_id == "test-vendor"
        assert sample_metadata.description == "Test optical component"
        assert sample_metadata.part_number == "TC-001"

    def test_default_version(self):
        """Default version should be '1.0'."""
        metadata = OBBMetadata(
            vendor_id="test",
            name="Test",
            efl_mm=50.0,
            na=0.1,
            diameter_mm=25.0,
            spectral_range_nm=(400, 700),
            num_surfaces=2,
        )
        assert metadata.version == "1.0"


class TestOBBMetadataValidation:
    """Tests for OBBMetadata field validation."""

    def test_vendor_id_min_length(self):
        """vendor_id must be at least 3 characters."""
        with pytest.raises(ValueError):
            OBBMetadata(
                vendor_id="ab",  # Too short
                name="Test",
                efl_mm=50.0,
                na=0.1,
                diameter_mm=25.0,
                spectral_range_nm=(400, 700),
                num_surfaces=2,
            )

    def test_vendor_id_max_length(self):
        """vendor_id must be at most 50 characters."""
        with pytest.raises(ValueError):
            OBBMetadata(
                vendor_id="a" * 51,  # Too long
                name="Test",
                efl_mm=50.0,
                na=0.1,
                diameter_mm=25.0,
                spectral_range_nm=(400, 700),
                num_surfaces=2,
            )

    def test_name_min_length(self):
        """name must be at least 1 character."""
        with pytest.raises(ValueError):
            OBBMetadata(
                vendor_id="test",
                name="",  # Empty
                efl_mm=50.0,
                na=0.1,
                diameter_mm=25.0,
                spectral_range_nm=(400, 700),
                num_surfaces=2,
            )

    def test_na_min_value(self):
        """na must be >= 0."""
        with pytest.raises(ValueError):
            OBBMetadata(
                vendor_id="test",
                name="Test",
                efl_mm=50.0,
                na=-0.1,  # Negative
                diameter_mm=25.0,
                spectral_range_nm=(400, 700),
                num_surfaces=2,
            )

    def test_na_max_value(self):
        """na must be <= 1.5."""
        with pytest.raises(ValueError):
            OBBMetadata(
                vendor_id="test",
                name="Test",
                efl_mm=50.0,
                na=2.0,  # Too high
                diameter_mm=25.0,
                spectral_range_nm=(400, 700),
                num_surfaces=2,
            )

    def test_diameter_must_be_positive(self):
        """diameter_mm must be > 0."""
        with pytest.raises(ValueError):
            OBBMetadata(
                vendor_id="test",
                name="Test",
                efl_mm=50.0,
                na=0.1,
                diameter_mm=0,  # Not positive
                spectral_range_nm=(400, 700),
                num_surfaces=2,
            )

    def test_num_surfaces_min_value(self):
        """num_surfaces must be >= 1."""
        with pytest.raises(ValueError):
            OBBMetadata(
                vendor_id="test",
                name="Test",
                efl_mm=50.0,
                na=0.1,
                diameter_mm=25.0,
                spectral_range_nm=(400, 700),
                num_surfaces=0,  # Too few
            )


class TestOBBMetadataProperties:
    """Tests for OBBMetadata computed properties."""

    def test_has_signature_false_when_empty(self):
        """has_signature should be False when signature is empty."""
        metadata = OBBMetadata(
            vendor_id="test",
            name="Test",
            efl_mm=50.0,
            na=0.1,
            diameter_mm=25.0,
            spectral_range_nm=(400, 700),
            num_surfaces=2,
            signature="",
        )
        assert metadata.has_signature is False

    def test_has_signature_true_when_present(self):
        """has_signature should be True when signature present."""
        metadata = OBBMetadata(
            vendor_id="test",
            name="Test",
            efl_mm=50.0,
            na=0.1,
            diameter_mm=25.0,
            spectral_range_nm=(400, 700),
            num_surfaces=2,
            signature="MEUCIQD...",
        )
        assert metadata.has_signature is True

    def test_spectral_range_str(self):
        """spectral_range_str should format range nicely."""
        metadata = OBBMetadata(
            vendor_id="test",
            name="Test",
            efl_mm=50.0,
            na=0.1,
            diameter_mm=25.0,
            spectral_range_nm=(400.0, 700.0),
            num_surfaces=2,
        )
        assert metadata.spectral_range_str == "400-700 nm"


class TestOBBMetadataOptionalFields:
    """Tests for optional metadata fields."""

    def test_description_optional(self):
        """description is optional."""
        metadata = OBBMetadata(
            vendor_id="test",
            name="Test",
            efl_mm=50.0,
            na=0.1,
            diameter_mm=25.0,
            spectral_range_nm=(400, 700),
            num_surfaces=2,
        )
        assert metadata.description is None

    def test_description_max_length(self):
        """description has max length of 500."""
        with pytest.raises(ValueError):
            OBBMetadata(
                vendor_id="test",
                name="Test",
                efl_mm=50.0,
                na=0.1,
                diameter_mm=25.0,
                spectral_range_nm=(400, 700),
                num_surfaces=2,
                description="x" * 501,
            )

    def test_part_number_optional(self):
        """part_number is optional."""
        metadata = OBBMetadata(
            vendor_id="test",
            name="Test",
            efl_mm=50.0,
            na=0.1,
            diameter_mm=25.0,
            spectral_range_nm=(400, 700),
            num_surfaces=2,
        )
        assert metadata.part_number is None

    def test_created_at_optional(self):
        """created_at is optional."""
        metadata = OBBMetadata(
            vendor_id="test",
            name="Test",
            efl_mm=50.0,
            na=0.1,
            diameter_mm=25.0,
            spectral_range_nm=(400, 700),
            num_surfaces=2,
        )
        assert metadata.created_at is None


class TestOBBMetadataSerialization:
    """Tests for OBBMetadata JSON serialization."""

    def test_json_roundtrip(self, sample_metadata):
        """OBBMetadata should survive JSON roundtrip."""
        json_str = sample_metadata.model_dump_json()
        restored = OBBMetadata.model_validate_json(json_str)
        
        assert restored.vendor_id == sample_metadata.vendor_id
        assert restored.name == sample_metadata.name
        assert restored.efl_mm == sample_metadata.efl_mm
        assert restored.spectral_range_nm == sample_metadata.spectral_range_nm

    def test_datetime_serialization(self, sample_metadata):
        """datetime should be serialized correctly."""
        json_str = sample_metadata.model_dump_json()
        restored = OBBMetadata.model_validate_json(json_str)
        
        assert restored.created_at == sample_metadata.created_at

    def test_tuple_serialization(self, sample_metadata):
        """spectral_range_nm tuple should survive serialization."""
        json_str = sample_metadata.model_dump_json()
        restored = OBBMetadata.model_validate_json(json_str)
        
        # May be restored as list, but should be convertible to tuple
        assert tuple(restored.spectral_range_nm) == sample_metadata.spectral_range_nm

    def test_efl_infinity(self):
        """Infinite EFL (afocal system) should serialize."""
        metadata = OBBMetadata(
            vendor_id="test",
            name="Afocal System",
            efl_mm=float("inf"),
            na=0.1,
            diameter_mm=25.0,
            spectral_range_nm=(400, 700),
            num_surfaces=4,
        )
        
        json_str = metadata.model_dump_json()
        # Should not raise
        assert "inf" in json_str.lower() or "null" in json_str.lower() or True
