"""Shared pytest fixtures for OpticalBlackBox tests.

Provides common fixtures for cryptographic keys, surface models,
metadata, and test file generation.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import ec

from optical_blackbox.crypto.keys import KeyManager
from optical_blackbox.models.surface import Surface, SurfaceType
from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.models.metadata import OBBMetadata


# =============================================================================
# Cryptographic Fixtures
# =============================================================================


@pytest.fixture
def vendor_keypair() -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """Generate a vendor ECDSA P-256 keypair for tests."""
    return KeyManager.generate_keypair()


@pytest.fixture
def platform_keypair() -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """Generate a platform ECDSA P-256 keypair for tests."""
    return KeyManager.generate_keypair()


@pytest.fixture
def vendor_private_key(vendor_keypair) -> ec.EllipticCurvePrivateKey:
    """Get vendor private key."""
    return vendor_keypair[0]


@pytest.fixture
def vendor_public_key(vendor_keypair) -> ec.EllipticCurvePublicKey:
    """Get vendor public key."""
    return vendor_keypair[1]


@pytest.fixture
def platform_private_key(platform_keypair) -> ec.EllipticCurvePrivateKey:
    """Get platform private key."""
    return platform_keypair[0]


@pytest.fixture
def platform_public_key(platform_keypair) -> ec.EllipticCurvePublicKey:
    """Get platform public key."""
    return platform_keypair[1]


@pytest.fixture
def aes_key() -> bytes:
    """Generate a valid 32-byte AES-256 key."""
    import os
    return os.urandom(32)


@pytest.fixture
def aes_nonce() -> bytes:
    """Generate a valid 12-byte AES-GCM nonce."""
    import os
    return os.urandom(12)


# =============================================================================
# Model Fixtures
# =============================================================================


@pytest.fixture
def flat_surface() -> Surface:
    """Create a flat surface (object plane)."""
    return Surface(
        surface_number=0,
        surface_type=SurfaceType.STANDARD,
        radius=float("inf"),
        thickness=float("inf"),
        material=None,
    )


@pytest.fixture
def spherical_surface() -> Surface:
    """Create a simple spherical surface."""
    return Surface(
        surface_number=1,
        surface_type=SurfaceType.STANDARD,
        radius=50.0,
        thickness=5.0,
        material="N-BK7",
        semi_diameter=12.7,
        conic=0.0,
    )


@pytest.fixture
def aspheric_surface() -> Surface:
    """Create an even asphere surface."""
    return Surface(
        surface_number=2,
        surface_type=SurfaceType.EVENASPH,
        radius=25.0,
        thickness=3.0,
        material="N-SF11",
        semi_diameter=10.0,
        conic=-0.5,
        aspheric_coeffs={"A4": 1.2e-5, "A6": -3.4e-8},
    )


@pytest.fixture
def image_surface() -> Surface:
    """Create an image plane surface."""
    return Surface(
        surface_number=3,
        surface_type=SurfaceType.STANDARD,
        radius=float("inf"),
        thickness=0.0,
        material=None,
    )


@pytest.fixture
def simple_lens_surfaces(flat_surface, spherical_surface, image_surface) -> list[Surface]:
    """Create surfaces for a simple lens."""
    # Front surface
    front = Surface(
        surface_number=1,
        radius=100.0,
        thickness=5.0,
        material="N-BK7",
        semi_diameter=12.7,
    )
    # Back surface
    back = Surface(
        surface_number=2,
        radius=-100.0,
        thickness=45.0,  # BFL
        material=None,
        semi_diameter=12.7,
    )
    return [flat_surface, front, back, image_surface]


@pytest.fixture
def sample_surface_group(simple_lens_surfaces) -> SurfaceGroup:
    """Create a sample SurfaceGroup representing a simple lens."""
    return SurfaceGroup(
        surfaces=simple_lens_surfaces,
        wavelengths_nm=[486.13, 587.56, 656.27],
        primary_wavelength_index=1,
        stop_surface=1,
    )


@pytest.fixture
def minimal_surface_group(spherical_surface) -> SurfaceGroup:
    """Create a minimal SurfaceGroup with one surface."""
    return SurfaceGroup(
        surfaces=[spherical_surface],
        wavelengths_nm=[587.56],
    )


@pytest.fixture
def sample_metadata() -> OBBMetadata:
    """Create sample OBBMetadata."""
    return OBBMetadata(
        version="1.0",
        vendor_id="test-vendor",
        name="Test Component AC254-050",
        efl_mm=50.0,
        na=0.25,
        diameter_mm=25.4,
        spectral_range_nm=(400.0, 700.0),
        num_surfaces=4,
        created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        description="Test optical component",
        part_number="TC-001",
    )


# =============================================================================
# File Fixtures
# =============================================================================


@pytest.fixture
def minimal_zmx_content() -> str:
    """Minimal valid Zemax .zmx file content."""
    return """\
VERS 140710 100 37889
MODE SEQ
NAME Simple lens
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1.0E+10
  DISZ 0
SURF 1
  TYPE STANDARD
  CURV 0.01
  THIC 5.0
  GLAS N-BK7
  DIAM 25.4
SURF 2
  TYPE STANDARD
  CURV -0.01
  THIC 45.0
  DIAM 25.4
SURF 3
  TYPE STANDARD
  CURV 0.0
  THIC 0.0
  DIAM 0
"""


@pytest.fixture
def tmp_zmx_file(tmp_path, minimal_zmx_content) -> Path:
    """Create a temporary .zmx file for testing."""
    zmx_path = tmp_path / "test_lens.zmx"
    # Write as UTF-16-LE which is standard Zemax encoding
    zmx_path.write_text(minimal_zmx_content, encoding="utf-16-le")
    return zmx_path


@pytest.fixture
def tmp_obb_file(tmp_path) -> Path:
    """Provide a temporary path for .obb file output."""
    return tmp_path / "test_output.obb"


@pytest.fixture
def tmp_key_dir(tmp_path) -> Path:
    """Create a temporary directory for key files."""
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    return key_dir


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_plaintext() -> bytes:
    """Sample plaintext data for encryption tests."""
    return b"This is test data for encryption testing. It contains some text."


@pytest.fixture
def large_plaintext() -> bytes:
    """Large plaintext data (1MB) for stress testing."""
    return b"X" * (1024 * 1024)


@pytest.fixture
def empty_plaintext() -> bytes:
    """Empty plaintext for edge case testing."""
    return b""
