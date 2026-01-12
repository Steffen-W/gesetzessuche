#!/usr/bin/env python3
"""Test that all Pydantic models with forward references work correctly"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gesetzessuche.models import (
    DD,
    LA,
    TOC,
    Content,
    Entry,
    Footnote,
    FormatElement,
    P,
    Revision,
)


def test_footnote_creation() -> None:
    """Test Footnote model can be created"""
    footnote = Footnote(
        id="fn1",
        prefix="*",
        fn_z="1",
        content=["Test footnote text"],
    )
    assert footnote.id == "fn1"
    assert footnote.content == ["Test footnote text"]
    print("✓ Footnote model works")


def test_entry_creation() -> None:
    """Test Entry model can be created"""
    entry = Entry(
        id="entry1",
        content=["Cell content", "More content"],
    )
    assert entry.id == "entry1"
    assert len(entry.content) == 2
    print("✓ Entry model works")


def test_toc_creation() -> None:
    """Test TOC model can be created"""
    toc = TOC(id="toc1", content=["TOC item 1", "TOC item 2"])
    assert toc.id == "toc1"
    assert len(toc.content) == 2
    print("✓ TOC model works")


def test_p_creation() -> None:
    """Test P (paragraph) model can be created"""
    p = P(id="p1", content=["Paragraph text"], raw_text="Paragraph text")
    assert p.id == "p1"
    assert len(p.content) == 1
    print("✓ P model works")


def test_la_creation() -> None:
    """Test LA model can be created"""
    la = LA(id="la1", size="normal", children=["List item"])
    assert la.id == "la1"
    assert la.size == "normal"
    print("✓ LA model works")


def test_dd_creation() -> None:
    """Test DD model can be created"""
    dd = DD(id="dd1", la=None, revisions=[])
    assert dd.id == "dd1"
    print("✓ DD model works")


def test_format_element_creation() -> None:
    """Test FormatElement can be created"""
    fmt = FormatElement(tag="B", text="Bold text", children=["nested"])
    assert fmt.tag == "B"
    assert fmt.text == "Bold text"
    print("✓ FormatElement model works")


def test_revision_creation() -> None:
    """Test Revision model can be created"""
    rev = Revision(id="rev1", content=["Revision content"])
    assert rev.id == "rev1"
    print("✓ Revision model works")


def test_content_creation() -> None:
    """Test Content model can be created"""
    content = Content(id="content1", elements=["Text element"], raw_text="Text")
    assert content.id == "content1"
    print("✓ Content model works")


def test_nested_content() -> None:
    """Test nested content elements work"""
    p = P(
        id="p1",
        content=["Text ", FormatElement(tag="B", text="bold")],
        raw_text="Text bold",
    )
    assert len(p.content) == 2
    assert isinstance(p.content[1], FormatElement)
    print("✓ Nested content elements work")


def main() -> None:
    """Run all forward reference tests"""
    print("Testing Pydantic model forward references...\n")

    test_footnote_creation()
    test_entry_creation()
    test_toc_creation()
    test_p_creation()
    test_la_creation()
    test_dd_creation()
    test_format_element_creation()
    test_revision_creation()
    test_content_creation()
    test_nested_content()

    print("\n✅ All forward reference tests passed!")


if __name__ == "__main__":
    main()
