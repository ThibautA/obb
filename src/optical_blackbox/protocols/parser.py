"""Protocol definitions for file parsers.

Defines the contract that all design file parsers must implement,
enabling extensibility for future formats (CODE V, Oslo, etc.).
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from optical_blackbox.models.surface_group import SurfaceGroup


@runtime_checkable
class DesignFileParser(Protocol):
    """Protocol for optical design file parsers.

    Implementers must provide methods to:
    - Declare supported file extensions
    - Check if a file can be parsed
    - Parse the file into a SurfaceGroup

    Example:
        >>> class MyParser:
        ...     @property
        ...     def supported_extensions(self) -> tuple[str, ...]:
        ...         return ('.myf',)
        ...
        ...     def can_parse(self, path: Path) -> bool:
        ...         return path.suffix.lower() in self.supported_extensions
        ...
        ...     def parse(self, path: Path) -> SurfaceGroup:
        ...         # Parse implementation
        ...         ...
    """

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions this parser handles.

        Returns:
            Tuple of lowercase extensions with dots (e.g., ('.zmx', '.zar'))
        """
        ...

    def can_parse(self, path: Path) -> bool:
        """Check if this parser can handle the given file.

        Args:
            path: Path to the file to check

        Returns:
            True if this parser can parse the file
        """
        ...

    def parse(self, path: Path) -> SurfaceGroup:
        """Parse the file and return a SurfaceGroup.

        Args:
            path: Path to the design file

        Returns:
            SurfaceGroup containing all parsed surfaces

        Raises:
            ParserError: If parsing fails
        """
        ...
