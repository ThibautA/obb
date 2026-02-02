# API Documentation

Complete Python API reference for Optical BlackBox.

## Installation

```bash
pip install optical-blackbox
```

## Quick Start

```python
from pathlib import Path
from optical_blackbox.crypto.keys import KeyManager
from optical_blackbox.formats.obb_file import OBBWriter, OBBReader
from optical_blackbox.parsers.zemax.zmx_parser import parse_zmx_file
from optical_blackbox.models.metadata import OBBMetadata

# Generate keys
vendor_priv, vendor_pub = KeyManager.generate_keypair()
platform_priv, platform_pub = KeyManager.generate_keypair()

# Parse Zemax file
result = parse_zmx_file(Path("lens.zmx"))
surface_group = result.unwrap()

# Create metadata
metadata = OBBMetadata(
    vendor_id="thorlabs",
    name="AC254-050-A",
    efl_mm=50.0,
    na=0.25,
    diameter_mm=25.4,
)

# Encrypt and write
OBBWriter.write(
    output_path=Path("lens.obb"),
    surface_group=surface_group,
    metadata=metadata,
    vendor_private_key=vendor_priv,
    platform_public_key=platform_pub,
)

# Read and decrypt
metadata_only = OBBReader.read_metadata(Path("lens.obb"))
metadata, surfaces = OBBReader.read_and_decrypt(
    path=Path("lens.obb"),
    platform_private_key=platform_priv,
    vendor_public_key=vendor_pub,
)
```

---

## Core Modules

### crypto.keys - Key Management

Generate, save, and load ECDSA P-256 keys.

#### KeyManager

```python
class KeyManager:
    """Manages ECDSA P-256 key pairs for vendors and platform."""
    
    @classmethod
    def generate_keypair(cls) -> tuple[EllipticCurvePrivateKey, EllipticCurvePublicKey]:
        """Generate a new ECDSA P-256 key pair."""
    
    @classmethod
    def save_private_key(cls, key: EllipticCurvePrivateKey, path: Path, password: str | None = None) -> None:
        """Save a private key to PEM file with optional encryption."""
    
    @classmethod
    def save_public_key(cls, key: EllipticCurvePublicKey, path: Path) -> None:
        """Save a public key to PEM file."""
    
    @classmethod
    def load_private_key(cls, path: Path, password: str | None = None) -> EllipticCurvePrivateKey:
        """Load a private key from PEM file."""
    
    @classmethod
    def load_public_key(cls, path: Path) -> EllipticCurvePublicKey:
        """Load a public key from PEM file."""
```

**Example:**

```python
from optical_blackbox.crypto.keys import KeyManager

# Generate
priv, pub = KeyManager.generate_keypair()

# Save with password
KeyManager.save_private_key(priv, Path("vendor.key"), password="secret")
KeyManager.save_public_key(pub, Path("vendor.pub"))

# Load
priv = KeyManager.load_private_key(Path("vendor.key"), password="secret")
pub = KeyManager.load_public_key(Path("vendor.pub"))
```

---

### crypto.hybrid - High-Level Encryption

Hybrid encryption and signing (ECDH + AES-GCM + ECDSA).

#### OBBEncryptor

```python
class OBBEncryptor:
    """Hybrid encryption using ECDH + AES-256-GCM."""
    
    @staticmethod
    def encrypt(
        plaintext: bytes,
        recipient_public_key: EllipticCurvePublicKey,
    ) -> tuple[bytes, EllipticCurvePublicKey]:
        """Encrypt data for a specific recipient.
        
        Returns:
            (encrypted_payload, ephemeral_public_key)
        """
    
    @staticmethod
    def decrypt(
        encrypted_payload: bytes,
        ephemeral_public_key: EllipticCurvePublicKey,
        recipient_private_key: EllipticCurvePrivateKey,
    ) -> bytes:
        """Decrypt data using recipient's private key."""
```

#### OBBSigner

```python
class OBBSigner:
    """ECDSA digital signatures."""
    
    @staticmethod
    def sign(data: bytes, private_key: EllipticCurvePrivateKey) -> str:
        """Sign data and return base64-encoded signature."""
    
    @staticmethod
    def verify(data: bytes, signature: str, public_key: EllipticCurvePublicKey) -> bool:
        """Verify a base64-encoded signature."""
    
    @staticmethod
    def verify_or_raise(data: bytes, signature: str, public_key: EllipticCurvePublicKey) -> None:
        """Verify signature or raise InvalidSignatureError."""
```

**Example:**

