"""Parser registry for extensible file format support.

Provides a decorator-based registration system for file parsers,
allowing new formats to be added without modifying core code.
"""

from pathlib import Path
from typing import Callable, Type

from optical_blackbox.protocols.parser import DesignFileParser
from optical_blackbox.models.surface_group import SurfaceGroup

# Global registry mapping extensions to parser classes
_PARSER_REGISTRY: dict[str, Type[DesignFileParser]] = {}


def register_parser(*extensions: str) -> Callable[[Type], Type]:
    """Decorator to register a parser for file extensions.

    Use this decorator to register a parser:

    Example:
        >>> @register_parser(".zmx", ".zar")
        ... class ZemaxParser:
        ...     @property
        ...     def supported_extensions(self) -> tuple[str, ...]:
        ...         return (".zmx", ".zar")
        ...     # ... other methods

    Args:
        *extensions: File extensions this parser handles (e.g., ".zmx", ".zar")

    Returns:
        Decorator function
    """

    def decorator(cls: Type) -> Type:
        for ext in extensions:
            ext_lower = ext.lower()
            if ext_lower in _PARSER_REGISTRY:
                raise ValueError(
                    f"Extension '{ext_lower}' is already registered to "
                    f"{_PARSER_REGISTRY[ext_lower].__name__}"
                )
            _PARSER_REGISTRY[ext_lower] = cls
        return cls

    return decorator


def get_parser_for_extension(extension: str) -> DesignFileParser:
    """Get a parser instance for a file extension.

    Args:
        extension: File extension (e.g., ".zmx")

    Returns:
        Parser instance

    Raises:
        ValueError: If no parser is registered for the extension
    """
    ext_lower = extension.lower()
    if ext_lower not in _PARSER_REGISTRY:
        available = list(_PARSER_REGISTRY.keys())
        raise ValueError(
            f"No parser registered for extension '{ext_lower}'. "
            f"Available: {available}"
        )
    return _PARSER_REGISTRY[ext_lower]()


def get_parser_for_file(path: Path) -> DesignFileParser:
    """Get a parser instance for a file based on its extension.

    Args:
        path: Path to the file

    Returns:
        Parser instance

    Raises:
        ValueError: If no parser is registered for the file's extension
    """
    return get_parser_for_extension(path.suffix)


def parse_file(path: Path) -> SurfaceGroup:
    """Parse a design file using the appropriate parser.

    Convenience function that gets the parser and parses in one call.

    Args:
        path: Path to the design file

    Returns:
        Parsed SurfaceGroup
    """
    parser = get_parser_for_file(path)
    return parser.parse(path)


def list_supported_extensions() -> list[str]:
    """List all registered file extensions.

    Returns:
        List of supported extensions
    """
    return list(_PARSER_REGISTRY.keys())


def is_extension_supported(extension: str) -> bool:
    """Check if a file extension is supported.

    Args:
        extension: File extension

    Returns:
        True if a parser is registered
    """
    return extension.lower() in _PARSER_REGISTRY


def clear_registry() -> None:
    """Clear all registered parsers.

    Primarily for testing purposes.
    """
    _PARSER_REGISTRY.clear()
