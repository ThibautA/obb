"""File parsers for Optical BlackBox."""

from optical_blackbox.parsers.registry import (
    register_parser,
    get_parser_for_file,
    get_parser_for_extension,
    parse_file,
    list_supported_extensions,
    is_extension_supported,
)

# Import Zemax parser to trigger registration
from optical_blackbox.parsers.zemax import ZemaxParser

__all__ = [
    # Registry functions
    "register_parser",
    "get_parser_for_file",
    "get_parser_for_extension",
    "parse_file",
    "list_supported_extensions",
    "is_extension_supported",
    # Parsers
    "ZemaxParser",
]
