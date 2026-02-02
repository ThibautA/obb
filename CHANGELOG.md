# Changelog

All notable changes to the Optical BlackBox project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Full support for additional Zemax surface types (toroidal, odd asphere)
- Extended glass catalog (all Schott, Ohara, Hoya)
- Chromatic aberration calculations
- Ray tracing capabilities
- Multi-configuration support

## [1.0.0] - 2026-02-02

### Added
- **Core Encryption**: ECDH key exchange + AES-256-GCM hybrid encryption
- **Digital Signatures**: ECDSA P-256 signatures for vendor authentication
- **OBB File Format**: Binary format with magic bytes, header, encrypted payload
- **Zemax Parser**: Support for .zmx (UTF-16LE) and .zar (ZIP) files
- **Surface Types**: Standard (conic) and even asphere surfaces
- **Glass Catalog**: 40+ Schott glasses with refractive indices
- **Paraxial Calculations**: ABCD matrix, EFL, BFL, NA computation
- **CLI Tool**: `obb` command-line interface for encrypt/decrypt/info
- **Python API**: Full programmatic access to all features
- **Type Safety**: Pydantic v2 models with strict validation
- **Result Type**: Rust-inspired error handling pattern
- **Comprehensive Tests**: 468 unit tests with 76% code coverage

### Documentation
- Technical specification (OPTICAL_BLACKBOX_SPEC.md)
- MVP limitations document (docs/MVP_LIMITATIONS.md)
- README with quick start guide
- API documentation with examples
- Inline docstrings (Google style)

### Security
- NIST P-256 elliptic curve cryptography
- AES-256-GCM authenticated encryption
- HKDF-SHA256 key derivation
- Constant-time operations for sensitive data
- Key management with PEM format support

## [0.1.0] - 2025-12-15 (Internal Alpha)

### Added
- Initial project structure
- Basic encryption/decryption prototype
- Zemax .zmx parsing (surface data only)
- Simple CLI prototype

---

## Release Notes

### Version 1.0.0 - MVP Release

This is the first stable release of Optical BlackBox, providing a secure format for distributing encrypted optical lens designs.

**Key Features:**
- ✅ Zemax .zmx/.zar parsing (sequential systems)
- ✅ Standard and even asphere surfaces
- ✅ Hybrid encryption (ECDH + AES-256-GCM)
- ✅ Digital signatures (ECDSA P-256)
- ✅ Paraxial optical calculations
- ✅ Basic glass catalog (Schott)

**Known Limitations:**
- Parser supports sequential ray tracing only
- Limited surface types (no toroidal, odd asphere)
- Minimal glass catalog (40 glasses)
- No chromatic aberration calculations
- Single wavelength refractive index (d-line)

See [docs/MVP_LIMITATIONS.md](docs/MVP_LIMITATIONS.md) for detailed scope.

**Breaking Changes:**
- None (initial release)

**Migration Guide:**
- N/A (initial release)

---

## Versioning Policy

- **Major version** (X.0.0): Breaking API changes, file format changes
- **Minor version** (1.X.0): New features, backward-compatible
- **Patch version** (1.0.X): Bug fixes, documentation updates

## Links

- [GitHub Repository](https://github.com/ThibautA/obb)
- [Issue Tracker](https://github.com/ThibautA/obb/issues)
- [Security Policy](SECURITY.md)
- [Contributing Guide](CONTRIBUTING.md)
