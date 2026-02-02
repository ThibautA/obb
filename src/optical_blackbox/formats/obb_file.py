"""OBB file reader and writer.

Provides high-level interface for reading and writing .obb files.
"""

from pathlib import Path
from datetime import datetime
from typing import BinaryIO

from cryptography.hazmat.primitives.asymmetric import ec

from optical_blackbox.models.metadata import OBBMetadata
from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.serialization.binary import BinaryReader, BinaryWriter
from optical_blackbox.formats.obb_constants import OBB_MAGIC
from optical_blackbox.formats.obb_header import (
    build_header,
    serialize_header,
    deserialize_header,
    extract_metadata,
    extract_ephemeral_key,
)
from optical_blackbox.formats.obb_payload import (
    encrypt_payload,
    encrypt_payload_selective,
    decrypt_payload,
    decrypt_payload_selective,
    sign_payload,
    verify_payload_signature,
)
from optical_blackbox.exceptions import (
    InvalidMagicBytesError,
    InvalidOBBFileError,
    InvalidSignatureError,
)


class OBBWriter:
    """Writes .obb files.

    Example:
        >>> OBBWriter.write(
        ...     output_path=Path("component.obb"),
        ...     surface_group=surfaces,
        ...     metadata=metadata,
        ...     vendor_private_key=vendor_key,
        ...     platform_public_key=platform_key,
        ... )
    """

    @classmethod
    def write(
        cls,
        output_path: Path,
        surface_group: SurfaceGroup,
        metadata: OBBMetadata,
        vendor_private_key: ec.EllipticCurvePrivateKey,
        platform_public_key: ec.EllipticCurvePublicKey,
    ) -> None:
        """Write a .obb file.

        Args:
            output_path: Path for the output file
            surface_group: Optical surfaces to encrypt
            metadata: Public metadata
            vendor_private_key: Vendor's key for signing
            platform_public_key: Platform's key for encryption
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            cls._write_to_stream(
                f,
                surface_group,
                metadata,
                vendor_private_key,
                platform_public_key,
            )

    @classmethod
    def _write_to_stream(
        cls,
        stream: BinaryIO,
        surface_group: SurfaceGroup,
        metadata: OBBMetadata,
        vendor_private_key: ec.EllipticCurvePrivateKey,
        platform_public_key: ec.EllipticCurvePublicKey,
    ) -> None:
        """Write .obb data to a stream.

        Args:
            stream: Binary stream to write to
            surface_group: Optical surfaces to encrypt
            metadata: Public metadata
            vendor_private_key: Vendor's key for signing
            platform_public_key: Platform's key for encryption
        """
        writer = BinaryWriter(stream)

        # Encrypt payload
        encrypted_payload, ephemeral_public = encrypt_payload(
            surface_group,
            platform_public_key,
        )

        # Sign payload
        signature = sign_payload(encrypted_payload, vendor_private_key)

        # Update metadata with signature and timestamp
        metadata.signature = signature
        metadata.created_at = datetime.utcnow()

        # Build and serialize header
        header = build_header(metadata, ephemeral_public)
        header_bytes = serialize_header(header)

        # Write file structure
        writer.write_magic(OBB_MAGIC)
        writer.write_length_prefixed(header_bytes)
        writer.write_bytes(encrypted_payload)

    @classmethod
    def write_selective(
        cls,
        output_path: Path,
        surface_group: SurfaceGroup,
        metadata: OBBMetadata,
        vendor_private_key: ec.EllipticCurvePrivateKey,
        platform_public_key: ec.EllipticCurvePublicKey,
    ) -> None:
        """Write a .obb file with selective surface encryption.

        Only surfaces marked with visibility=ENCRYPTED are encrypted.
        Surfaces with visibility=PUBLIC remain in clear text.
        Surfaces with visibility=REDACTED are completely hidden (only index stored).

        Args:
            output_path: Path for the output file
            surface_group: Optical surfaces (visibility field controls encryption)
            metadata: Public metadata
            vendor_private_key: Vendor's key for signing
            platform_public_key: Platform's key for encryption
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            cls._write_selective_to_stream(
                f,
                surface_group,
                metadata,
                vendor_private_key,
                platform_public_key,
            )

    @classmethod
    def _write_selective_to_stream(
        cls,
        stream: BinaryIO,
        surface_group: SurfaceGroup,
        metadata: OBBMetadata,
        vendor_private_key: ec.EllipticCurvePrivateKey,
        platform_public_key: ec.EllipticCurvePublicKey,
    ) -> None:
        """Write selectively encrypted .obb data to a stream.

        Args:
            stream: Binary stream to write to
            surface_group: Optical surfaces with visibility flags
            metadata: Public metadata
            vendor_private_key: Vendor's key for signing
            platform_public_key: Platform's key for encryption
        """
        import json
        writer = BinaryWriter(stream)

        # Encrypt payload selectively
        payload_dict, ephemeral_public = encrypt_payload_selective(
            surface_group,
            platform_public_key,
        )

        # Serialize payload dict to bytes for signing
        payload_bytes = json.dumps(payload_dict).encode("utf-8")

        # Sign payload
        signature = sign_payload(payload_bytes, vendor_private_key)

        # Update metadata with signature and timestamp
        metadata.signature = signature
        metadata.created_at = datetime.utcnow()

        # Build and serialize header
        header = build_header(metadata, ephemeral_public)
        header_bytes = serialize_header(header)

        # Write file structure
        writer.write_magic(OBB_MAGIC)
        writer.write_length_prefixed(header_bytes)
        writer.write_bytes(payload_bytes)