```python
from optical_blackbox.crypto.hybrid import OBBEncryptor, OBBSigner

# Encrypt
plaintext = b"Lens design data"
encrypted, ephemeral_pub = OBBEncryptor.encrypt(plaintext, platform_public_key)

# Sign
signature = OBBSigner.sign(encrypted, vendor_private_key)

# Verify
if OBBSigner.verify(encrypted, signature, vendor_public_key):
    # Decrypt
    decrypted = OBBEncryptor.decrypt(encrypted, ephemeral_pub, platform_private_key)
```

---

### formats.obb_file - OBB File Format

Read and write .obb encrypted files.

#### OBBWriter

```python
class OBBWriter:
    """Write encrypted OBB files."""
    
    @staticmethod
    def write(
        output_path: Path,
        surface_group: SurfaceGroup,
        metadata: OBBMetadata,
        vendor_private_key: EllipticCurvePrivateKey,
        platform_public_key: EllipticCurvePublicKey,
    ) -> None:
        """Write an encrypted OBB file."""
```

#### OBBReader

```python
class OBBReader:
    """Read encrypted OBB files."""
    
    @staticmethod
    def read_metadata(path: Path) -> OBBMetadata:
        """Read metadata without decrypting payload."""
    
    @staticmethod
    def read_and_decrypt(
        path: Path,
        platform_private_key: EllipticCurvePrivateKey,
        vendor_public_key: EllipticCurvePublicKey,
    ) -> tuple[OBBMetadata, SurfaceGroup]:
        """Read and decrypt full OBB file."""
```

**Example:**

```python
from optical_blackbox.formats.obb_file import OBBWriter, OBBReader

# Write
OBBWriter.write(
    output_path=Path("output.obb"),
    surface_group=surfaces,
    metadata=metadata,
    vendor_private_key=vendor_priv,
    platform_public_key=platform_pub,
)

# Read metadata only (no decryption)
meta = OBBReader.read_metadata(Path("output.obb"))
print(f"{meta.vendor_id}: {meta.name}, EFL={meta.efl_mm}mm")

# Full decrypt
metadata, surfaces = OBBReader.read_and_decrypt(
    path=Path("output.obb"),
    platform_private_key=platform_priv,
    vendor_public_key=vendor_pub,
)
```

---

### parsers.zemax - Zemax File Parsing

Parse Zemax .zmx and .zar files.

#### parse_zmx_file

```python
def parse_zmx_file(path: Path) -> Result[SurfaceGroup, ParserError]:
    """Parse a Zemax .zmx file.
    
    Supports:
    - UTF-16LE encoding
    - Sequential ray tracing systems
    - Standard and even asphere surfaces
    
    Returns:
        Ok(SurfaceGroup) on success
        Err(ParserError) on failure
    """
```

**Example:**

```python
from optical_blackbox.parsers.zemax.zmx_parser import parse_zmx_file

result = parse_zmx_file(Path("lens.zmx"))

if result.is_ok():
    surface_group = result.unwrap()
    print(f"Parsed {surface_group.num_surfaces} surfaces")
else:
    error = result.unwrap_or(None)
    print(f"Parse failed: {error}")
```

---

### models - Data Models

Pydantic models with validation.

#### Surface

```python
class Surface(BaseModel):
    """Single optical surface."""
    
    surface_number: int
    surface_type: SurfaceType
    radius: float  # mm (inf for flat)
    thickness: float  # mm
    material: str | None  # None for air
    semi_diameter: float  # mm
    conic: float
    aspheric_coeffs: dict[str, float] | None
    
    # Properties
    @property
    def is_flat(self) -> bool: ...
    
    @property
    def is_air(self) -> bool: ...
    
    @property
    def curvature(self) -> float: ...
```

#### SurfaceGroup

```python
class SurfaceGroup(BaseModel):
    """Collection of surfaces forming an optical system."""
    
    surfaces: list[Surface]
    wavelengths_nm: list[float] = [587.56]  # d-line default
    primary_wavelength_index: int = 0
    stop_surface: int | None = None
    
    # Computed properties
    @property
    def num_surfaces(self) -> int: ...
    
    @property
    def total_length(self) -> float: ...
    
    @property
    def primary_wavelength(self) -> float: ...
    
    def get_surface(self, index: int) -> Surface: ...
```

#### OBBMetadata

```python
class OBBMetadata(BaseModel):
    """Metadata for OBB file."""
    
    vendor_id: str  # 3-50 chars, lowercase
    name: str  # Component name
    efl_mm: float
    bfl_mm: float
    na: float
    diameter_mm: float
    spectral_range_nm: tuple[float, float]
    
    # Optional
    description: str | None = None
    part_number: str | None = None
    created_at: datetime | None = None
    signature: str = ""  # Set by writer
```

