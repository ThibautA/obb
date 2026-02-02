"""OBB payload encryption and decryption.

Handles the encrypted payload portion of .obb files.
"""

from cryptography.hazmat.primitives.asymmetric import ec

from optical_blackbox.models.surface_group import SurfaceGroup
from optical_blackbox.models.surface import Surface, SurfaceVisibility
from optical_blackbox.crypto.hybrid import OBBEncryptor, OBBSigner


def encrypt_payload(
    surface_group: SurfaceGroup,
    platform_public_key: ec.EllipticCurvePublicKey,
) -> tuple[bytes, ec.EllipticCurvePublicKey]:
    """Encrypt SurfaceGroup for storage in .obb file.

    Args:
        surface_group: Surface group to encrypt
        platform_public_key: Platform's public key for encryption

    Returns:
        Tuple of (encrypted_payload, ephemeral_public_key)
    """
    # Serialize surface group to JSON
    payload_json = surface_group.model_dump_json().encode("utf-8")

    # Encrypt with hybrid encryption
    encrypted_payload, ephemeral_public = OBBEncryptor.encrypt(
        payload_json,
        platform_public_key,
    )

    return encrypted_payload, ephemeral_public


def encrypt_payload_selective(
    surface_group: SurfaceGroup,
    platform_public_key: ec.EllipticCurvePublicKey,
) -> tuple[dict, ec.EllipticCurvePublicKey]:
    """Encrypt only selected surfaces based on visibility flags.

    Args:
        surface_group: Surface group with visibility flags
        platform_public_key: Platform's public key for encryption

    Returns:
        Tuple of (payload_dict, ephemeral_public_key)
        payload_dict contains:
            - encryption_mode: "selective"
            - public_surfaces: List of public surface dicts
            - encrypted_surfaces_data: Encrypted bytes of encrypted surfaces
            - redacted_surface_indices: List of redacted surface numbers
    """
    public_surfaces = surface_group.get_public_surfaces()
    encrypted_surfaces = surface_group.get_encrypted_surfaces()
    redacted_surfaces = surface_group.get_redacted_surfaces()

    # Build payload structure
    payload = {
        "encryption_mode": "selective",
        "public_surfaces": [s.model_dump(mode="json") for s in public_surfaces],
        "redacted_surface_indices": [s.surface_number for s in redacted_surfaces],
        "wavelengths_nm": surface_group.wavelengths_nm,
        "primary_wavelength_index": surface_group.primary_wavelength_index,
        "stop_surface": surface_group.stop_surface,
        "field_type": surface_group.field_type,
        "max_field": surface_group.max_field,
    }

    # Encrypt only the encrypted surfaces
    if encrypted_surfaces:
        encrypted_data = {
            "surfaces": [s.model_dump(mode="json") for s in encrypted_surfaces]
        }
        import json
        import base64
        encrypted_json = json.dumps(encrypted_data).encode("utf-8")
        
        encrypted_bytes, ephemeral_public = OBBEncryptor.encrypt(
            encrypted_json,
            platform_public_key,
        )
        
        # Base64-encode the encrypted bytes for JSON serialization
        payload["encrypted_surfaces_data"] = base64.b64encode(encrypted_bytes).decode("ascii")
    else:
        # No surfaces to encrypt - generate ephemeral key anyway for consistency
        from optical_blackbox.crypto.ecdh import generate_ephemeral_keypair
        _, ephemeral_public = generate_ephemeral_keypair()
        payload["encrypted_surfaces_data"] = ""

    return payload, ephemeral_public


