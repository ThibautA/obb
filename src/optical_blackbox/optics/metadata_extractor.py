"""Metadata extractor for optical systems.

Extracts OBBMetadata from a SurfaceGroup by computing optical properties.
"""

from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.models.metadata import OBBMetadata
from optical_blackbox.optics.paraxial import compute_paraxial_properties


def extract_metadata(
    surface_group: SurfaceGroup,
    vendor_id: str,
    name: str,
    description: str | None = None,
    part_number: str | None = None,
) -> OBBMetadata:
    """Extract OBBMetadata from a SurfaceGroup.

    Computes optical properties (EFL, NA) and extracts structural info.

    Args:
        surface_group: Source optical surfaces
        vendor_id: Vendor identifier
        name: Component name
        description: Optional description
        part_number: Optional part number

    Returns:
        Populated OBBMetadata
    """
    # Compute paraxial properties
    paraxial = compute_paraxial_properties(surface_group)

    # Get max diameter
    max_diameter = surface_group.max_diameter

    # Get spectral range
    spectral_range = surface_group.spectral_range

    return OBBMetadata(
        version="1.0",
        vendor_id=vendor_id,
        name=name,
        efl_mm=paraxial["efl_mm"],
        na=paraxial["na"],
        diameter_mm=round(max_diameter, 2),
        spectral_range_nm=spectral_range,
        num_surfaces=surface_group.num_surfaces,
        created_at=None,  # Set at write time
        signature="",  # Set at write time
        description=description,
        part_number=part_number,
    )


def update_metadata_from_surfaces(
    metadata: OBBMetadata,
    surface_group: SurfaceGroup,
) -> OBBMetadata:
    """Update metadata with computed values from surfaces.

    Useful when metadata was partially filled and needs optical properties.

    Args:
        metadata: Existing metadata (will not be modified)
        surface_group: Source surfaces

    Returns:
        New metadata with updated optical properties
    """
    paraxial = compute_paraxial_properties(surface_group)

    return OBBMetadata(
        version=metadata.version,
        vendor_id=metadata.vendor_id,
        name=metadata.name,
        efl_mm=paraxial["efl_mm"],
        na=paraxial["na"],
        diameter_mm=round(surface_group.max_diameter, 2),
        spectral_range_nm=surface_group.spectral_range,
        num_surfaces=surface_group.num_surfaces,
        created_at=metadata.created_at,
        signature=metadata.signature,
        description=metadata.description,
        part_number=metadata.part_number,
    )