class OBBReader:
    """Reads .obb files.

    Example:
        >>> # Read metadata only (no decryption)
        >>> metadata = OBBReader.read_metadata(Path("component.obb"))
        >>>
        >>> # Full read with decryption
        >>> metadata, surfaces = OBBReader.read_and_decrypt(
        ...     path=Path("component.obb"),
        ...     platform_private_key=platform_key,
        ...     vendor_public_key=vendor_key,
        ... )
    """

    @classmethod
    def read_metadata(cls, path: Path) -> OBBMetadata:
        """Read only the public metadata (no decryption).

        Args:
            path: Path to the .obb file

        Returns:
            OBBMetadata object

        Raises:
            InvalidMagicBytesError: If file is not a valid .obb
            InvalidOBBFileError: If file is malformed
        """
        with open(path, "rb") as f:
            reader = BinaryReader(f)

            # Verify magic bytes
            if not reader.read_and_verify_magic(OBB_MAGIC):
                raise InvalidMagicBytesError()

            # Read header
            header_bytes = reader.read_length_prefixed()
            header = deserialize_header(header_bytes)

            return extract_metadata(header)

    @classmethod
    def read_and_decrypt(
        cls,
        path: Path,
        platform_private_key: ec.EllipticCurvePrivateKey,
        vendor_public_key: ec.EllipticCurvePublicKey,
        verify_signature: bool = True,
    ) -> tuple[OBBMetadata, SurfaceGroup]:
        """Read and decrypt a .obb file.

        Args:
            path: Path to the .obb file
            platform_private_key: Platform's private key for decryption
            vendor_public_key: Vendor's public key for signature verification
            verify_signature: Whether to verify the signature (default: True)

        Returns:
            Tuple of (metadata, surface_group)

        Raises:
            InvalidMagicBytesError: If file is not a valid .obb
            InvalidSignatureError: If signature verification fails
            DecryptionError: If decryption fails
        """
        with open(path, "rb") as f:
            reader = BinaryReader(f)

            # Verify magic bytes
            if not reader.read_and_verify_magic(OBB_MAGIC):
                raise InvalidMagicBytesError()

            # Read header
            header_bytes = reader.read_length_prefixed()
            header = deserialize_header(header_bytes)

            # Read encrypted payload
            encrypted_payload = reader.read_rest()

        # Extract metadata and ephemeral key
        metadata = extract_metadata(header)
        ephemeral_public = extract_ephemeral_key(header)

        # Verify signature
        if verify_signature:
            if not verify_payload_signature(
                encrypted_payload,
                metadata.signature,
                vendor_public_key,
            ):
                raise InvalidSignatureError()

        # Decrypt payload
        surface_group = decrypt_payload(
            encrypted_payload,
            ephemeral_public,
            platform_private_key,
        )

        return metadata, surface_group

    @classmethod
    def read_and_decrypt_selective(
        cls,
        path: Path,
        platform_private_key: ec.EllipticCurvePrivateKey,
        vendor_public_key: ec.EllipticCurvePublicKey,
        verify_signature: bool = True,
    ) -> tuple[OBBMetadata, SurfaceGroup]:
        """Read and decrypt a selectively encrypted .obb file.

        Handles files created with write_selective() where only some surfaces
        are encrypted. Public surfaces remain accessible without decryption keys.

        Args:
            path: Path to the .obb file
            platform_private_key: Platform's private key for decryption
            vendor_public_key: Vendor's public key for signature verification
            verify_signature: Whether to verify the signature (default: True)

        Returns:
            Tuple of (metadata, surface_group)

        Raises:
            InvalidMagicBytesError: If file is not a valid .obb
            InvalidSignatureError: If signature verification fails
            DecryptionError: If decryption fails
        """
        import json

        with open(path, "rb") as f:
            reader = BinaryReader(f)

            # Verify magic bytes
            if not reader.read_and_verify_magic(OBB_MAGIC):
                raise InvalidMagicBytesError()

            # Read header
            header_bytes = reader.read_length_prefixed()
            header = deserialize_header(header_bytes)

            # Read payload (JSON dict, not fully encrypted)
            payload_bytes = reader.read_rest()

        # Extract metadata and ephemeral key
        metadata = extract_metadata(header)
        ephemeral_public = extract_ephemeral_key(header)

        # Verify signature
        if verify_signature:
            if not verify_payload_signature(
                payload_bytes,
                metadata.signature,
                vendor_public_key,
            ):
                raise InvalidSignatureError()

        # Parse payload dict
        payload_dict = json.loads(payload_bytes.decode("utf-8"))

        # Decrypt payload selectively
        surface_group = decrypt_payload_selective(
            payload_dict,
            ephemeral_public,
            platform_private_key,
        )

        return metadata, surface_group

    @classmethod
    def read(
        cls,
        path: Path,
        platform_private_key: ec.EllipticCurvePrivateKey,
        vendor_public_key: ec.EllipticCurvePublicKey,
        verify_signature: bool = True,
    ) -> tuple[OBBMetadata, SurfaceGroup]:
        """Smart read that auto-detects encryption mode.

        Automatically detects whether the file uses full or selective encryption
        and calls the appropriate decryption method.

        Args:
            path: Path to the .obb file
            platform_private_key: Platform's private key for decryption
            vendor_public_key: Vendor's public key for signature verification
            verify_signature: Whether to verify the signature (default: True)

        Returns:
            Tuple of (metadata, surface_group)

        Raises:
            InvalidMagicBytesError: If file is not a valid .obb
            InvalidSignatureError: If signature verification fails
            DecryptionError: If decryption fails
        """
        import json

        with open(path, "rb") as f:
            reader = BinaryReader(f)

            # Verify magic bytes
            if not reader.read_and_verify_magic(OBB_MAGIC):
                raise InvalidMagicBytesError()

            # Read header
            header_bytes = reader.read_length_prefixed()
            header = deserialize_header(header_bytes)

            # Read payload
            payload_bytes = reader.read_rest()

        # Extract metadata and ephemeral key
        metadata = extract_metadata(header)
        ephemeral_public = extract_ephemeral_key(header)

        # Verify signature
        if verify_signature:
            if not verify_payload_signature(
                payload_bytes,
                metadata.signature,
                vendor_public_key,
            ):
                raise InvalidSignatureError()

        # Try to detect selective encryption by checking if payload is valid JSON
        try:
            payload_dict = json.loads(payload_bytes.decode("utf-8"))
            if isinstance(payload_dict, dict) and payload_dict.get("encryption_mode") == "selective":
                # Selective encryption mode
                surface_group = decrypt_payload_selective(
                    payload_dict,
                    ephemeral_public,
                    platform_private_key,
                )
            else:
                # Fall back to full encryption
                surface_group = decrypt_payload(
                    payload_bytes,
                    ephemeral_public,
                    platform_private_key,
                )
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not JSON, must be fully encrypted
            surface_group = decrypt_payload(
                payload_bytes,
                ephemeral_public,
                platform_private_key,
            )

        return metadata, surface_group

    @classmethod
    def is_valid_obb_file(cls, path: Path) -> bool:
        """Check if a file is a valid .obb file.

        Args:
            path: Path to check

        Returns:
            True if file has valid magic bytes
        """
        try:
            with open(path, "rb") as f:
                magic = f.read(len(OBB_MAGIC))
                return magic == OBB_MAGIC
        except Exception:
            return False
