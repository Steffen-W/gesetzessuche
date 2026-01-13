"""
MCP Gesetze - Parser for German federal laws
Complete DTD-compliant implementation

Public API:
    - parse_gesetz: Main function for parsing law XML
    - Dokumente: Main container for a law document
    - Norm: Individual norm (paragraph/article)
    - Metadaten: Metadata of a norm
    - Content: Text content
    - GesetzParser: Parser class for advanced usage

Search and Query:
    - LawSearch: Search and query class for law documents
    - SearchResult: TypedDict for search results
    - LawMapping: TypedDict for law mapping entries

Utility Functions:
    - get_law: Load a law by its code
    - load_law_mapping: Load law mapping from law_mapping.json
    - save_law_mapping: Save law mapping to law_mapping.json
    - find_law_in_mapping: Find law in mapping by code
    - extract_text_from_norm: Extract text from a Norm object
    - extract_text_from_p: Extract text from a P element
    - load_toc_index: Load TOC index from gii-toc.xml
    - find_law_in_toc: Find law in TOC by code
    - download_laws_batch: Batch download laws

Formatting Functions:
    - extract_text_from_elements: Extract text from content elements
    - process_dl_list: Process definition lists with proper formatting
    - format_p_element: Format a P element with lists and proper indentation
"""

from .models import (
    Content,
    Dokumente,
    LawMapping,
    LawReference,
    Metadaten,
    Norm,
    SearchResult,
)
from .parser import GesetzParser, parse_gesetz
from .search import LawSearch
from .utils import (
    download_laws_batch,
    extract_text_from_norm,
    extract_text_from_p,
    find_law_in_mapping,
    find_law_in_toc,
    get_law,
    load_law_mapping,
    load_toc_index,
    parse_law_reference,
    save_law_mapping,
)
from .formatting import (
    extract_text_from_elements,
    process_dl_list,
    format_p_element,
)

__all__ = [
    # Main classes
    "Dokumente",
    "Norm",
    # Parser
    "parse_gesetz",
    "GesetzParser",
    # Search and Query
    "LawSearch",
    "SearchResult",
    "LawMapping",
    "LawReference",
    # Advanced usage
    "Metadaten",
    "Content",
    # Utility Functions
    "get_law",
    "load_law_mapping",
    "save_law_mapping",
    "find_law_in_mapping",
    "extract_text_from_norm",
    "extract_text_from_p",
    "load_toc_index",
    "find_law_in_toc",
    "download_laws_batch",
    "parse_law_reference",
    # Formatting Functions
    "extract_text_from_elements",
    "process_dl_list",
    "format_p_element",
]
