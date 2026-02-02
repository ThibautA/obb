"""Unit tests for parsers/zemax/zmx_parser.py - Zemax parser."""

import pytest
from pathlib import Path
import zipfile

from optical_blackbox.parsers.zemax.zmx_parser import ZemaxParser
from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.models.surface import SurfaceType
from optical_blackbox.exceptions import ZemaxParseError, NoSurfacesFoundError


class TestZemaxParserBasic:
    """Basic tests for ZemaxParser."""

    def test_supported_extensions(self):
        """Should support .zmx and .zar extensions."""
        parser = ZemaxParser()
        assert parser.supported_extensions == (".zmx", ".zar")

    def test_can_parse_zmx(self, tmp_path):
        """Should return True for .zmx files."""
        parser = ZemaxParser()
        zmx_file = tmp_path / "test.zmx"
        zmx_file.write_text("dummy")
        assert parser.can_parse(zmx_file) is True

    def test_can_parse_zar(self, tmp_path):
        """Should return True for .zar files."""
        parser = ZemaxParser()
        zar_file = tmp_path / "test.zar"
        zar_file.write_bytes(b"dummy")
        assert parser.can_parse(zar_file) is True

    def test_cannot_parse_other(self, tmp_path):
        """Should return False for other extensions."""
        parser = ZemaxParser()
        other_file = tmp_path / "test.txt"
        other_file.write_text("dummy")
        assert parser.can_parse(other_file) is False


class TestZemaxParserParsing:
    """Tests for parsing .zmx files."""

    def test_parse_minimal_zmx(self, tmp_zmx_file):
        """Should parse minimal .zmx file."""
        parser = ZemaxParser()
        result = parser.parse(tmp_zmx_file)
        
        assert isinstance(result, SurfaceGroup)
        assert result.num_surfaces >= 1

    def test_parse_returns_surface_group(self, tmp_zmx_file):
        """Should return SurfaceGroup."""
        parser = ZemaxParser()
        result = parser.parse(tmp_zmx_file)
        assert isinstance(result, SurfaceGroup)

    def test_parse_extracts_surfaces(self, tmp_zmx_file):
        """Should extract surfaces from .zmx."""
        parser = ZemaxParser()
        result = parser.parse(tmp_zmx_file)
        
        # Should have multiple surfaces
        assert len(result.surfaces) >= 2

    def test_parse_extracts_wavelengths(self, tmp_path):
        """Should extract wavelengths from WAVM lines."""
        content = """\
VERS 140710
MODE SEQ
WAVM 1 0.486130 1
WAVM 2 0.587560 1
WAVM 3 0.656270 1
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1E10
SURF 1
  TYPE STANDARD
  CURV 0.02
  THIC 5.0
  GLAS N-BK7
"""
        zmx_file = tmp_path / "test.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        # Check wavelengths (converted from µm to nm)
        assert len(result.wavelengths_nm) >= 1

    def test_parse_empty_file_raises_error(self, tmp_path):
        """Empty file should raise NoSurfacesFoundError."""
        zmx_file = tmp_path / "empty.zmx"
        zmx_file.write_text("", encoding="utf-16-le")
        
        parser = ZemaxParser()
        with pytest.raises(NoSurfacesFoundError):
            parser.parse(zmx_file)

    def test_parse_no_surfaces_raises_error(self, tmp_path):
        """File without SURF keywords should raise error."""
        content = """VERS 140710
MODE SEQ
WAVM 1 0.587560 1
"""
        zmx_file = tmp_path / "no_surf.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        with pytest.raises(NoSurfacesFoundError):
            parser.parse(zmx_file)


