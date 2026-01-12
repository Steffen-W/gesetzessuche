"""
Search and query functionality for German law documents.

Provides the LawSearch class for:
- Finding specific paragraphs and sections
- Full-text search across law content
- Listing all paragraphs
- Displaying law information
"""

from .models import Dokumente, Norm, P, SearchResult
from .utils import extract_text_from_norm, extract_text_from_p, parse_law_reference


class LawSearch:
    """Search and query German law documents."""

    def __init__(self, documents: Dokumente, law_code: str):
        """
        Initialize search for a law document.

        Args:
            documents: Parsed law document
            law_code: Short code for the law (e.g., 'AktG', 'BGB')
        """
        self.documents = documents
        self.law_code = law_code

    def _format_paragraph(self, norm: Norm, show_full_text: bool = True) -> str:
        """
        Format a paragraph for display.

        Args:
            norm: The norm to format
            show_full_text: Whether to include full text content

        Returns:
            Formatted paragraph string
        """
        if not norm.metadaten:
            return ""

        result = []

        # Header
        enbez = norm.metadaten.enbez or "?"
        result.append(f"{'=' * 70}")
        result.append(f"{self.law_code} {enbez}")

        if norm.metadaten.titel:
            result.append(f"{norm.metadaten.titel}")

        result.append(f"{'=' * 70}")

        if show_full_text:
            text = extract_text_from_norm(norm)
            if text:
                result.append("")
                result.append(text)

        return "\n".join(result)

    def find_paragraph(self, paragraph_num: str) -> str | None:
        """
        Find a specific paragraph by number.

        Args:
            paragraph_num: Paragraph number (e.g., '1', '8b')

        Returns:
            Formatted paragraph text or None if not found
        """
        paragraph_num = paragraph_num.replace("§", "").strip()

        paragraphs = self.documents.get_paragraphen()
        for norm in paragraphs:
            if not norm.metadaten or not norm.metadaten.enbez:
                continue

            current_para = norm.metadaten.enbez.replace("§", "").strip()
            if current_para == paragraph_num:
                return self._format_paragraph(norm)

        return None

    def find_paragraph_section(
        self, paragraph_num: str, section_num: str
    ) -> str | None:
        """
        Find a specific section (Absatz) in a paragraph.

        Args:
            paragraph_num: Paragraph number (e.g., '1', '8b')
            section_num: Section number (e.g., '1', '2')

        Returns:
            Formatted section text or None if not found
        """
        paragraph_num = paragraph_num.replace("§", "").strip()

        paragraphs = self.documents.get_paragraphen()
        for norm in paragraphs:
            if not norm.metadaten or not norm.metadaten.enbez:
                continue

            current_para = norm.metadaten.enbez.replace("§", "").strip()
            if current_para == paragraph_num:
                return self._find_section_in_norm(norm, section_num)

        return None

    def _find_section_in_norm(self, norm: Norm, section_num: str) -> str | None:
        """
        Find a section within a norm.

        Args:
            norm: The norm to search in
            section_num: Section number

        Returns:
            Formatted section text or None if not found
        """
        if not norm.textdaten or not norm.textdaten.text:
            return None

        text_content = norm.textdaten.text.content
        if not text_content or not text_content.elements:
            return None

        # Look through content for section
        section_count = 0
        target_section = int(section_num)

        for item in text_content.elements:
            if isinstance(item, P):
                section_count += 1
                if section_count == target_section:
                    enbez = norm.metadaten.enbez if norm.metadaten else "?"
                    result = [
                        "=" * 70,
                        f"{self.law_code} {enbez} Absatz {section_num}",
                        "=" * 70,
                        "",
                        extract_text_from_p(item),
                    ]
                    return "\n".join(result)

        return None

    def search_term(
        self, term: str, case_sensitive: bool = False
    ) -> list[SearchResult]:
        """
        Search for a term in all paragraphs.

        Args:
            term: Term to search for
            case_sensitive: Whether to perform case-sensitive search

        Returns:
            List of search results with context
        """
        results: list[SearchResult] = []
        search_term = term if case_sensitive else term.lower()

        for norm in self.documents.get_paragraphen():
            if not norm.metadaten or not norm.metadaten.enbez:
                continue

            text = extract_text_from_norm(norm)
            if not text:
                continue

            compare_text = text if case_sensitive else text.lower()

            if search_term in compare_text:
                # Extract context around match
                idx = compare_text.find(search_term)
                start = max(0, idx - 100)
                end = min(len(text), idx + len(term) + 100)
                context = text[start:end]

                if start > 0:
                    context = "..." + context
                if end < len(text):
                    context = context + "..."

                results.append(
                    {
                        "paragraph": norm.metadaten.enbez,
                        "title": norm.metadaten.titel or "",
                        "context": context,
                    }
                )

        return results

    def list_all_paragraphs(self) -> list[dict[str, str]]:
        """
        List all paragraphs with their titles.

        Returns:
            List of dictionaries with 'number' and 'title' keys
        """
        result = []
        for norm in self.documents.get_paragraphen():
            if norm.metadaten and norm.metadaten.enbez:
                result.append(
                    {
                        "number": norm.metadaten.enbez,
                        "title": norm.metadaten.titel or "",
                    }
                )
        return result

    def get_by_reference(self, reference: str) -> str | None:
        """
        Get law text by parsing a reference string.

        Supports various formats:
        - "§ 52 Absatz 1 Satz 1" (full reference with sentence)
        - "§ 8b Absatz 2" (paragraph with section)
        - "§ 1" (paragraph only)
        - "Artikel 20 Absatz 3"
        - "Art. 1 Abs. 2"

        Args:
            reference: Law reference string (e.g., "§ 52 Absatz 1 Satz 1")

        Returns:
            Formatted text or None if not found

        Examples:
            >>> search = LawSearch(documents, "BGB")
            >>> text = search.get_by_reference("§ 1")
            >>> text = search.get_by_reference("§ 8b Absatz 2")
        """
        parsed = parse_law_reference(reference)

        if not parsed:
            return None

        # For complex references (with Nummer, Buchstabe, or Satz),
        # show the entire section instead of trying to extract parts
        # This preserves context and shows the actual structure from the norm
        if parsed["number"] or parsed["letter"] or parsed["sentence"]:
            # Show the section with a note about what was searched for
            if parsed["section"]:
                result = self.find_paragraph_section(
                    parsed["paragraph"], parsed["section"]
                )
                if result:
                    # Add a note about the specific reference
                    note_parts = []
                    if parsed["number"]:
                        note_parts.append(f"Nummer {parsed['number']}")
                    if parsed["letter"]:
                        note_parts.append(f"Buchstabe {parsed['letter']}")
                    if parsed["sentence"]:
                        note_parts.append(f"Satz {parsed['sentence']}")

                    if note_parts:
                        note = f"(Gesucht: {' '.join(note_parts)})"
                        # Insert note after header
                        lines = result.split("\n")
                        lines.insert(3, note)
                        return "\n".join(lines)
                return result
            else:
                # No section specified, show entire paragraph
                return self.find_paragraph(parsed["paragraph"])

        # If we have section but no complex parts, use find_paragraph_section
        if parsed["section"]:
            return self.find_paragraph_section(parsed["paragraph"], parsed["section"])

        # Otherwise just get the paragraph
        return self.find_paragraph(parsed["paragraph"])

    def show_info(self) -> str:
        """
        Show law information.

        Returns:
            Formatted law information string
        """
        result = []
        result.append("=" * 70)
        result.append(f"{self.law_code}: {self.documents.get_titel() or 'Unknown'}")
        result.append("=" * 70)
        result.append(f"Abbreviations: {', '.join(self.documents.get_jurabk())}")
        result.append(f"Total norms:   {len(self.documents.normen)}")
        result.append(f"Paragraphs:    {len(self.documents.get_paragraphen())}")
        result.append(f"Structure:     {len(self.documents.get_gliederung())} elements")
        result.append("")
        result.append("First 5 paragraphs:")
        for norm in self.documents.get_paragraphen()[:5]:
            if norm.metadaten and norm.metadaten.enbez:
                title = norm.metadaten.titel or ""
                result.append(f"  {norm.metadaten.enbez:15} {title[:50]}")

        return "\n".join(result)
