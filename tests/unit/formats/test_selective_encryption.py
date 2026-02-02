"""Test selective surface encryption."""

import pytest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from optical_blackbox.models.surface import Surface, SurfaceVisibility
from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.models.metadata import OBBMetadata
from optical_blackbox.formats.obb_file import OBBWriter, OBBReader
from optical_blackbox.crypto.keys import KeyManager


@pytest.fixture
def vendor_keypair():
    """Generate vendor keypair for testing."""
    private_key, public_key = KeyManager.generate_keypair()
    return {"private": private_key, "public": public_key}


@pytest.fixture
def platform_keypair():
    """Generate platform keypair for testing."""
    private_key, public_key = KeyManager.generate_keypair()
    return {"private": private_key, "public": public_key}


@pytest.fixture
def mixed_surface_group():
    """Create a surface group with mixed visibility levels."""
    surfaces = [
        # Public surfaces
        Surface(
            surface_number=0,
            surface_type="standard",
            visibility=SurfaceVisibility.PUBLIC,
            comment="Object surface (public)",
        ),
        Surface(
            surface_number=1,
            surface_type="standard",
            radius=50.0,
            thickness=5.0,
            visibility=SurfaceVisibility.PUBLIC,
            comment="Front lens (public)",
        ),
        # Encrypted surfaces (proprietary aspheric)
        Surface(
            surface_number=2,
            surface_type="evenasph",
            radius=25.0,
            thickness=3.0,
            conic=-0.5,
            visibility=SurfaceVisibility.ENCRYPTED,
            comment="Proprietary aspheric 1 (encrypted)",
        ),
        Surface(
            surface_number=3,
            surface_type="evenasph",
            radius=-30.0,
            thickness=2.0,
            conic=-0.8,
            visibility=SurfaceVisibility.ENCRYPTED,
            comment="Proprietary aspheric 2 (encrypted)",
        ),
        # Redacted surface
        Surface(
            surface_number=4,
            surface_type="standard",
            radius=40.0,
            thickness=10.0,
            visibility=SurfaceVisibility.REDACTED,
            comment="Secret element (redacted)",
        ),
        # Public surfaces
        Surface(
            surface_number=5,
            surface_type="standard",
            thickness=1.0,
            visibility=SurfaceVisibility.PUBLIC,
            comment="Image plane (public)",
        ),
    ]
    
    return SurfaceGroup(
        surfaces=surfaces,
        wavelengths_nm=[486.1, 587.6, 656.3],
        primary_wavelength_index=1,
        stop_surface=2,
    )


@pytest.fixture
def metadata():
    """Create test metadata."""
    return OBBMetadata(
        vendor_id="test-vendor",
        version="1.0.0",
        name="Test Selective Encryption Lens",
        efl_mm=50.0,
        na=0.25,
        diameter_mm=25.4,
        spectral_range_nm=(400.0, 700.0),
        num_surfaces=6,
    )


def test_selective_encryption_roundtrip(
    tmp_path: Path,
    mixed_surface_group: SurfaceGroup,
    metadata: OBBMetadata,
    vendor_keypair,
    platform_keypair,
):
    """Test full roundtrip of selective encryption."""
    output_path = tmp_path / "test_selective.obb"
    
    # Write with selective encryption
    OBBWriter.write_selective(
        output_path=output_path,
        surface_group=mixed_surface_group,
        metadata=metadata,
        vendor_private_key=vendor_keypair["private"],
        platform_public_key=platform_keypair["public"],
    )
    
    # Read back
    read_metadata, read_surfaces = OBBReader.read_and_decrypt_selective(
        path=output_path,
        platform_private_key=platform_keypair["private"],
        vendor_public_key=vendor_keypair["public"],
    )
    
    # Verify metadata
    assert read_metadata.vendor_id == metadata.vendor_id
    assert read_metadata.name == metadata.name
    
    # Verify all surfaces present
    assert len(read_surfaces.surfaces) == 6
    
    # Verify visibility preserved
    assert read_surfaces.surfaces[0].visibility == SurfaceVisibility.PUBLIC
    assert read_surfaces.surfaces[1].visibility == SurfaceVisibility.PUBLIC
    assert read_surfaces.surfaces[2].visibility == SurfaceVisibility.ENCRYPTED
    assert read_surfaces.surfaces[3].visibility == SurfaceVisibility.ENCRYPTED
    assert read_surfaces.surfaces[4].visibility == SurfaceVisibility.REDACTED
    assert read_surfaces.surfaces[5].visibility == SurfaceVisibility.PUBLIC
    
    # Verify encrypted surfaces decrypted correctly
    assert read_surfaces.surfaces[2].radius == 25.0
    assert read_surfaces.surfaces[2].conic == -0.5
    assert read_surfaces.surfaces[3].radius == -30.0
    assert read_surfaces.surfaces[3].conic == -0.8
    
    # Verify redacted surface is placeholder
    assert read_surfaces.surfaces[4].surface_number == 4


