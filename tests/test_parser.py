#!/usr/bin/env python3
"""Test script to parse example XML files"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gesetzessuche.parser import parse_gesetz


def parse_xml_file(xml_file: Path) -> bool:
    """Parse a single XML file (not a pytest test)"""
    print(f"\n{'=' * 80}")
    print(f"Testing: {xml_file.name}")
    print(f"{'=' * 80}")

    try:
        dokumente = parse_gesetz(xml_file)

        print(f"✓ Successfully parsed {xml_file.name}")
        print(f"  - Build date: {dokumente.builddate}")
        print(f"  - Document number: {dokumente.doknr}")
        print(f"  - Title: {dokumente.get_titel()}")
        print(f"  - Abbreviations: {', '.join(dokumente.get_jurabk())}")
        print(f"  - Total norms: {len(dokumente.normen)}")
        print(f"  - Paragraphs: {len(dokumente.get_paragraphen())}")
        print(f"  - Structure elements: {len(dokumente.get_gliederung())}")

        # Show first few paragraphs
        paragraphs = dokumente.get_paragraphen()[:3]
        if paragraphs:
            print("\n  First paragraphs:")
            for p in paragraphs:
                if p.metadaten and p.metadaten.enbez:
                    print(
                        f"    - {p.metadaten.enbez}: {p.metadaten.titel or '(no title)'}"
                    )

        return True
    except Exception as e:
        print(f"✗ Failed to parse {xml_file.name}")
        print(f"  Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def main() -> None:
    """Test all data XML files"""
    data_dir = Path("data")
    xml_files = sorted(data_dir.glob("*.xml"))

    if not xml_files:
        print("No XML files found in data/ directory")
        return

    print(f"Found {len(xml_files)} XML files to test")

    results = []
    for xml_file in xml_files:
        success = parse_xml_file(xml_file)
        results.append((xml_file.name, success))

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    successful = sum(1 for _, success in results if success)
    total = len(results)

    for filename, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {filename}")

    print(f"\nTotal: {successful}/{total} files parsed successfully")

    if successful == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - successful} file(s) failed")


if __name__ == "__main__":
    main()
