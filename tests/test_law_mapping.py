#!/usr/bin/env python3
"""
Minimal test to verify law_mapping.json can be accessed.
"""

from pathlib import Path
from gesetzessuche.utils import load_law_mapping


def test_law_mapping_exists():
    """Test that law_mapping.json can be loaded from package."""
    # Load from package directory
    package_dir = Path(__file__).parent.parent / "gesetzessuche"
    mapping_file = package_dir / "law_mapping.json"

    assert mapping_file.exists(), f"law_mapping.json not found at {mapping_file}"
    print(f"✓ law_mapping.json found at {mapping_file}")


def test_load_law_mapping():
    """Test that law_mapping can be loaded."""
    mapping = load_law_mapping()

    assert mapping is not None, "Failed to load law_mapping"
    assert len(mapping) > 0, "law_mapping is empty"
    assert "BGB" in mapping, "BGB not found in mapping"

    print(f"✓ Loaded {len(mapping)} laws from law_mapping.json")
    print(f"✓ BGB found: {mapping['BGB']['title']}")


if __name__ == "__main__":
    test_law_mapping_exists()
    test_load_law_mapping()
    print("\n✓ All tests passed!")