def decrypt_payload(
    encrypted_payload: bytes,
    ephemeral_public_key: ec.EllipticCurvePublicKey,
    platform_private_key: ec.EllipticCurvePrivateKey,
) -> SurfaceGroup:
    """Decrypt payload and parse SurfaceGroup.

    Args:
        encrypted_payload: Encrypted payload bytes
        ephemeral_public_key: Ephemeral public key from header
        platform_private_key: Platform's private key for decryption

    Returns:
        Decrypted SurfaceGroup

    Raises:
        DecryptionError: If decryption fails
    """
    # Decrypt payload
    payload_json = OBBEncryptor.decrypt(
        encrypted_payload,
        ephemeral_public_key,
        platform_private_key,
    )

    # Parse SurfaceGroup from JSON
    return SurfaceGroup.model_validate_json(payload_json)


def decrypt_payload_selective(
    payload_dict: dict,
    ephemeral_public_key: ec.EllipticCurvePublicKey,
    platform_private_key: ec.EllipticCurvePrivateKey,
) -> SurfaceGroup:
    """Decrypt selectively encrypted payload and reconstruct SurfaceGroup.

    Args:
        payload_dict: Payload dictionary with public/encrypted/redacted surfaces
        ephemeral_public_key: Ephemeral public key from header
        platform_private_key: Platform's private key for decryption

    Returns:
        Reconstructed SurfaceGroup with all surfaces (encrypted ones decrypted)

    Raises:
        DecryptionError: If decryption fails
    """
    import json
    import base64
    from optical_blackbox.models.surface import Surface, SurfaceVisibility

    # Reconstruct public surfaces
    public_surfaces = [Surface.model_validate(s) for s in payload_dict.get("public_surfaces", [])]
    
    # Get redacted surface indices
    redacted_indices = payload_dict.get("redacted_surface_indices", [])
    
    # Decrypt encrypted surfaces
    encrypted_surfaces = []
    encrypted_data_b64 = payload_dict.get("encrypted_surfaces_data", "")
    if encrypted_data_b64:
        # Decode base64 back to bytes
        encrypted_data_bytes = base64.b64decode(encrypted_data_b64)
        decrypted_json = OBBEncryptor.decrypt(
            encrypted_data_bytes,
            ephemeral_public_key,
            platform_private_key,
        )
        encrypted_data = json.loads(decrypted_json)
        encrypted_surfaces = [Surface.model_validate(s) for s in encrypted_data.get("surfaces", [])]
    
    # Create redacted placeholder surfaces
    redacted_surfaces = []
    for idx in redacted_indices:
        redacted_surfaces.append(
            Surface(
                surface_number=idx,
                surface_type="standard",
                visibility=SurfaceVisibility.REDACTED,
                comment=f"Surface {idx} (redacted)",
            )
        )
    
    # Combine all surfaces and sort by surface_number
    all_surfaces = public_surfaces + encrypted_surfaces + redacted_surfaces
    all_surfaces.sort(key=lambda s: s.surface_number)
    
    # Reconstruct SurfaceGroup
    return SurfaceGroup(
        surfaces=all_surfaces,
        wavelengths_nm=payload_dict.get("wavelengths_nm", [550.0]),
        primary_wavelength_index=payload_dict.get("primary_wavelength_index", 0),
        stop_surface=payload_dict.get("stop_surface"),
        field_type=payload_dict.get("field_type"),
        max_field=payload_dict.get("max_field"),
    )


def sign_payload(
    encrypted_payload: bytes,
    vendor_private_key: ec.EllipticCurvePrivateKey,
) -> str:
    """Sign encrypted payload.

    Args:
        encrypted_payload: Encrypted payload bytes
        vendor_private_key: Vendor's private key for signing

    Returns:
        Base64-encoded signature
    """
    return OBBSigner.sign(encrypted_payload, vendor_private_key)


def verify_payload_signature(
    encrypted_payload: bytes,
    signature_b64: str,
    vendor_public_key: ec.EllipticCurvePublicKey,
) -> bool:
    """Verify payload signature.

    Args:
        encrypted_payload: Encrypted payload bytes
        signature_b64: Base64-encoded signature
        vendor_public_key: Vendor's public key for verification

    Returns:
        True if signature is valid
    """
    return OBBSigner.verify(encrypted_payload, signature_b64, vendor_public_key)
