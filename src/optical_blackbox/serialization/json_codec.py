"""JSON codec with support for custom types.

Provides JSON encoding/decoding for types not natively supported:
- datetime objects
- bytes (base64 encoded)
- tuples (preserved, not converted to lists)
"""

import json
import base64
from datetime import datetime
from typing import Any


class OBBJSONEncoder(json.JSONEncoder):
    """JSON encoder with support for OBB-specific types.

    Handles:
    - datetime → ISO format string with marker
    - bytes → base64 string with marker
    - tuple → list with marker (to preserve type on decode)

    Example:
        >>> import json
        >>> data = {"time": datetime.now(), "data": b"hello"}
        >>> json.dumps(data, cls=OBBJSONEncoder)
    """

    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, datetime):
            return {"__datetime__": obj.isoformat()}

        if isinstance(obj, bytes):
            return {"__bytes__": base64.b64encode(obj).decode("ascii")}

        if isinstance(obj, tuple):
            return {"__tuple__": list(obj)}

        return super().default(obj)


def _obb_json_decoder_hook(dct: dict[str, Any]) -> Any:
    """JSON decoder hook for custom types.

    Args:
        dct: Dictionary to potentially decode

    Returns:
        Decoded object or original dict
    """
    if "__datetime__" in dct:
        return datetime.fromisoformat(dct["__datetime__"])

    if "__bytes__" in dct:
        return base64.b64decode(dct["__bytes__"])

    if "__tuple__" in dct:
        return tuple(dct["__tuple__"])

    return dct


def dumps(obj: Any, *, indent: int | None = None, **kwargs: Any) -> str:
    """Serialize object to JSON string with custom type support.

    Args:
        obj: Object to serialize
        indent: Indentation level for pretty printing
        **kwargs: Additional arguments passed to json.dumps

    Returns:
        JSON string
    """
    return json.dumps(obj, cls=OBBJSONEncoder, indent=indent, **kwargs)


def loads(s: str | bytes) -> Any:
    """Deserialize JSON string with custom type support.

    Args:
        s: JSON string or bytes to deserialize

    Returns:
        Deserialized object with custom types restored
    """
    return json.loads(s, object_hook=_obb_json_decoder_hook)


def dump(obj: Any, fp: Any, *, indent: int | None = 2, **kwargs: Any) -> None:
    """Serialize object to JSON file with custom type support.

    Args:
        obj: Object to serialize
        fp: File-like object to write to
        indent: Indentation level for pretty printing
        **kwargs: Additional arguments passed to json.dump
    """
    json.dump(obj, fp, cls=OBBJSONEncoder, indent=indent, **kwargs)


def load(fp: Any) -> Any:
    """Deserialize JSON from file with custom type support.

    Args:
        fp: File-like object to read from

    Returns:
        Deserialized object with custom types restored
    """
    return json.load(fp, object_hook=_obb_json_decoder_hook)
