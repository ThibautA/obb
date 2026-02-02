"""Zemax .zmx file parser.

Parses Zemax sequential lens files into OBB SurfaceGroup format.
"""

from pathlib import Path
from typing import Any

from optical_blackbox.models.surface import Surface
from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.parsers.registry import register_parser
from optical_blackbox.parsers.zemax.zmx_tokens import (
    SURF, TYPE, CURV, THIC, GLAS, DIAM, CONI, STOP, PARM,
    WAVM, DECX, DECY, TILTX, TILTY,
    IGNORED_KEYWORDS,
)
from optical_blackbox.parsers.zemax.zmx_surface_mapper import (
    build_surface,
    parse_thickness,
)
from optical_blackbox.parsers.zemax.zar_extractor import extract_zmx_content
from optical_blackbox.exceptions import ZemaxParseError, NoSurfacesFoundError


@register_parser(".zmx", ".zar")
class ZemaxParser:
    """Parser for Zemax .zmx and .zar files.

    Handles sequential mode optical systems from Zemax OpticStudio.
    Extracts surfaces, wavelengths, and basic system configuration.

    Example:
        >>> parser = ZemaxParser()
        >>> surface_group = parser.parse(Path("doublet.zmx"))
        >>> print(f"Found {surface_group.num_surfaces} surfaces")
    """

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Get supported file extensions."""
        return (".zmx", ".zar")

    def can_parse(self, path: Path) -> bool:
        """Check if this parser can handle the file."""
        return path.suffix.lower() in self.supported_extensions

    def parse(self, path: Path) -> SurfaceGroup:
        """Parse a Zemax file into a SurfaceGroup.

        Args:
            path: Path to the .zmx or .zar file

        Returns:
            SurfaceGroup containing parsed surfaces

        Raises:
            ZemaxParseError: If parsing fails
            NoSurfacesFoundError: If no surfaces are found
        """
        # Get content (extract from .zar if needed)
        if path.suffix.lower() == ".zar":
            content = extract_zmx_content(path)
        else:
            content = self._read_zmx_file(path)

        return self._parse_content(content)

    def _read_zmx_file(self, path: Path) -> str:
        """Read a .zmx file with appropriate encoding.

        Args:
            path: Path to the .zmx file

        Returns:
            File content as string
        """
        # Try encodings in order of likelihood
        encodings = ["utf-16-le", "utf-16", "utf-8", "latin-1"]

        for encoding in encodings:
            try:
                content = path.read_text(encoding=encoding)
                # Check for valid content
                if "SURF" in content or "surf" in content.lower():
                    return content
            except (UnicodeDecodeError, UnicodeError):
                continue

        # Last resort: read as bytes and decode with errors ignored
        try:
            return path.read_bytes().decode("utf-16-le", errors="ignore")
        except Exception as e:
            raise ZemaxParseError(f"Failed to read file: {e}") from e

    def _parse_content(self, content: str) -> SurfaceGroup:
        """Parse .zmx content into SurfaceGroup.

        Args:
            content: File content as string

        Returns:
            Parsed SurfaceGroup
        """
        lines = content.split("\n")

        surfaces_data: list[dict[str, Any]] = []
        wavelengths: list[float] = []
        current_surface: dict[str, Any] | None = None
        stop_surface: int | None = None

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                parts = line.split()
                if not parts:
                    continue

                keyword = parts[0].upper()

                # Skip ignored keywords
                if keyword in IGNORED_KEYWORDS:
                    continue

                # New surface
                if keyword == SURF:
                    # Save previous surface
                    if current_surface is not None:
                        surfaces_data.append(current_surface)

                    surf_num = int(parts[1]) if len(parts) > 1 else len(surfaces_data)
                    current_surface = self._new_surface_data(surf_num)

                # Surface properties
                elif current_surface is not None:
                    self._parse_surface_property(
                        keyword, parts, current_surface, line_num
                    )

                    # Check for stop surface
                    if keyword == STOP:
                        stop_surface = current_surface["number"]

                # Wavelengths (outside surface context)
                elif keyword == WAVM:
                    self._parse_wavelength(parts, wavelengths)

            except Exception as e:
                # Log but continue parsing
                pass

        # Add last surface
        if current_surface is not None:
            surfaces_data.append(current_surface)

        # Validate we have surfaces
        if not surfaces_data:
            raise NoSurfacesFoundError()

        # Build Surface objects
        surfaces = [build_surface(data) for data in surfaces_data]

        # Default wavelength if none found
        if not wavelengths:
            wavelengths = [587.56]

        return SurfaceGroup(
            surfaces=surfaces,
            stop_surface=stop_surface,
            wavelengths_nm=wavelengths,
            primary_wavelength_index=0,
        )

    def _new_surface_data(self, number: int) -> dict[str, Any]:
        """Create a new surface data dictionary.

        Args:
            number: Surface number

        Returns:
            Initialized surface data dict
        """
        return {
            "number": number,
            "type": "STANDARD",
            "curvature": 0.0,
            "thickness": 0.0,
            "material": None,
            "semi_diameter": 0.0,
            "conic": 0.0,
            "parm": {},
            "decenter_x": 0.0,
            "decenter_y": 0.0,
            "tilt_x": 0.0,
            "tilt_y": 0.0,
        }

    def _parse_surface_property(
        self,
        keyword: str,
        parts: list[str],
        surface: dict[str, Any],
        line_num: int,
    ) -> None:
        """Parse a surface property line.

        Args:
            keyword: Line keyword
            parts: Split line parts
            surface: Surface data dict to update
            line_num: Line number for error messages
        """
        try:
            if keyword == TYPE and len(parts) > 1:
                surface["type"] = parts[1].upper()

            elif keyword == CURV and len(parts) > 1:
                surface["curvature"] = float(parts[1])

            elif keyword == THIC and len(parts) > 1:
                surface["thickness"] = parse_thickness(parts[1])

            elif keyword == GLAS and len(parts) > 1:
                # Material name (ignore additional parameters)
                surface["material"] = parts[1]

            elif keyword == DIAM and len(parts) > 1:
                surface["semi_diameter"] = float(parts[1])

            elif keyword == CONI and len(parts) > 1:
                surface["conic"] = float(parts[1])

            elif keyword == PARM and len(parts) > 2:
                parm_index = int(parts[1])
                parm_value = float(parts[2])
                surface["parm"][parm_index] = parm_value

            elif keyword == DECX and len(parts) > 1:
                surface["decenter_x"] = float(parts[1])

            elif keyword == DECY and len(parts) > 1:
                surface["decenter_y"] = float(parts[1])

            elif keyword == TILTX and len(parts) > 1:
                surface["tilt_x"] = float(parts[1])

            elif keyword == TILTY and len(parts) > 1:
                surface["tilt_y"] = float(parts[1])

        except (ValueError, IndexError):
            # Skip malformed lines
            pass

    def _parse_wavelength(self, parts: list[str], wavelengths: list[float]) -> None:
        """Parse a wavelength definition line.

        Args:
            parts: Split line parts
            wavelengths: List to append wavelength to
        """
        # WAVM format: WAVM <index> <wavelength_um> <weight>
        if len(parts) >= 3:
            try:
                wavelength_um = float(parts[2])
                wavelength_nm = wavelength_um * 1000  # Convert µm to nm
                if wavelength_nm > 0:
                    wavelengths.append(wavelength_nm)
            except ValueError:
                pass
