#!/usr/bin/env python3
"""
Modern XML to Markdown converter using the new Pydantic-based parser
Much more compact than the old ElementTree-based version
"""

import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gesetzessuche import parse_gesetz, Dokumente, Norm, P, DL, ContentElement


class MarkdownConverter:
    """Converts parsed law documents to Markdown"""

    def __init__(self, dokumente: Dokumente, gesetz_kuerzel: str):
        self.dokumente = dokumente
        self.gesetz_kuerzel = gesetz_kuerzel
        self.output: List[str] = []

    def _extract_text(self, elements: List[ContentElement]) -> str:
        """Recursively extract text from content elements"""
        parts = []
        for elem in elements:
            if isinstance(elem, str):
                parts.append(elem)
            elif isinstance(elem, P):
                # Recursively extract from P elements
                if elem.raw_text:
                    parts.append(elem.raw_text)
                elif elem.content:
                    parts.append(self._extract_text(elem.content))
            elif isinstance(elem, DL):
                # Skip DL in text extraction - handled separately
                continue
            elif hasattr(elem, "text") and elem.text:
                parts.append(elem.text)
            elif hasattr(elem, "content") and elem.content:
                parts.append(self._extract_text(elem.content))
            elif hasattr(elem, "children") and elem.children:
                parts.append(self._extract_text(elem.children))

        return " ".join(parts).strip()

    def _process_dl_list(
        self, dl: DL, indent_level: int = 0, parent_ref: str | None = None
    ) -> None:
        """Process a definition list recursively"""
        indent = "  " * indent_level

        for item in dl.items:
            dt_text = item.dt.text or ""

            # Build reference
            if parent_ref and indent_level == 0:
                item_ref = f"{parent_ref} Nummer {dt_text}"
            elif parent_ref and indent_level == 1:
                item_ref = f"{parent_ref} Buchstabe {dt_text}"
            else:
                item_ref = None

            # Extract DD content
            if item.dd.la:
                # Check for nested DL
                nested_dls = []
                if item.dd.la.children:
                    nested_dls = [
                        child for child in item.dd.la.children if isinstance(child, DL)
                    ]

                if not nested_dls:
                    # Simple text
                    text = item.dd.la.text or self._extract_text(item.dd.la.children)
                    if text and item_ref:
                        self.output.append(f"{indent}**{item_ref}** {text}")
                    elif text:
                        self.output.append(f"{indent}{dt_text}. {text}")
                else:
                    # With nested list
                    intro_text = item.dd.la.text or ""
                    if intro_text and item_ref:
                        self.output.append(f"{indent}**{item_ref}** {intro_text}")
                    elif intro_text:
                        self.output.append(f"{indent}{dt_text}. {intro_text}")
                    elif item_ref:
                        self.output.append(f"{indent}**{item_ref}**")
                    else:
                        self.output.append(f"{indent}{dt_text}.")

                    # Process nested lists
                    for nested_dl in nested_dls:
                        self._process_dl_list(nested_dl, indent_level + 1, item_ref)

    def _process_paragraph_content(self, p: P, paragraph_num: str) -> None:
        """Process a paragraph element"""
        # Extract absatz number if present
        text = p.raw_text or ""
        absatz_match = text[:10].strip() if text else ""
        absatz_num = None

        if absatz_match.startswith("(") and ")" in absatz_match[:5]:
            absatz_num = absatz_match[1 : absatz_match.index(")")]

        # Build reference
        if absatz_num:
            paragraph_ref = (
                f"**{self.gesetz_kuerzel} {paragraph_num} Absatz {absatz_num}**"
            )
            paragraph_ref_plain = (
                f"{self.gesetz_kuerzel} {paragraph_num} Absatz {absatz_num}"
            )
            # Remove (1), (2) etc. from text
            text = text[text.index(")") + 1 :].strip() if ")" in text[:10] else text
        else:
            paragraph_ref = f"**{self.gesetz_kuerzel} {paragraph_num}**"
            paragraph_ref_plain = f"{self.gesetz_kuerzel} {paragraph_num}"

        # Check for DL lists in content
        dl_lists = [elem for elem in p.content if isinstance(elem, DL)]

        if not dl_lists:
            # Simple text
            if text:
                self.output.append(f"{paragraph_ref} {text}")
        else:
            # Extract text before first DL
            intro_parts = []
            for elem in p.content:
                if isinstance(elem, DL):
                    break
                if isinstance(elem, str):
                    intro_parts.append(elem)

            intro_text = " ".join(intro_parts).strip()
            # Remove (1), (2) if present
            if absatz_num and intro_text.startswith(f"({absatz_num})"):
                intro_text = intro_text[intro_text.index(")") + 1 :].strip()

            if intro_text:
                self.output.append(f"{paragraph_ref} {intro_text}")
            else:
                self.output.append(f"{paragraph_ref}")

            # Process all DL lists
            for dl in dl_lists:
                self._process_dl_list(
                    dl, indent_level=0, parent_ref=paragraph_ref_plain
                )

    def _process_norm(self, norm: Norm) -> None:
        """Process a single norm (paragraph or structure element)"""
        if not norm.metadaten:
            return

        # Handle Gliederungseinheit (structure elements)
        if norm.metadaten.gliederungseinheit:
            g = norm.metadaten.gliederungseinheit
            bez = g.gliederungsbez or ""
            titel = g.gliederungstitel or ""

            if bez and titel:
                # Determine heading level
                if "Buch" in bez or "Teil" in bez:
                    self.output.append(f"\n# {bez}: {titel}\n")
                elif "Abschnitt" in bez or "Kapitel" in bez:
                    self.output.append(f"\n## {bez}: {titel}\n")
                else:
                    self.output.append(f"\n### {bez}: {titel}\n")
            return

        # Handle paragraphs
        enbez = norm.metadaten.enbez
        if not enbez or not norm.textdaten:
            return

        paragraph_num = enbez.replace("§", "").strip()
        titel_text = norm.metadaten.titel or ""

        # Heading
        if titel_text:
            self.output.append(f"\n## {enbez} - {titel_text}\n")
        else:
            self.output.append(f"\n## {enbez}\n")

        # Process text content
        if norm.textdaten.text and norm.textdaten.text.content:
            content = norm.textdaten.text.content

            # Find all P elements
            p_elements = [elem for elem in content.elements if isinstance(elem, P)]

            if p_elements:
                for p in p_elements:
                    self._process_paragraph_content(p, paragraph_num)
            else:
                # Fallback: use raw text
                if content.raw_text:
                    ref = f"**{self.gesetz_kuerzel} {paragraph_num}**"
                    self.output.append(f"{ref} {content.raw_text}\n")

    def convert(self) -> str:
        """Convert the document to Markdown"""
        # Title and metadata
        titel = self.dokumente.get_titel()
        if titel:
            self.output.append(f"# {titel}\n")
            self.output.append("")

        # Stand information
        if self.dokumente.normen and self.dokumente.normen[0].metadaten:
            first_meta = self.dokumente.normen[0].metadaten
            if first_meta.standangabe:
                for stand in first_meta.standangabe:
                    if stand.standkommentar:
                        self.output.append(f"*{stand.standkommentar}*\n")
                        self.output.append("")
                        break

        # Process all norms
        for norm in self.dokumente.normen:
            self._process_norm(norm)

        return "\n".join(self.output)

    def save_markdown(self, output_path: Path) -> Path:
        """Save the Markdown to a file"""
        markdown_content = self.convert()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"✓ Successfully converted: {output_path.name}")
        return output_path