def test_smart_read_selective(
    tmp_path: Path,
    mixed_surface_group: SurfaceGroup,
    metadata: OBBMetadata,
    vendor_keypair,
    platform_keypair,
):
    """Test smart read auto-detects selective encryption."""
    output_path = tmp_path / "test_smart.obb"
    
    # Write with selective encryption
    OBBWriter.write_selective(
        output_path=output_path,
        surface_group=mixed_surface_group,
        metadata=metadata,
        vendor_private_key=vendor_keypair["private"],
        platform_public_key=platform_keypair["public"],
    )
    
    # Use smart read (should auto-detect)
    read_metadata, read_surfaces = OBBReader.read(
        path=output_path,
        platform_private_key=platform_keypair["private"],
        vendor_public_key=vendor_keypair["public"],
    )
    
    # Verify surfaces
    assert len(read_surfaces.surfaces) == 6
    assert read_surfaces.surfaces[2].visibility == SurfaceVisibility.ENCRYPTED


def test_surface_group_helpers(mixed_surface_group: SurfaceGroup):
    """Test SurfaceGroup helper methods."""
    # Test has_selective_encryption
    assert mixed_surface_group.has_selective_encryption() is True
    
    # Test get_public_surfaces
    public = mixed_surface_group.get_public_surfaces()
    assert len(public) == 3  # surfaces 0, 1, 5
    assert all(s.visibility == SurfaceVisibility.PUBLIC for s in public)
    
    # Test get_encrypted_surfaces
    encrypted = mixed_surface_group.get_encrypted_surfaces()
    assert len(encrypted) == 2  # surfaces 2, 3
    assert all(s.visibility == SurfaceVisibility.ENCRYPTED for s in encrypted)
    
    # Test get_redacted_surfaces
    redacted = mixed_surface_group.get_redacted_surfaces()
    assert len(redacted) == 1  # surface 4
    assert all(s.visibility == SurfaceVisibility.REDACTED for s in redacted)


def test_backward_compatibility_full_encryption(
    tmp_path: Path,
    metadata: OBBMetadata,
    vendor_keypair,
    platform_keypair,
):
    """Test that old-style full encryption still works."""
    # Create surface group without visibility flags (all default to PUBLIC)
    surfaces = [
        Surface(
            surface_number=0,
            surface_type="standard",
            comment="Surface 0",
        ),
        Surface(
            surface_number=1,
            surface_type="standard",
            radius=50.0,
            comment="Surface 1",
        ),
    ]
    surface_group = SurfaceGroup(surfaces=surfaces)
    
    # Verify no selective encryption
    assert surface_group.has_selective_encryption() is False
    
    # Write with regular encryption (not selective)
    output_path = tmp_path / "test_full.obb"
    OBBWriter.write(
        output_path=output_path,
        surface_group=surface_group,
        metadata=metadata,
        vendor_private_key=vendor_keypair["private"],
        platform_public_key=platform_keypair["public"],
    )
    
    # Read with smart read
    read_metadata, read_surfaces = OBBReader.read(
        path=output_path,
        platform_private_key=platform_keypair["private"],
        vendor_public_key=vendor_keypair["public"],
    )
    
    # Verify roundtrip
    assert len(read_surfaces.surfaces) == 2
    assert read_surfaces.surfaces[1].radius == 50.0
