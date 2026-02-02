# MVP Limitations

This document tracks simplifications and limitations in the MVP release of Optical BlackBox.

## Scope

The MVP focuses on the core functionality needed to:
1. Parse Zemax designs (.zmx, .zar)
2. Encrypt and sign surface data
3. Create .obb files for distribution
4. Inspect metadata from .obb files

---

## Parser Limitations

### Supported Formats
- ✅ Zemax Sequential (.zmx)
- ✅ Zemax Archive (.zar)
- ❌ CODE V (.seq, .len)
- ❌ Oslo
- ❌ SYNOPSYS

### Zemax Parsing Limitations

**Unsupported Surface Types:**
- Zernike polynomial surfaces
- Q-type aspheres (Q-con, Q-bfs)
- Freeform surfaces (XY Polynomial, Grid Sag)
- Binary optics / diffractive
- Gradient index (GRIN)
- User-defined surfaces
- Toroidal surfaces
- Biconic surfaces

**Supported Surface Types:**
- Standard (spherical)
- Even Asphere (up to 16th order)
- Plane / Flat

**Ignored Zemax Keywords:**
- `CONF` - Configuration data (multi-config)
- `COAT` - Coating specifications
- `MIRR` - Mirror surfaces (treated as refraction)
- `PARM` - Extra parameters beyond standard asphere
- `XDAT`, `UDAT` - Extra/User data
- `MOFF` - Multi-configuration offsets
- `PICL` - Pick-up coupling
- `ELOB` - Element obscuration
- `OPDX` - OPD data

**Encoding:**
- Assumes UTF-16-LE for .zmx files (standard Zemax encoding)
- Falls back to UTF-8 if UTF-16 fails

---

## Optical Calculations

### Glass Catalog

**MVP Implementation:**
- Single wavelength: d-line (587.56 nm)
- ~40 common glasses from Schott catalog
- No dispersion formulas (Sellmeier, etc.)
- Unknown glasses default to n=1.5

**Missing Features:**
- Temperature-dependent index
- Inhomogeneity coefficients
- Custom glass definitions
- Private catalog import
- Wavelength interpolation

### Paraxial Analysis

**Implemented:**
- ABCD matrix raytracing
- Effective Focal Length (EFL)
- Back Focal Length (BFL)
- Numerical Aperture (NA) approximation

**Not Implemented:**
- Front Focal Length (FFL)
- Principal plane locations
- Nodal points
- Petzval curvature
- Real ray tracing
- Aberration analysis
- MTF calculations
- Tolerance analysis

---

## Cryptography

### Implemented
- ECDSA P-256 for signatures
- ECDH P-256 for key exchange
- AES-256-GCM for encryption
- HKDF-SHA256 for key derivation

### Limitations
- No key rotation mechanism
- No certificate chain validation
- No HSM integration
- No key backup/recovery
- Single recipient encryption only (no broadcast encryption)

---

## File Format

### Implemented
- Magic bytes: `OBB\x01`
- JSON header with metadata
- AES-256-GCM encrypted payload
- ECDSA signature

### Limitations
- No streaming encryption (entire payload in memory)
- No compression before encryption
- No partial decryption
- File size limited by available memory

---

## CLI

### Implemented Commands
- `obb keygen` - Generate key pair
- `obb create` - Create .obb file
- `obb inspect` - View metadata

### Missing Commands
- `obb verify` - Verify signature without decryption
- `obb decrypt` - Full decryption (Agent Etendue only)
- `obb convert` - Format conversion
- `obb validate` - Validate structure

---

## Integration

### Agent Etendue
- Decryption designed for Agent Etendue raytracer
- MVP does not include Agent Etendue integration code
- Black-box raytrace API not included

### API
- Python API for programmatic use
- No REST API
- No gRPC interface

---

## Future Roadmap

### Phase 2
- [ ] Additional surface types (Zernike, Q-type)
- [ ] Multi-wavelength glass catalog
- [ ] CODE V parser
- [ ] Streaming encryption

### Phase 3
- [ ] Full aberration analysis
- [ ] Agent Etendue integration
- [ ] REST API
- [ ] Broadcast encryption

### Phase 4
- [ ] HSM support
- [ ] Certificate chains
- [ ] Audit logging
- [ ] Enterprise key management

---

## Known Issues

1. **Large Files**: Files > 100MB may cause memory issues
2. **Unicode Paths**: Non-ASCII paths may have issues on Windows
3. **Concurrent Access**: No file locking during write operations

---

## Contributing

When adding features, please update this document to reflect:
- What was implemented
- What limitations remain
- Known issues discovered

Maintainer: ThibautA