def main() -> None:
    """Main function"""
    example_dir = Path(__file__).parent.parent / "example"

    gesetze = [
        ("Handelsgesetzbuch.xml", "HGB §", "Handelsgesetzbuch_v2.md"),
        ("Körperschaftsteuergesetz.xml", "KStG §", "Körperschaftsteuergesetz_v2.md"),
        ("Abgabenordnung.xml", "AO §", "Abgabenordnung_v2.md"),
        ("Bürgerliches_Gesetzbuch.xml", "BGB §", "Bürgerliches_Gesetzbuch_v2.md"),
        ("Gewerbesteuergesetz.xml", "GewStG §", "Gewerbesteuergesetz_v2.md"),
        ("Umsatzsteuergesetz.xml", "UStG §", "Umsatzsteuergesetz_v2.md"),
    ]

    print("Converting laws from XML to Markdown using new parser...\n")

    for xml_file, kuerzel, md_file in gesetze:
        xml_path = example_dir / xml_file
        if xml_path.exists():
            # Parse using new parser
            dokumente = parse_gesetz(xml_path)

            # Convert to Markdown
            converter = MarkdownConverter(dokumente, kuerzel)
            converter.save_markdown(example_dir / md_file)
        else:
            print(f"⚠ Skipped: {xml_file} not found")

    print("\n✓ Conversion complete!")


if __name__ == "__main__":
    main()
