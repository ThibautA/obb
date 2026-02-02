"""Surface type implementations for Optical BlackBox.

This module re-exports the Surface model from the models package.
Surface types are defined in the SurfaceType enum within the Surface model.
"""

# The actual Surface model is in models.surface
# We only re-export it here for convenience
from optical_blackbox.models.surface import Surface, SurfaceType

__all__ = [
    "Surface",
    "SurfaceType",
]
