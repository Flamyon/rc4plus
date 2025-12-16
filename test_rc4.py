#!/usr/bin/env python3
"""
Script de prueba rápida para verificar el funcionamiento del visualizador RC4/RC4+
"""

import sys
from rc4_crypto import RC4Classic, RC4Plus, encrypt_decrypt


def test_rc4_classic():
    """Test RC4 classic implementation"""
    print("=" * 60)
    print("Testing RC4 Classic")
    print("=" * 60)

    rc4 = RC4Classic(256)
    key = "SecretKey"
    plaintext = b"Hello RC4"

    # KSA
    rc4.ksa(key)
    print(f"✓ KSA completed with key: '{key}'")

    # Generate keystream
    keystream = []
    for _ in range(len(plaintext)):
        result = rc4.prga_step()
        keystream.append(result["output_byte"])

    print(f"✓ Generated {len(keystream)} keystream bytes")
    print(f"  Keystream: {' '.join([f'{b:02x}' for b in keystream])}")

    # Encrypt
    ciphertext = encrypt_decrypt(plaintext, keystream)
    print(f"  Plaintext:  {plaintext}")
    print(f"  Ciphertext: {' '.join([f'{b:02x}' for b in ciphertext])}")

    # Decrypt
    rc4_decrypt = RC4Classic(256)
    rc4_decrypt.ksa(key)
    keystream_decrypt = []
    for _ in range(len(ciphertext)):
        result = rc4_decrypt.prga_step()
        keystream_decrypt.append(result["output_byte"])

    recovered = encrypt_decrypt(ciphertext, keystream_decrypt)
    print(f"  Recovered:  {bytes(recovered)}")

    if bytes(recovered) == plaintext:
        print("✓ RC4 Classic test PASSED: Encryption/Decryption is symmetric")
        return True
    else:
        print("✗ RC4 Classic test FAILED")
        return False


def test_rc4_plus():
    """Test RC4+ implementation"""
    print("\n" + "=" * 60)
    print("Testing RC4+")
    print("=" * 60)

    rc4plus = RC4Plus()
    key = "SecretKey"
    plaintext = b"Hello RC4+"

    # KSA
    rc4plus.ksa(key)
    print(f"✓ KSA completed with key: '{key}'")

    # Generate keystream
    keystream = []
    for _ in range(len(plaintext)):
        result = rc4plus.prga_step()
        keystream.append(result["output_byte"])

        # Verify RC4+ specific fields
        if "t_prime" not in result or "t_double" not in result:
            print("✗ RC4+ result missing t_prime or t_double")
            return False

    print(f"✓ Generated {len(keystream)} keystream bytes (with t_prime and t_double)")
    print(f"  Keystream: {' '.join([f'{b:02x}' for b in keystream])}")

    # Encrypt
    ciphertext = encrypt_decrypt(plaintext, keystream)
    print(f"  Plaintext:  {plaintext}")
    print(f"  Ciphertext: {' '.join([f'{b:02x}' for b in ciphertext])}")

    # Decrypt
    rc4plus_decrypt = RC4Plus()
    rc4plus_decrypt.ksa(key)
    keystream_decrypt = []
    for _ in range(len(ciphertext)):
        result = rc4plus_decrypt.prga_step()
        keystream_decrypt.append(result["output_byte"])

    recovered = encrypt_decrypt(ciphertext, keystream_decrypt)
    print(f"  Recovered:  {bytes(recovered)}")

    if bytes(recovered) == plaintext:
        print("✓ RC4+ test PASSED: Encryption/Decryption is symmetric")
        return True
    else:
        print("✗ RC4+ test FAILED")
        return False


def test_modules_import():
    """Test that all modules import correctly"""
    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    try:
        from rc4_crypto import RC4Classic, RC4Plus, encrypt_decrypt, generate_keystream

        print("✓ rc4_crypto module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import rc4_crypto: {e}")
        return False

    try:
        from rc4_visualization import StateVisualizer, LogManager

        print("✓ rc4_visualization module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import rc4_visualization: {e}")
        return False

    try:
        from rc4_ui import ControlPanel, ButtonPanel, ResultPanel, StateVariablesPanel

        print("✓ rc4_ui module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import rc4_ui: {e}")
        return False

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("RC4/RC4+ Visualizer - Test Suite")
    print("=" * 60 + "\n")

    results = []

    # Test imports
    results.append(("Module Imports", test_modules_import()))

    # Test RC4 Classic
    results.append(("RC4 Classic", test_rc4_classic()))

    # Test RC4+
    results.append(("RC4+", test_rc4_plus()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:20s}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
