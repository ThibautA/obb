"""Unit tests for serialization/json_codec.py - OBBJSONEncoder and helpers."""

import pytest
from datetime import datetime

from optical_blackbox.serialization import json_codec


class TestOBBJSONEncoderDatetime:
    """Tests for datetime serialization."""

    def test_encode_datetime(self):
        """Should encode datetime with marker."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        
        result = json_codec.dumps({"time": dt})
        
        assert '"__datetime__"' in result
        assert "2024-01-15T10:30:00" in result

    def test_decode_datetime(self):
        """Should decode datetime from marker."""
        json_str = '{"time": {"__datetime__": "2024-01-15T10:30:00"}}'
        
        result = json_codec.loads(json_str)
        
        assert result["time"] == datetime(2024, 1, 15, 10, 30, 0)

    def test_datetime_roundtrip(self):
        """Should roundtrip datetime."""
        dt = datetime(2024, 6, 15, 14, 45, 30)
        original = {"created": dt}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded["created"] == dt

    def test_datetime_with_microseconds(self):
        """Should preserve microseconds."""
        dt = datetime(2024, 1, 1, 0, 0, 0, 123456)
        
        encoded = json_codec.dumps({"dt": dt})
        decoded = json_codec.loads(encoded)
        
        assert decoded["dt"].microsecond == 123456


class TestOBBJSONEncoderBytes:
    """Tests for bytes serialization."""

    def test_encode_bytes(self):
        """Should encode bytes as base64 with marker."""
        data = b"hello world"
        
        result = json_codec.dumps({"data": data})
        
        assert '"__bytes__"' in result
        # base64 of "hello world"
        assert "aGVsbG8gd29ybGQ=" in result

    def test_decode_bytes(self):
        """Should decode bytes from marker."""
        json_str = '{"data": {"__bytes__": "aGVsbG8gd29ybGQ="}}'
        
        result = json_codec.loads(json_str)
        
        assert result["data"] == b"hello world"

    def test_bytes_roundtrip(self):
        """Should roundtrip bytes."""
        data = b"\x00\x01\x02\xff\xfe"
        original = {"binary": data}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded["binary"] == data

    def test_empty_bytes(self):
        """Should handle empty bytes."""
        original = {"empty": b""}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded["empty"] == b""


class TestOBBJSONEncoderTuple:
    """Tests for tuple serialization.
    
    Note: In standard JSON, tuples are converted to lists before custom
    encoding is applied. The __tuple__ marker in OBBJSONEncoder.default()
    is never reached. These tests verify actual behavior.
    """

    def test_tuple_converted_to_list(self):
        """Tuples are converted to lists in JSON."""
        data = (1, 2, 3)
        
        result = json_codec.dumps({"point": data})
        decoded = json_codec.loads(result)
        
        # JSON converts tuples to lists
        assert decoded["point"] == [1, 2, 3]

    def test_decode_tuple_marker(self):
        """Should decode tuple from explicit marker if present."""
        json_str = '{"point": {"__tuple__": [1, 2, 3]}}'
        
        result = json_codec.loads(json_str)
        
        assert result["point"] == (1, 2, 3)
        assert isinstance(result["point"], tuple)

    def test_tuple_in_json_becomes_list(self):
        """Tuples become lists in roundtrip."""
        original = {"coords": (10, 20, 30)}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        # Tuples become lists in standard JSON
        assert decoded["coords"] == [10, 20, 30]
        assert isinstance(decoded["coords"], list)

    def test_nested_tuple_becomes_list(self):
        """Nested tuples become nested lists."""
        original = {"nested": ((1, 2), (3, 4))}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded["nested"] == [[1, 2], [3, 4]]


class TestOBBJSONEncoderMixed:
    """Tests for mixed type serialization."""

    def test_mixed_types(self):
        """Should handle mixed custom types."""
        original = {
            "time": datetime(2024, 1, 1),
            "data": b"binary",
            "point": (1, 2),
        }
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded["time"] == original["time"]
        assert decoded["data"] == original["data"]
        # Tuples become lists in JSON
        assert decoded["point"] == [1, 2]

    def test_nested_structure(self):
        """Should handle nested structures with custom types."""
        original = {
            "metadata": {
                "created": datetime(2024, 1, 1),
                "hash": b"\x00\x01\x02",
            },
            "points": [(1, 2), (3, 4)],  # list of tuples
        }
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded["metadata"]["created"] == original["metadata"]["created"]
        assert decoded["metadata"]["hash"] == original["metadata"]["hash"]


class TestOBBJSONStandardTypes:
    """Tests for standard JSON types (should work normally)."""

    def test_strings(self):
        """Should handle strings normally."""
        original = {"name": "test", "value": "hello"}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded == original

    def test_numbers(self):
        """Should handle numbers normally."""
        original = {"int": 42, "float": 3.14, "neg": -100}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded["int"] == 42
        assert abs(decoded["float"] - 3.14) < 1e-10
        assert decoded["neg"] == -100

    def test_lists(self):
        """Should handle lists normally."""
        original = {"items": [1, 2, 3, "four"]}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded == original

    def test_none(self):
        """Should handle None."""
        original = {"value": None}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded["value"] is None

    def test_booleans(self):
        """Should handle booleans."""
        original = {"flag": True, "other": False}
        
        encoded = json_codec.dumps(original)
        decoded = json_codec.loads(encoded)
        
        assert decoded == original


class TestDumpsLoads:
    """Tests for dumps/loads helper functions."""

    def test_dumps_indent(self):
        """Should support indent parameter."""
        data = {"a": 1, "b": 2}
        
        result = json_codec.dumps(data, indent=2)
        
        assert "\n" in result  # Pretty printed
        assert "  " in result

    def test_loads_bytes(self):
        """Should accept bytes input."""
        json_bytes = b'{"key": "value"}'
        
        result = json_codec.loads(json_bytes)
        
        assert result == {"key": "value"}

    def test_loads_string(self):
        """Should accept string input."""
        json_str = '{"key": "value"}'
        
        result = json_codec.loads(json_str)
        
        assert result == {"key": "value"}


class TestDumpLoad:
    """Tests for dump/load file operations."""

    def test_dump_load_file(self, tmp_path):
        """Should dump and load from file."""
        filepath = tmp_path / "test.json"
        original = {
            "time": datetime(2024, 1, 1),
            "data": b"test",
        }
        
        with open(filepath, "w") as f:
            json_codec.dump(original, f)
        
        with open(filepath, "r") as f:
            decoded = json_codec.load(f)
        
        assert decoded["time"] == original["time"]
        assert decoded["data"] == original["data"]
