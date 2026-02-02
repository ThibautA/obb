# Optical BlackBox (OBB)

[![PyPI version](https://badge.fury.io/py/optical-blackbox.svg)](https://badge.fury.io/py/optical-blackbox)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Create encrypted optical component files (`.obb`) from Zemax designs for secure distribution.

## Overview

Optical BlackBox allows optical component manufacturers to distribute their lens designs in an encrypted format that:

- **Protects IP**: Optical surface data is encrypted with AES-256-GCM
- **Enables simulation**: Platforms can decrypt and use the design for raytracing
- **Proves authenticity**: ECDSA signatures verify the vendor identity
- **Exposes metadata**: Public properties (EFL, NA, diameter) remain visible

## Installation

```bash
pip install optical-blackbox
```

## Quick Start

### 1. Generate vendor keys

```bash
obb keygen --vendor-id mycompany --output ./keys/
```

This creates:
- `mycompany_private.pem` - Keep this **SECRET**
- `mycompany_public.pem` - Register this on the platform

### 2. Get the platform's public key

Download from the platform or use the provided key file.

### 3. Create a blackbox file

```bash
obb create \
    --input my-lens.zmx \
    --private-key ./keys/mycompany_private.pem \
    --platform-key platform_public.pem \
    --vendor-id mycompany \
    --name "MY-LENS-50" \
    --output MY-LENS-50.obb
```

### 4. Inspect metadata (no decryption needed)

```bash
obb inspect MY-LENS-50.obb
```

Output:
```
┌─────────────────────────────────┐
│        OBB Metadata             │
├─────────────┬───────────────────┤
│ Version     │ 1.0               │
│ Vendor      │ mycompany         │
│ Name        │ MY-LENS-50        │
│ EFL         │ 50.0 mm           │
│ NA          │ 0.25              │
│ Diameter    │ 25.4 mm           │
│ Surfaces    │ 4                 │
│ Signature   │ ✓ Present         │
└─────────────┴───────────────────┘
```

## Security Model

```
┌──────────────────────────────────────────────────────────────────┐
│                         .obb FILE                                │
├──────────────────────────────────────────────────────────────────┤
│  PUBLIC HEADER (JSON)           │  ENCRYPTED PAYLOAD             │
│  ─────────────────────          │  ────────────────────          │
│  • vendor_id                    │  • Surface definitions         │
│  • name                         │  • Radii, thicknesses          │
│  • EFL, NA, diameter            │  • Materials                   │
│  • spectral range               │  • Aspheric coefficients       │
│  • signature (ECDSA)            │  (AES-256-GCM encrypted)       │
│  • ephemeral public key         │                                │
└──────────────────────────────────────────────────────────────────┘
```

- **Vendor Private Key**: Signs the encrypted payload, proving authenticity
- **Platform Public Key**: Encrypts the optical data (ECDH + AES-256-GCM)
- **Only the platform** can decrypt the optical surfaces
- **Anyone** can verify the signature and read metadata

## CLI Commands

| Command | Description |
|---------|-------------|
| `obb keygen` | Generate ECDSA key pair for a vendor |
| `obb create` | Create encrypted .obb from Zemax file |
| `obb inspect` | View public metadata without decryption |

## Supported Formats

### Input (MVP)
- Zemax `.zmx` (sequential mode)
- Zemax `.zar` (archive containing .zmx)

### Output
- `.obb` (Optical BlackBox format)

## Development

```bash
# Clone the repository
git clone https://github.com/ThibautA/obb.git
cd obb

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.