class TestZemaxParserEncoding:
    """Tests for file encoding handling."""

    def test_parse_utf16le_encoding(self, tmp_path, minimal_zmx_content):
        """Should parse UTF-16-LE encoded files."""
        zmx_file = tmp_path / "utf16le.zmx"
        zmx_file.write_text(minimal_zmx_content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        assert result.num_surfaces >= 1

    def test_parse_utf8_encoding(self, tmp_path, minimal_zmx_content):
        """Should parse UTF-8 encoded files."""
        zmx_file = tmp_path / "utf8.zmx"
        zmx_file.write_text(minimal_zmx_content, encoding="utf-8")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        assert result.num_surfaces >= 1

    def test_parse_latin1_encoding(self, tmp_path, minimal_zmx_content):
        """Should parse Latin-1 encoded files."""
        zmx_file = tmp_path / "latin1.zmx"
        zmx_file.write_text(minimal_zmx_content, encoding="latin-1")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        assert result.num_surfaces >= 1


class TestZemaxParserSurfaceTypes:
    """Tests for surface type parsing."""

    def test_parse_standard_surface(self, tmp_path):
        """Should parse STANDARD surface type."""
        content = """\
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1E10
SURF 1
  TYPE STANDARD
  CURV 0.05
  THIC 5.0
  GLAS N-BK7
"""
        zmx_file = tmp_path / "standard.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        assert result.surfaces[1].surface_type == SurfaceType.STANDARD

    def test_parse_evenasph_surface(self, tmp_path):
        """Should parse EVENASPH surface type."""
        content = """\
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1E10
SURF 1
  TYPE EVENASPH
  CURV 0.04
  THIC 5.0
  GLAS N-BK7
  CONI -1.0
  PARM 1 0
  PARM 2 1.2e-5
  PARM 3 -3.4e-8
"""
        zmx_file = tmp_path / "asphere.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        assert result.surfaces[1].surface_type == SurfaceType.EVENASPH


class TestZemaxParserProperties:
    """Tests for surface property parsing."""

    def test_parse_curvature_to_radius(self, tmp_path):
        """Should convert curvature to radius."""
        content = """\
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1E10
SURF 1
  TYPE STANDARD
  CURV 0.02
  THIC 5.0
"""
        zmx_file = tmp_path / "curv.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        # Curvature 0.02 → Radius 50.0
        assert abs(result.surfaces[1].radius - 50.0) < 0.01

    def test_parse_flat_surface(self, tmp_path):
        """Zero curvature should give infinite radius."""
        content = """\
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1E10
SURF 1
  TYPE STANDARD
  CURV 0.0
  THIC 5.0
"""
        zmx_file = tmp_path / "flat.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        assert result.surfaces[1].is_flat

    def test_parse_thickness_infinity(self, tmp_path):
        """Should parse INFINITY thickness."""
        content = """\
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC INFINITY
SURF 1
  TYPE STANDARD
  CURV 0.02
  THIC 5.0
"""
        zmx_file = tmp_path / "inf_thic.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        assert result.surfaces[0].thickness == float("inf")

    def test_parse_glass_material(self, tmp_path):
        """Should parse GLAS keyword."""
        content = """\
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1E10
SURF 1
  TYPE STANDARD
  CURV 0.02
  THIC 5.0
  GLAS N-BK7
"""
        zmx_file = tmp_path / "glass.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        assert result.surfaces[1].material == "N-BK7"

    def test_parse_semi_diameter(self, tmp_path):
        """Should parse DIAM keyword."""
        content = """\
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1E10
SURF 1
  TYPE STANDARD
  CURV 0.02
  THIC 5.0
  DIAM 12.7
"""
        zmx_file = tmp_path / "diam.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        assert abs(result.surfaces[1].semi_diameter - 12.7) < 0.01

    def test_parse_conic_constant(self, tmp_path):
        """Should parse CONI keyword."""
        content = """\
SURF 0
  TYPE STANDARD
  CURV 0.0
  THIC 1E10
SURF 1
  TYPE STANDARD
  CURV 0.02
  THIC 5.0
  CONI -1.0
"""
        zmx_file = tmp_path / "conic.zmx"
        zmx_file.write_text(content, encoding="utf-16-le")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_file)
        
        assert result.surfaces[1].conic == -1.0


class TestZemaxParserZar:
    """Tests for .zar archive parsing."""

    def test_parse_zar_file(self, tmp_path, minimal_zmx_content):
        """Should parse .zar archive containing .zmx."""
        # Create a .zar (ZIP) file with a .zmx inside
        zmx_name = "design.zmx"
        zar_path = tmp_path / "test.zar"
        
        with zipfile.ZipFile(zar_path, "w") as zf:
            # Write ZMX content encoded as UTF-16-LE
            zmx_bytes = minimal_zmx_content.encode("utf-16-le")
            zf.writestr(zmx_name, zmx_bytes)
        
        parser = ZemaxParser()
        result = parser.parse(zar_path)
        
        assert isinstance(result, SurfaceGroup)
        assert result.num_surfaces >= 1


class TestRealZemaxFiles:
    """Tests using real Zemax test files from testdata/."""

    @pytest.fixture
    def testdata_path(self):
        """Get path to testdata directory."""
        return Path(__file__).parent.parent.parent.parent / "testdata" / "Eyepieces"

    def test_parse_real_zmx_file(self, testdata_path):
        """Should parse a real .zmx file from testdata."""
        # Skip if testdata not available
        if not testdata_path.exists():
            pytest.skip("testdata directory not found")
        
        # Find first .zmx file
        zmx_files = list(testdata_path.glob("*.zmx"))
        if not zmx_files:
            pytest.skip("No .zmx files in testdata")
        
        parser = ZemaxParser()
        result = parser.parse(zmx_files[0])
        
        assert isinstance(result, SurfaceGroup)
        assert result.num_surfaces >= 1
        assert len(result.surfaces) >= 1
