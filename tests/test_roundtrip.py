"""Test round-trip encryption/decryption of .zmx files."""

import sys
import tempfile
from pathlib import Path

# Add src to path for testing without install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from optical_blackbox.crypto.keys import KeyManager
from optical_blackbox.parsers import ZemaxParser
from optical_blackbox.optics import extract_metadata
from optical_blackbox.formats.obb_file import OBBWriter, OBBReader


def test_roundtrip(zmx_path: Path) -> bool:
    """Test encrypt/decrypt round-trip for a .zmx file.
    
    Returns True if successful, False otherwise.
    """
    print(f"\n{'='*60}")
    print(f"Testing: {zmx_path.name}")
    print('='*60)
    
    try:
        # 1. Generate keys
        print("1. Generating keys...")
        vendor_private, vendor_public = KeyManager.generate_keypair()
        platform_private, platform_public = KeyManager.generate_keypair()
        
        # 2. Parse .zmx file
        print("2. Parsing Zemax file...")
        parser = ZemaxParser()
        
        try:
            original_surfaces = parser.parse(zmx_path)
        except Exception as parse_error:
            print(f"   ERROR: Failed to parse - {parse_error}")
            return False
        
        print(f"   Found {original_surfaces.num_surfaces} surfaces")
        
        # 3. Extract metadata
        print("3. Extracting metadata...")
        metadata = extract_metadata(
            surface_group=original_surfaces,
            vendor_id="test-vendor",
            name=zmx_path.stem,
            description="Test encryption round-trip",
        )
        print(f"   EFL: {metadata.efl_mm:.2f} mm, NA: {metadata.na:.4f}")
        
        # 4. Write encrypted .obb file
        print("4. Writing encrypted .obb file...")
        with tempfile.NamedTemporaryFile(suffix=".obb", delete=False) as f:
            obb_path = Path(f.name)
        
        OBBWriter.write(
            output_path=obb_path,
            surface_group=original_surfaces,
            metadata=metadata,
            vendor_private_key=vendor_private,
            platform_public_key=platform_public,
        )
        
        file_size = obb_path.stat().st_size
        print(f"   Created: {obb_path.name} ({file_size} bytes)")
        
        # 5. Read metadata (without decryption)
        print("5. Reading metadata from .obb...")
        try:
            read_metadata = OBBReader.read_metadata(obb_path)
        except Exception as read_error:
            print(f"   ERROR: Failed to read metadata - {read_error}")
            return False
        
        print(f"   Name: {read_metadata.name}")
        print(f"   Surfaces: {read_metadata.num_surfaces}")
        
        # 6. Decrypt and read surfaces
        print("6. Decrypting .obb file...")
        try:
            decrypted_meta, decrypted_surfaces = OBBReader.read_and_decrypt(
                obb_path,
                platform_private_key=platform_private,
                vendor_public_key=vendor_public,
            )
        except Exception as decrypt_error:
            print(f"   ERROR: Failed to decrypt - {decrypt_error}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"   Decrypted {decrypted_surfaces.num_surfaces} surfaces")
        
        # 7. Verify round-trip
        print("7. Verifying round-trip...")
        
        # Check number of surfaces
        if original_surfaces.num_surfaces != decrypted_surfaces.num_surfaces:
            print(f"   ERROR: Surface count mismatch: {original_surfaces.num_surfaces} vs {decrypted_surfaces.num_surfaces}")
            return False
        
        # Check each surface
        for i, (orig, decr) in enumerate(zip(original_surfaces.surfaces, decrypted_surfaces.surfaces)):
            if abs(orig.radius - decr.radius) > 1e-10:
                print(f"   ERROR: Surface {i} radius mismatch: {orig.radius} vs {decr.radius}")
                return False
            if abs(orig.thickness - decr.thickness) > 1e-10:
                print(f"   ERROR: Surface {i} thickness mismatch: {orig.thickness} vs {decr.thickness}")
                return False
            if orig.material != decr.material:
                print(f"   ERROR: Surface {i} material mismatch: {orig.material} vs {decr.material}")
                return False
        
        # Cleanup
        obb_path.unlink()
        
        print("\n✓ ROUND-TRIP SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run round-trip tests on sample .zmx files."""
    testdata = Path(__file__).parent.parent / "testdata"
    
    # Find some .zmx files to test
    zmx_files = list(testdata.rglob("*.zmx"))[:20]  # Test first 20 files
    
    if not zmx_files:
        print("No .zmx files found in testdata/")
        return 1
    
    print(f"Found {len(zmx_files)} .zmx files to test")
    
    results = []
    for zmx_path in zmx_files:
        success = test_roundtrip(zmx_path)
        results.append((zmx_path.name, success))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, s in results if s)
    failed = len(results) - passed
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{len(results)} passed")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
