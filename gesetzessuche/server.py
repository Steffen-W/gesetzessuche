#!/usr/bin/env python3
"""
MCP Server for German Law Documents
Provides intuitive access to German law paragraphs via natural reference strings

Key features:
- Natural reference parsing: "KStG § 6 Absatz 1"
- Lazy loading with caching for performance
- Search across law documents
- Auto-download missing laws
"""

import logging

from fastmcp import FastMCP

# Relative imports
from .models import SearchResult
from .search import LawSearch
from .utils import get_law, load_law_mapping

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("German Law Documents")

# Cache for LawSearch instances (lazy loading for performance)
_search_cache: dict[str, LawSearch] = {}


def _get_search(law_code: str) -> LawSearch | None:
    """
    Get a LawSearch instance with caching and auto-download.

    Args:
        law_code: Law code (e.g., 'HGB', 'KSTG')

    Returns:
        LawSearch instance or None if not found
    """
    law_upper = law_code.upper()

    # Return from cache if available
    if law_upper in _search_cache:
        return _search_cache[law_upper]

    # Load law document with auto-download
    dokumente = get_law(law_code, auto_download=True)

    if not dokumente:
        return None

    # Get law code from jurabk
    law_key = dokumente.get_jurabk()[0] if dokumente.get_jurabk() else law_upper

    # Create and cache LawSearch instance
    search = LawSearch(dokumente, law_key)
    _search_cache[law_upper] = search

    return search


@mcp.tool()
def list_laws() -> dict[str, int | list[dict[str, str]]]:
    """
    List all available German laws from law_mapping.json.

    Returns:
        Dictionary with list of laws and their details

    Examples:
        >>> list_laws()
        {'total': 150, 'laws': [{'code': 'HGB', 'title': 'Handelsgesetzbuch', ...}, ...]}
    """
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

    return {"total": len(laws), "laws": laws}


@mcp.tool()
def get_law_reference(reference: str) -> str:
    """
    Get law content by reference string - THE PRIMARY TOOL.

    Supports natural references like:
    - "KStG § 6 Absatz 1" (law code included)
    - "BGB § 1" (just paragraph)
    - "HGB § 8b Absatz 2" (paragraph with section)
    - "GmbHG § 13 Absatz 2 Satz 1" (full reference)

    Args:
        reference: Full law reference string with law code

    Returns:
        Formatted law text

    Examples:
        >>> get_law_reference("KStG § 6 Absatz 1")
        "======================================================================
        KStG § 6 Absatz 1
        ======================================================================"

        >>> get_law_reference("BGB § 1")
        "Full paragraph text..."
    """
    # Parse reference to extract law code
    from .utils import parse_law_reference

    parsed = parse_law_reference(reference)

    if not parsed or not parsed["law"]:
        return f"❌ Error: Reference must include law code (e.g., 'BGB § 1')\nGot: '{reference}'"

    # Get LawSearch instance
    search = _get_search(parsed["law"])
    if not search:
        return f"❌ Law '{parsed['law']}' not found"

    # Get content using reference parser
    result = search.get_by_reference(reference)

    if not result:
        return f"❌ Could not find or parse reference: '{reference}'"

    return result


@mcp.tool()
def search_law(
    law: str, search_term: str, max_results: int = 5
) -> dict[str, str | int | list[SearchResult]]:
    """
    Search for a term within a specific law.

    Args:
        law: Law code (e.g., 'HGB', 'BGB', 'KSTG')
        search_term: Text to search for (case-insensitive)
        max_results: Maximum number of results (default: 5)

    Returns:
        Dictionary with search results

    Examples:
        >>> search_law('HGB', 'Handelsregister', max_results=3)
        {'law': 'HGB', 'term': 'Handelsregister', 'found': 3,
         'results': [{'paragraph': '§ 2', 'title': '...', 'context': '...'}, ...]}
    """
    search = _get_search(law)
    if not search:
        return {"error": f"Law '{law}' not found"}

    results = search.search_term(search_term, case_sensitive=False)

    # Limit results
    limited_results = results[:max_results]

    return {
        "law": law.upper(),
        "term": search_term,
        "found": len(limited_results),
        "total_matches": len(results),
        "results": limited_results,
    }


@mcp.tool()
def list_paragraphs(
    law: str, limit: int = 20
) -> dict[str, str | int | list[dict[str, str]]]:
    """
    List paragraphs in a law with their titles.

    Args:
        law: Law code (e.g., 'HGB', 'BGB', 'KSTG')
        limit: Maximum number of paragraphs (default: 20)

    Returns:
        Dictionary with list of paragraphs

    Examples:
        >>> list_paragraphs('HGB', limit=5)
        {'law': 'HGB', 'total': 695, 'shown': 5,
         'paragraphs': [{'number': '§ 1', 'title': '...'}, ...]}
    """
    search = _get_search(law)
    if not search:
        return {"error": f"Law '{law}' not found"}

    all_paragraphs = search.list_all_paragraphs()

    return {
        "law": law.upper(),
        "total": len(all_paragraphs),
        "shown": min(limit, len(all_paragraphs)),
        "paragraphs": all_paragraphs[:limit],
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
