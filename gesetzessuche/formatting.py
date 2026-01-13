"""
Formatting utilities for displaying German law documents.

Provides functions for:
- Extracting text from content elements
- Processing definition lists (DL elements)
- Formatting paragraphs and sections
"""

from typing import List
from .models import P, DL, ContentElement


def extract_text_from_elements(elements: List[ContentElement]) -> str:
    """
    Recursively extract text from content elements.

    Args:
        elements: List of content elements

    Returns:
        Extracted text as string
    """
    parts = []
    for elem in elements:
        if isinstance(elem, str):
            parts.append(elem)
        elif isinstance(elem, P):
            # Recursively extract from P elements
            if elem.raw_text:
                parts.append(elem.raw_text)
            elif elem.content:
                parts.append(extract_text_from_elements(elem.content))
        elif isinstance(elem, DL):
            # Skip DL in text extraction - handled separately
            continue
        elif hasattr(elem, "text") and elem.text:
            parts.append(elem.text)
        elif hasattr(elem, "content") and elem.content:
            parts.append(extract_text_from_elements(elem.content))
        elif hasattr(elem, "children") and elem.children:
            parts.append(extract_text_from_elements(elem.children))

    return " ".join(parts).strip()


def process_dl_list(
    dl: DL,
    indent_level: int = 0,
    parent_ref: str | None = None,
) -> List[str]:
    """
    Process a definition list recursively with proper indentation.

    Args:
        dl: Definition list to process
        indent_level: Current indentation level
        parent_ref: Parent reference for building hierarchical references

    Returns:
        List of formatted lines
    """
    lines = []
    indent = "  " * indent_level

    for item in dl.items:
        dt_text = item.dt.text or ""

        # Build reference - just append the DT text without labels
        if parent_ref:
            item_ref = f"{parent_ref} {dt_text}"
        else:
            item_ref = None

        # Extract DD content
        if item.dd.la:
            # Check for nested DL
            nested_dls = []
            text_parts = []
            if item.dd.la.children:
                for child in item.dd.la.children:
                    if isinstance(child, DL):
                        nested_dls.append(child)
                    elif isinstance(child, str):
                        text_parts.append(child)

            if not nested_dls:
                # Simple text - no nested lists
                text = (
                    item.dd.la.text
                    or " ".join(text_parts)
                    or extract_text_from_elements(item.dd.la.children)
                )
                if text:
                    # Show with proper formatting
                    lines.append(f"{indent}{dt_text} {text}")
            else:
                # With nested list
                intro_text = item.dd.la.text or " ".join(text_parts)
                if intro_text:
                    lines.append(f"{indent}{dt_text} {intro_text}")
                else:
                    lines.append(f"{indent}{dt_text}")

                # Process nested lists
                for nested_dl in nested_dls:
                    lines.extend(process_dl_list(nested_dl, indent_level + 1, item_ref))

    return lines


def format_p_element(
    p: P,
    paragraph_ref: str,
    skip_intro: bool = False,
) -> List[str]:
    """
    Format a single P element with proper list formatting.

    Args:
        p: P element to format
        paragraph_ref: Reference for building hierarchical references (e.g., "HGB 266 Absatz 2")
        skip_intro: If True, skip the intro text (because it's already in header)

    Returns:
        List of formatted lines
    """
    lines = []

    # Check for DL lists in content
    dl_lists = [elem for elem in p.content if isinstance(elem, DL)]

    if not dl_lists:
        # Simple text without lists
        text = p.raw_text or ""
        # Remove (1), (2) etc. prefix if present (using parsed absatz_num)
        if p.absatz_num and text.startswith(f"({p.absatz_num})"):
            text = text[len(f"({p.absatz_num})") :].strip()

        if text and not skip_intro:
            lines.append(text)
    else:
        # With lists - extract text before first DL
        intro_parts = []
        for elem in p.content:
            if isinstance(elem, DL):
                break
            if isinstance(elem, str):
                intro_parts.append(elem)

        intro_text = " ".join(intro_parts).strip()
        # Remove (1), (2) etc. prefix if present (using parsed absatz_num)
        if p.absatz_num and intro_text.startswith(f"({p.absatz_num})"):
            intro_text = intro_text[len(f"({p.absatz_num})") :].strip()

        # Only add intro text if not skipping
        if intro_text and not skip_intro:
            lines.append(intro_text)

        # Process all DL lists
        for dl in dl_lists:
            lines.extend(process_dl_list(dl, indent_level=0, parent_ref=paragraph_ref))

    return lines


def format_norm_content(
    norm,  # Type: Norm - avoiding circular import
    law_code: str,
) -> str:
    """
    Format the full text content of a norm with proper list formatting.

    Args:
        norm: Norm object to format
        law_code: Law code for building references (e.g., "HGB")

    Returns:
        Formatted text as string
    """
    if not norm.textdaten or not norm.textdaten.text:
        return ""

    text_content = norm.textdaten.text.content
    if not text_content or not text_content.elements:
        return ""

    # Find all P elements
    p_elements = [elem for elem in text_content.elements if isinstance(elem, P)]

    if not p_elements:
        # Fallback to raw text
        if text_content.raw_text:
            return text_content.raw_text
        return ""

    # Get paragraph number from norm metadata
    paragraph_num = ""
    if norm.metadaten and norm.metadaten.enbez:
        paragraph_num = norm.metadaten.enbez.replace("§", "").strip()

    all_lines = []

    for idx, p in enumerate(p_elements):
        # Add spacing between Absätze (but not before the first one)
        if idx > 0:
            all_lines.append("")

        # Get absatz number from P element (extracted during parsing)
        absatz_num = p.absatz_num
        text = p.raw_text or ""

        # Build reference
        if absatz_num:
            paragraph_ref = f"{law_code} {paragraph_num} Absatz {absatz_num}"
        else:
            paragraph_ref = f"{law_code} {paragraph_num}"

        # Check for DL lists
        dl_lists = [elem for elem in p.content if isinstance(elem, DL)]

        if not dl_lists:
            # Simple text without lists
            if absatz_num:
                # Add Absatz header on same line as text if text is short
                # Remove (1), (2) etc. prefix from text since we already have absatz_num
                text_clean = text
                if text.startswith(f"({absatz_num})"):
                    text_clean = text[len(f"({absatz_num})") :].strip()
                all_lines.append(
                    f"({absatz_num}) {text_clean}" if text_clean else f"({absatz_num})"
                )
            elif text:
                all_lines.append(text)
        else:
            # With lists - use format_p_element
            # Extract intro text for Absatz header
            intro_parts = []
            for elem in p.content:
                if isinstance(elem, DL):
                    break
                if isinstance(elem, str):
                    intro_parts.append(elem)

            intro_text = " ".join(intro_parts).strip()
            # Remove (1), (2) etc. prefix from intro_text since we already have absatz_num
            if absatz_num and intro_text.startswith(f"({absatz_num})"):
                intro_text = intro_text[len(f"({absatz_num})") :].strip()

            # Add Absatz header with intro text
            if absatz_num and intro_text:
                all_lines.append(f"({absatz_num}) {intro_text}")
            elif absatz_num:
                all_lines.append(f"({absatz_num})")
            elif intro_text:
                all_lines.append(intro_text)

            # Process all DL lists
            for dl in dl_lists:
                all_lines.extend(
                    process_dl_list(dl, indent_level=0, parent_ref=paragraph_ref)
                )

    return "\n".join(all_lines)
