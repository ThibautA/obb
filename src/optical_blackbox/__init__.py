"""Optical BlackBox - Create encrypted optical component files (.obb) from Zemax designs.

This package provides tools for optical component manufacturers to distribute
their lens designs in an encrypted format that protects intellectual property
while enabling simulation on authorized platforms.

Example:
    >>> from optical_blackbox import OBBReader, OBBWriter, KeyManager
    >>> # Generate vendor keys
    >>> private_key, public_key = KeyManager.generate_keypair()
    >>> # Read metadata from .obb file
    >>> metadata = OBBReader.read_metadata("component.obb")
    >>> print(f"EFL: {metadata.efl_mm} mm")
"""

__version__ = "1.0.0"

# Public API - lazy imports for better startup time
from optical_blackbox.models.surface import Surface, SurfaceType
from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.models.metadata import OBBMetadata
from optical_blackbox.formats.obb_file import OBBReader, OBBWriter
from optical_blackbox.crypto.keys import KeyManager
from optical_blackbox.crypto.hybrid import OBBEncryptor, OBBSigner

__all__ = [
    # Version
    "__version__",
    # Models
    "Surface",
    "SurfaceType",
    "SurfaceGroup",
    "OBBMetadata",
    # Format
    "OBBReader",
    "OBBWriter",
    # Crypto
    "KeyManager",
    "OBBEncryptor",
    "OBBSigner",
]
