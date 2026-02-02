"""OBB Metadata model.

Defines the public (unencrypted) metadata stored in .obb files.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OBBMetadata(BaseModel):
    """Public metadata for .obb files.

    This information is stored unencrypted in the file header and can
    be read by anyone without the decryption key.

    Attributes:
        version: OBB format version (e.g., "1.0")
        vendor_id: Unique vendor identifier
        name: Component/product name
        efl_mm: Effective focal length in mm
        na: Numerical aperture
        diameter_mm: Maximum diameter in mm
        spectral_range_nm: Tuple of (min, max) wavelength in nm
        num_surfaces: Number of optical surfaces
        created_at: Creation timestamp
        signature: ECDSA signature of encrypted payload (base64)
        description: Optional description
        part_number: Optional vendor part number

    Example:
        >>> metadata = OBBMetadata(
        ...     vendor_id="thorlabs",
        ...     name="AC254-050-A",
        ...     efl_mm=50.0,
        ...     na=0.25,
        ...     diameter_mm=25.4,
        ...     spectral_range_nm=(400, 700),
        ...     num_surfaces=4,
        ... )
    """

    version: str = Field(
        default="1.0",
        description="OBB format version",
    )
    vendor_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique vendor identifier",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Component or product name",
    )

    # Optical properties
    efl_mm: float = Field(
        ...,
        description="Effective focal length in mm (can be inf for afocal)",
    )
    na: float = Field(
        ...,
        ge=0,
        le=1.5,
        description="Numerical aperture (0 < NA <= ~1.0 for most systems)",
    )
    diameter_mm: float = Field(
        ...,
        gt=0,
        description="Maximum diameter in mm",
    )
    spectral_range_nm: tuple[float, float] = Field(
        ...,
        description="Spectral range as (min_nm, max_nm)",
    )

    # Structure
    num_surfaces: int = Field(
        ...,
        ge=1,
        description="Number of optical surfaces",
    )

    # Timestamps
    created_at: Optional[datetime] = Field(
        default=None,
        description="Creation timestamp (UTC)",
    )

    # Security
    signature: str = Field(
        default="",
        description="ECDSA signature of encrypted payload (base64)",
    )

    # Optional info
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description of the component",
    )
    part_number: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Vendor's part number",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "version": "1.0",
                "vendor_id": "thorlabs",
                "name": "AC254-050-A",
                "efl_mm": 50.0,
                "na": 0.25,
                "diameter_mm": 25.4,
                "spectral_range_nm": (400, 700),
                "num_surfaces": 4,
                "created_at": "2026-01-30T14:32:00Z",
                "signature": "MEUCIQD...",
            }
        }
    }

    @property
    def has_signature(self) -> bool:
        """Check if signature is present."""
        return bool(self.signature)

    @property
    def spectral_range_str(self) -> str:
        """Get spectral range as formatted string."""
        return f"{self.spectral_range_nm[0]:.0f}-{self.spectral_range_nm[1]:.0f} nm"
