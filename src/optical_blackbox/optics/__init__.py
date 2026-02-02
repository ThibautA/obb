"""Optical calculations for Optical BlackBox."""

from optical_blackbox.optics.paraxial import (
    compute_paraxial_properties,
    compute_system_matrix,
    ParaxialCalculator,
)
from optical_blackbox.optics.glass_catalog import (
    get_refractive_index,
    is_material_known,
    list_materials,
    GLASS_CATALOG,
)
from optical_blackbox.optics.metadata_extractor import (
    extract_metadata,
    update_metadata_from_surfaces,
)

__all__ = [
    # Paraxial
    "compute_paraxial_properties",
    "compute_system_matrix",
    "ParaxialCalculator",
    # Glass catalog
    "get_refractive_index",
    "is_material_known",
    "list_materials",
    "GLASS_CATALOG",
    # Metadata
    "extract_metadata",
    "update_metadata_from_surfaces",
]
