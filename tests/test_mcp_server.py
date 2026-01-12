#!/usr/bin/env python3
"""
Test script for MCP server functionality
Tests the underlying logic without MCP decorators
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the underlying modules directly
from gesetzessuche.search import LawSearch
from gesetzessuche.utils import get_law, load_law_mapping, parse_law_reference


def test_list_laws():
    """Test listing available laws"""
    print("Testing list_laws()...")
    mapping = load_law_mapping()

    laws = []
    for code, info in sorted(mapping.items()):
        laws.append(
            {
                "code": code,
                "title": info.get("title", ""),
                "category": info.get("category", ""),
            }
        )

    result = {"total": len(laws), "laws": laws}

    print(f"  ✓ Found {result['total']} laws")
    if result["laws"]:
        print(f"    Sample: {', '.join([law['code'] for law in result['laws'][:5]])}")
    assert result["total"] > 0
    print()


def test_get_law_reference():
    """Test getting law content by reference"""
    print("Testing get_law_reference('HGB § 1')...")
    reference = "HGB § 1"

    # Parse reference
    parsed = parse_law_reference(reference)
    assert parsed is not None
    assert parsed["law"] == "HGB"

    # Load law
    dokumente = get_law(parsed["law"], auto_download=False)
    assert dokumente is not None

    # Create search instance
    law_key = dokumente.get_jurabk()[0] if dokumente.get_jurabk() else "HGB"
    search = LawSearch(dokumente, law_key)

    # Get by reference
    result = search.get_by_reference(reference)

    print(f"  Result length: {len(result)}")
    print(f"  First 100 chars: {result[:100]}")
    assert "error" not in result.lower() and "❌" not in result
    assert len(result) > 0
    print("  ✓ Reference retrieved successfully")
    print()


def test_get_law_reference_with_absatz():
    """Test getting law content with Absatz"""
    print("Testing get_law_reference('KStG § 6 Absatz 1')...")
    reference = "KStG § 6 Absatz 1"

    # Parse reference
    parsed = parse_law_reference(reference)
    assert parsed is not None

    # Load law
    dokumente = get_law(parsed["law"], auto_download=False)
    assert dokumente is not None

    # Create search instance
    law_key = dokumente.get_jurabk()[0] if dokumente.get_jurabk() else "KSTG"
    search = LawSearch(dokumente, law_key)

    # Get by reference
    result = search.get_by_reference(reference)

    print(f"  Result length: {len(result)}")
    assert "error" not in result.lower() and "❌" not in result
    assert "KStG" in result or "§ 6" in result
    print("  ✓ Reference with Absatz retrieved successfully")
    print()


def test_list_paragraphs():
    """Test listing paragraphs"""
    print("Testing list_paragraphs('HGB', limit=5)...")

    # Load law
    dokumente = get_law("HGB", auto_download=False)
    assert dokumente is not None

    # Create search instance
    law_key = dokumente.get_jurabk()[0] if dokumente.get_jurabk() else "HGB"
    search = LawSearch(dokumente, law_key)

    # List paragraphs
    all_paragraphs = search.list_all_paragraphs()
    limit = 5

    result = {
        "law": "HGB",
        "total": len(all_paragraphs),
        "shown": min(limit, len(all_paragraphs)),
        "paragraphs": all_paragraphs[:limit],
    }

    print(f"  Total: {result.get('total')}")
    print(f"  Shown: {result.get('shown')}")
    if result.get("paragraphs"):
        for p in result["paragraphs"][:3]:
            print(f"    - {p.get('number')}: {p.get('title')}")
    assert "error" not in result
    assert result.get("shown", 0) <= 5
    print("  ✓ Paragraphs listed successfully")
    print()


def test_search_law():
    """Test searching within a law"""
    print("Testing search_law('HGB', 'Handelsregister', max_results=3)...")

    # Load law
    dokumente = get_law("HGB", auto_download=False)
    assert dokumente is not None

    # Create search instance
    law_key = dokumente.get_jurabk()[0] if dokumente.get_jurabk() else "HGB"
    search = LawSearch(dokumente, law_key)

    # Search
    results = search.search_term("Handelsregister", case_sensitive=False)
    max_results = 3
    limited_results = results[:max_results]

    result = {
        "law": "HGB",
        "term": "Handelsregister",
        "found": len(limited_results),
        "total_matches": len(results),
        "results": limited_results,
    }

    print(f"  Found: {result.get('found')} matches")
    print(f"  Total matches: {result.get('total_matches')}")
    if result.get("results"):
        for idx, r in enumerate(result["results"][:2], 1):
            print(f"    {idx}. {r.get('paragraph')}")
            print(f"       {r.get('context')[:60]}...")
    assert "error" not in result
    assert result.get("found", 0) > 0
    print("  ✓ Search completed successfully")
    print()


def test_error_handling():
    """Test error handling for non-existent law"""
    print("Testing error handling with non-existent law...")
    dokumente = get_law("NONEXISTENT", auto_download=False)
    assert dokumente is None, "Expected None for non-existent law"
    print("  ✓ Error handling works correctly (returns None)")
    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Server Functionality Tests")
    print("=" * 60)
    print()

    try:
        test_list_laws()
        test_get_law_reference()
        test_get_law_reference_with_absatz()
        test_list_paragraphs()
        test_search_law()
        test_error_handling()

        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
