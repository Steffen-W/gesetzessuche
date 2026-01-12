#!/usr/bin/env python3
"""
Test script to verify MCP server caching performance
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gesetzessuche import server


def test_caching_performance():
    """Test that caching improves performance on repeated access"""
    print("=" * 60)
    print("MCP Server Caching Performance Test")
    print("=" * 60)
    print()

    # Clear cache first
    server._search_cache.clear()
    print("Cache cleared")
    print()

    # First load (cold cache)
    print("First load (cold cache):")
    start = time.time()
    search1 = server._get_search("HGB")
    time1 = (time.time() - start) * 1000
    print(f"  Time: {time1:.1f}ms")
    assert search1 is not None
    print()

    # Second load (cached)
    print("Second load (from cache):")
    start = time.time()
    search2 = server._get_search("HGB")
    time2 = (time.time() - start) * 1000
    print(f"  Time: {time2:.1f}ms")
    assert search2 is not None
    print()

    # Verify it's the same object (cached)
    assert search1 is search2, "Should return same cached object"
    print("✓ Caching verified (same object returned)")
    print()

    # Performance improvement
    speedup = time1 / time2 if time2 > 0 else float("inf")
    print(f"Performance improvement: {speedup:.0f}x faster")
    print()

    # Verify cache contains HGB
    assert "HGB" in server._search_cache
    print(f"✓ Cache contains: {', '.join(server._search_cache.keys())}")
    print()

    # Load another law
    print("Loading another law (KSTG):")
    start = time.time()
    search3 = server._get_search("KSTG")
    time3 = (time.time() - start) * 1000
    print(f"  Time: {time3:.1f}ms")
    assert search3 is not None
    print()

    # Verify both are cached
    assert len(server._search_cache) == 2
    print(f"✓ Cache now contains: {', '.join(server._search_cache.keys())}")
    print()

    print("=" * 60)
    print("✓ Caching test passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_caching_performance()
