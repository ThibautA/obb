"""Zemax .zar archive extractor.

Handles extraction of .zmx files from Zemax archive files.
"""

import zipfile
from pathlib import Path

from optical_blackbox.exceptions import ZemaxParseError


def extract_zmx_content(zar_path: Path) -> str:
    """Extract .zmx content from a .zar archive.

    A .zar file is a ZIP archive containing the .zmx file and
    potentially other resources (glass catalogs, coatings, etc.).

    Args:
        zar_path: Path to the .zar file

    Returns:
        Content of the embedded .zmx file as a string

    Raises:
        ZemaxParseError: If no .zmx file is found or extraction fails
    """
    try:
        with zipfile.ZipFile(zar_path, "r") as zf:
            # Find the .zmx file in the archive
            zmx_files = [
                name for name in zf.namelist()
                if name.lower().endswith(".zmx")
            ]

            if not zmx_files:
                raise ZemaxParseError("No .zmx file found in .zar archive")

            # Use the first .zmx file found
            zmx_filename = zmx_files[0]

            # Read and decode the content
            zmx_bytes = zf.read(zmx_filename)

            # Try UTF-16-LE first (common for Zemax), then UTF-8
            try:
                content = zmx_bytes.decode("utf-16-le")
            except UnicodeDecodeError:
                try:
                    content = zmx_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    content = zmx_bytes.decode("latin-1", errors="ignore")

            return content

    except zipfile.BadZipFile as e:
        raise ZemaxParseError(f"Invalid .zar file: {e}") from e
    except Exception as e:
        raise ZemaxParseError(f"Failed to extract .zar: {e}") from e


def list_zar_contents(zar_path: Path) -> list[str]:
    """List all files in a .zar archive.

    Args:
        zar_path: Path to the .zar file

    Returns:
        List of filenames in the archive
    """
    try:
        with zipfile.ZipFile(zar_path, "r") as zf:
            return zf.namelist()
    except Exception:
        return []