**Example:**

```python
from optical_blackbox.models import Surface, SurfaceGroup, OBBMetadata

# Create surface
s1 = Surface(
    surface_number=1,
    radius=100.0,
    thickness=5.0,
    material="N-BK7",
    semi_diameter=12.7,
)

# Create group
group = SurfaceGroup(
    surfaces=[s1],
    wavelengths_nm=[486.13, 587.56, 656.27],
)

# Create metadata
meta = OBBMetadata(
    vendor_id="thorlabs",
    name="AC254-050-A",
    efl_mm=50.0,
    bfl_mm=45.0,
    na=0.25,
    diameter_mm=25.4,
    spectral_range_nm=(400.0, 700.0),
)
```

---

### optics.paraxial - Paraxial Calculations

ABCD matrix paraxial optics.

#### compute_paraxial_properties

```python
def compute_paraxial_properties(
    surface_group: SurfaceGroup,
    wavelength_nm: float | None = None,
) -> dict[str, float]:
    """Compute paraxial optical properties.
    
    Returns:
        {
            "efl_mm": float,  # Effective focal length
            "bfl_mm": float,  # Back focal length
            "na": float,      # Numerical aperture
        }
    """
```

**Example:**

```python
from optical_blackbox.optics.paraxial import compute_paraxial_properties

props = compute_paraxial_properties(surface_group)
print(f"EFL: {props['efl_mm']:.2f} mm")
print(f"BFL: {props['bfl_mm']:.2f} mm")
print(f"NA: {props['na']:.3f}")
```

---

### core.result - Error Handling

Rust-inspired Result type for explicit error handling.

#### Result Type

```python
Result[T, E] = Ok[T] | Err[E]

class Ok[T]:
    def unwrap(self) -> T: ...
    def is_ok(self) -> bool: ...
    def map(self, func: Callable[[T], U]) -> Ok[U]: ...

class Err[E]:
    def unwrap(self) -> None:  # Raises error
    def is_err(self) -> bool: ...
    def unwrap_or(self, default: T) -> T: ...
```

**Example:**

```python
from optical_blackbox.core.result import Ok, Err

def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)

result = divide(10, 2)
if result.is_ok():
    print(result.unwrap())  # 5.0
else:
    print(f"Error: {result.error}")
```

---

## CLI Reference

### obb generate-keypair

Generate ECDSA P-256 key pair.

```bash
obb generate-keypair --role vendor --output-dir keys/
```

Options:
- `--role`: vendor or platform
- `--output-dir`: Output directory (default: current)
- `--password`: Encrypt private key

### obb encrypt

Encrypt Zemax file to OBB format.

```bash
obb encrypt lens.zmx \
    --output lens.obb \
    --vendor-private-key keys/vendor.key \
    --platform-public-key keys/platform.pub \
    --vendor-id thorlabs \
    --name "AC254-050-A"
```

### obb decrypt

Decrypt OBB file.

```bash
obb decrypt lens.obb \
    --output lens.zmx \
    --platform-private-key keys/platform.key \
    --vendor-public-key keys/vendor.pub
```

### obb info

Display OBB file metadata.

```bash
obb info lens.obb
```

---

## Error Handling

All errors inherit from `OBBError`:

```python
from optical_blackbox.exceptions import (
    OBBError,
    DecryptionError,
    InvalidSignatureError,
    InvalidKeyError,
    ParserError,
)

try:
    metadata, surfaces = OBBReader.read_and_decrypt(...)
except InvalidSignatureError:
    print("Signature verification failed!")
except DecryptionError:
    print("Wrong decryption key!")
except OBBError as e:
    print(f"Error: {e}")
```

---

## Type Hints

Full type hint support:

```python
from optical_blackbox.crypto.keys import KeyManager
from cryptography.hazmat.primitives.asymmetric import ec

priv: ec.EllipticCurvePrivateKey
pub: ec.EllipticCurvePublicKey
priv, pub = KeyManager.generate_keypair()
```

Run type checking:

```bash
mypy your_script.py
```

---

## Examples

See [examples/](../examples/) for complete scripts:
- `encrypt_lens.py` - Full encryption workflow
- `decrypt_lens.py` - Decryption and validation
- `batch_convert.py` - Batch processing

---

For more details, see [OPTICAL_BLACKBOX_SPEC.md](../OPTICAL_BLACKBOX_SPEC.md).
