"""
Utility functions for German law documents.

Provides common functionality for:
- Law mapping (load/save/find)
- Text extraction from XML elements
- TOC index management
- Law download and extraction
"""

import json
import logging
import re
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Optional

# Conditional import for type hints
if sys.version_info >= (3, 11):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from .models import LawReference, Norm, P

if TYPE_CHECKING:
    from .models import Dokumente

logger = logging.getLogger(__name__)

# Constants
GII_TOC_URL = "https://www.gesetze-im-internet.de/gii-toc.xml"


# ============================================================================
# Law Reference Parser
# ============================================================================


def parse_law_reference(reference: str) -> LawReference | None:
    """
    Parse a law reference string into its components.

    Supports various formats:
    - "§ 52 Absatz 1 Satz 1"
    - "§ 8b Absatz 2"
    - "§ 1"
    - "Artikel 20 Absatz 3"
    - "Art. 1 Abs. 2 Satz 3"
    - "§ 10 Absatz 1 Nummer 4 Buchstabe a" (with number and letter)
    - "Artikel 34 Absatz 6 Buchstaben a und b" (plural Buchstaben)
    - "BGB § 26 Absatz 4" (with law code)
    - "GmbHG § 13 Absatz 2" (with law code)

    Args:
        reference: Law reference string

    Returns:
        Parsed reference with law, paragraph, section, number, letter, and sentence or None if invalid

    Examples:
        >>> parse_law_reference("§ 52 Absatz 1 Satz 1")
        {'law': None, 'paragraph': '52', 'section': '1', 'number': None, 'letter': None, 'sentence': '1'}
        >>> parse_law_reference("BGB § 26 Absatz 4")
        {'law': 'BGB', 'paragraph': '26', 'section': '4', 'number': None, 'letter': None, 'sentence': None}
        >>> parse_law_reference("§ 10 Absatz 1 Nummer 4 Buchstabe a")
        {'law': None, 'paragraph': '10', 'section': '1', 'number': '4', 'letter': 'a', 'sentence': None}
    """
    # Pattern to match various reference formats
    # Matches: Optional law code, § or Artikel/Art., paragraph number, optional Absatz, Nummer, Buchstabe, Satz
    pattern = r"""
        (?:([A-Z][A-Za-z]*[A-Z]|[A-Z]{2,})\s+)?  # Optional law code (e.g., BGB, GmbHG, KStG)
        (?:§|Artikel|Art\.?)\s*                  # Paragraph marker
        (\d+[a-z]?)                               # Paragraph number (e.g., 52, 8b)
        (?:\s+(?:Absatz|Abs\.?)\s+(\d+))?         # Optional section (Absatz)
        (?:\s+(?:Nummer|Nr\.?)\s+(\d+))?          # Optional number (Nummer)
        (?:\s+Buchstabe[n]?\s+([a-z]))?           # Optional letter (Buchstabe/Buchstaben)
        (?:\s+Satz\s+(\d+))?                      # Optional sentence (Satz)
    """

    match = re.search(pattern, reference, re.VERBOSE | re.IGNORECASE)

    if not match:
        return None

    result: LawReference = {
        "law": match.group(1) if match.group(1) else None,
        "paragraph": match.group(2),
        "section": match.group(3) if match.group(3) else None,
        "number": match.group(4) if match.group(4) else None,
        "letter": match.group(5) if match.group(5) else None,
        "sentence": match.group(6) if match.group(6) else None,
    }

    return result


class LawMapping(TypedDict):
    """Law mapping entry structure."""

    filename: str
    title: str
    category: str
    builddate: str
    url_path: str


class TOCEntry(TypedDict):
    """Table of contents entry structure."""

    title: str
    url: str
    url_path: str
    category: str


class DownloadResult(TypedDict):
    """Result of batch download operation."""

    downloaded: int
    failed: int
    skipped: int


# ============================================================================
# Law Mapping Functions
# ============================================================================


def load_law_mapping(base_path: Optional[Path] = None) -> dict[str, LawMapping]:
    """
    Load law mapping from law_mapping.json.

    Args:
        base_path: Base directory containing law_mapping.json (default: project root)

    Returns:
        Dictionary mapping law codes (jurabk) to law info
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent

    mapping_file = base_path / "law_mapping.json"

    if not mapping_file.exists():
        logger.warning(f"Law mapping file not found: {mapping_file}")
        return {}

    try:
        with open(mapping_file, encoding="utf-8") as f:
            mapping: dict[str, LawMapping] = json.load(f)
        logger.debug(f"Loaded {len(mapping)} laws from {mapping_file}")
        return mapping
    except Exception as e:
        logger.error(f"Error loading law_mapping.json: {e}")
        return {}


def save_law_mapping(
    mapping: dict[str, LawMapping], base_path: Optional[Path] = None
) -> bool:
    """
    Save law mapping to law_mapping.json.

    Args:
        mapping: Dictionary mapping law codes to law info
        base_path: Base directory for law_mapping.json (default: project root)

    Returns:
        True if successful, False otherwise
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent

    mapping_file = base_path / "law_mapping.json"

    try:
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2, sort_keys=True)
        logger.info(f"Saved mapping with {len(mapping)} laws to {mapping_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving law_mapping.json: {e}")
        return False


def find_law_in_mapping(law_code: str, mapping: dict[str, LawMapping]) -> Optional[str]:
    """
    Find a law key in mapping (case-insensitive with fallbacks).

    Args:
        law_code: Law code to search for (e.g., "HGB", "KStG")
        mapping: Law mapping dictionary

    Returns:
        Matching law key or None if not found
    """
    # Try exact match first
    if law_code in mapping:
        return law_code

    # Try case-insensitive exact match
    law_upper = law_code.upper()
    for key in mapping:
        if key.upper() == law_upper:
            return key

    # Try match at start of key with delimiter (e.g., "KStG" matches "KStG 1977")
    for key in mapping:
        key_upper = key.upper()
        if key_upper.startswith(law_upper + " ") or key_upper.startswith(
            law_upper + "_"
        ):
            return key

    # Fallback: word boundary match (only at start)
    for key in mapping:
        if key.upper().startswith(law_upper):
            return key

    return None


# ============================================================================
# Text Extraction Functions
# ============================================================================


def extract_text_from_p(p: P) -> str:
    """
    Extract clean text from a P (paragraph) element.

    Args:
        p: P element from XML

    Returns:
        Extracted text as string
    """
    if p.raw_text:
        return p.raw_text

    # Fallback: reconstruct from content
    parts = []
    for elem in p.content:
        if isinstance(elem, str):
            parts.append(elem)
        elif hasattr(elem, "text") and elem.text:
            parts.append(elem.text)

    return " ".join(parts).strip()


def extract_text_from_norm(norm: Norm) -> str:
    """
    Extract full text content from a norm.

    Args:
        norm: Norm object

    Returns:
        Complete text content as string
    """
    if not norm.textdaten or not norm.textdaten.text:
        return ""

    text_content = norm.textdaten.text
    if not text_content.content:
        return ""

    # Use raw_text if available (performance optimization)
    if text_content.content.raw_text:
        return text_content.content.raw_text

    # Otherwise reconstruct from content elements
    parts = []
    for item in text_content.content.elements:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, P):
            parts.append(extract_text_from_p(item))
        elif hasattr(item, "raw_text") and item.raw_text:
            parts.append(item.raw_text)

    return "\n".join(parts)


# ============================================================================
# TOC (Table of Contents) Functions
# ============================================================================


def download_toc(base_path: Optional[Path] = None) -> bool:
    """
    Download gii-toc.xml from gesetze-im-internet.de.

    Args:
        base_path: Base directory to save gii-toc.xml (default: project root)

    Returns:
        True if successful, False otherwise
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent

    toc_path = base_path / "gii-toc.xml"

    try:
        logger.info(f"Downloading gii-toc.xml from {GII_TOC_URL}")
        urllib.request.urlretrieve(GII_TOC_URL, toc_path)
        logger.info(f"Successfully downloaded gii-toc.xml to {toc_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading gii-toc.xml: {e}")
        return False


def extract_category_from_title(title: str) -> str:
    """
    Extract the legal category from a document title.

    Categories: Gesetz, Verordnung, Anordnung, Bekanntmachung, Abkommen, etc.

    Args:
        title: Full title of the legal document

    Returns:
        Category string or "Sonstiges" if no category found
    """
    categories = [
        ("Abkommen", r"(abkommen|übereinkommen|konvention|vertrag)\b"),
        ("Verordnung", r"verordnung\b"),
        ("Bekanntmachung", r"bekanntmachung\b"),
        ("Gesetz", r"(gesetz|gesetzbuch)\b"),
    ]

    for category, pattern in categories:
        if re.search(pattern, title, re.IGNORECASE):
            return category

    return "Sonstiges"


def load_toc_index(base_path: Optional[Path] = None) -> dict[str, TOCEntry]:
    """
    Parse gii-toc.xml and create an index of all available laws.
    Downloads gii-toc.xml if not present.

    Args:
        base_path: Base directory containing gii-toc.xml (default: project root)

    Returns:
        Dictionary mapping title to TOC entry
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent

    toc_path = base_path / "gii-toc.xml"

    # Download if not present
    if not toc_path.exists():
        logger.info("gii-toc.xml not found, downloading...")
        if not download_toc(base_path):
            return {}

    try:
        tree = ET.parse(toc_path)
        root = tree.getroot()

        index: dict[str, TOCEntry] = {}
        for item in root.findall("item"):
            title_elem = item.find("title")
            link_elem = item.find("link")

            if (
                title_elem is not None
                and link_elem is not None
                and title_elem.text
                and link_elem.text
            ):
                title = title_elem.text
                url = link_elem.text

                # Extract url_path (e.g., "hgb" from "https://www.gesetze-im-internet.de/hgb/xml.zip")
                url_path = url.split("/")[-2] if "/" in url else ""

                # Extract category from title
                category = extract_category_from_title(title)

                index[title] = {
                    "title": title,
                    "url": url,
                    "url_path": url_path,
                    "category": category,
                }

        logger.info(f"Loaded {len(index)} laws from gii-toc.xml")
        return index

    except Exception as e:
        logger.error(f"Error parsing gii-toc.xml: {e}")
        return {}


def find_law_in_toc(
    law_code: str, toc_index: dict[str, TOCEntry]
) -> Optional[TOCEntry]:
    """
    Find a law in the TOC index by searching for the law code.

    Args:
        law_code: Law code to search for (e.g., "HGB", "KSTG")
        toc_index: TOC index dictionary

    Returns:
        TOC entry or None if not found
    """
    law_lower = law_code.lower()

    # Try exact match in URL path first (most reliable)
    for title, entry in toc_index.items():
        if entry["url_path"].lower() == law_lower:
            return entry

    # Try exact match at start of URL path
    for title, entry in toc_index.items():
        if entry["url_path"].lower().startswith(law_lower + "_"):
            return entry

    # Try partial match in URL path
    for title, entry in toc_index.items():
        if law_lower in entry["url_path"].lower():
            return entry

    # Finally try matching in title
    law_upper = law_code.upper()
    for title, entry in toc_index.items():
        if law_upper in title.upper():
            return entry

    return None


# ============================================================================
# XML Extraction Functions
# ============================================================================


def extract_jurabk_from_xml(xml_path: Path) -> Optional[str]:
    """
    Extract the jurabk (legal abbreviation) from a law XML file.

    Args:
        xml_path: Path to the XML file

    Returns:
        The jurabk string or None if not found
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        jurabk_elem = root.find(".//jurabk")
        if jurabk_elem is not None and jurabk_elem.text:
            return jurabk_elem.text.strip()

        logger.warning(f"No <jurabk> found in {xml_path}")
        return None

    except Exception as e:
        logger.error(f"Error extracting jurabk from {xml_path}: {e}")
        return None


def extract_builddate_from_xml(xml_path: Path) -> Optional[str]:
    """
    Extract the builddate from a law XML file.

    Args:
        xml_path: Path to the XML file

    Returns:
        The builddate string (format: YYYYMMDDHHMMSS) or None if not found
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        builddate = root.get("builddate")
        if builddate:
            return builddate.strip()

        logger.warning(f"No builddate attribute found in {xml_path}")
        return None

    except Exception as e:
        logger.error(f"Error extracting builddate from {xml_path}: {e}")
        return None


# ============================================================================
# Law Loading Functions
# ============================================================================


def get_law(
    law_code: str,
    base_path: Optional[Path] = None,
    auto_download: bool = False,
) -> Optional["Dokumente"]:
    """
    Load and parse a law document.

    Args:
        law_code: Law code (e.g., 'HGB', 'KStG', 'BGB')
        base_path: Base directory containing law_mapping.json and data/ (default: project root)
        auto_download: Automatically download if not found locally (default: False)

    Returns:
        Parsed Dokumente object or None if not found

    Examples:
        >>> get_law('HGB')
        <Dokumente: Handelsgesetzbuch>

        >>> get_law('KStG')
        <Dokumente: Körperschaftsteuergesetz>
    """
    from .parser import parse_gesetz

    if base_path is None:
        base_path = Path(__file__).parent.parent

    # Load mapping and find law
    mapping = load_law_mapping(base_path)
    if not mapping:
        logger.warning("No law mapping found")
        return None

    law_key = find_law_in_mapping(law_code, mapping)

    # If not found in mapping, try to download
    if not law_key and auto_download:
        logger.info(f"Law '{law_code}' not in mapping, attempting download...")
        toc_index = load_toc_index(base_path)
        toc_entry = find_law_in_toc(law_code, toc_index)

        if toc_entry:
            logger.info(f"Found '{law_code}' in TOC: {toc_entry['title']}")
            target_dir = base_path / "data"
            result = download_and_extract_law(toc_entry["url"], target_dir)

            if result:
                xml_path, jurabk = result
                builddate = extract_builddate_from_xml(xml_path)

                # Update mapping
                mapping[jurabk] = {
                    "filename": xml_path.name,
                    "title": toc_entry["title"],
                    "category": toc_entry.get("category", ""),
                    "builddate": builddate or "",
                    "url_path": toc_entry.get("url_path", ""),
                }
                save_law_mapping(mapping, base_path)
                law_key = jurabk
                logger.info(f"Successfully downloaded and added '{jurabk}' to mapping")
            else:
                logger.error(f"Failed to download '{law_code}'")
                return None
        else:
            logger.warning(f"Law '{law_code}' not found in TOC")
            return None

    if not law_key:
        logger.warning(f"Law '{law_code}' not found")
        return None

    # Get XML path from mapping
    law_info = mapping[law_key]
    xml_path = base_path / "data" / law_info["filename"]

    if not xml_path.exists():
        logger.error(f"XML file not found: {xml_path}")
        return None

    # Parse and return
    try:
        return parse_gesetz(xml_path)
    except Exception as e:
        logger.error(f"Error parsing {xml_path}: {e}")
        return None


# ============================================================================
# Download Functions
# ============================================================================


def download_and_extract_law(url: str, target_dir: Path) -> Optional[tuple[Path, str]]:
    """
    Download a law ZIP file, extract the XML, and determine its jurabk.

    Args:
        url: URL to the law ZIP file
        target_dir: Directory where to save the extracted XML

    Returns:
        Tuple of (xml_path, jurabk) or None if failed
    """
    try:
        logger.info(f"Downloading law from {url}")

        # Download ZIP to temporary file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            urllib.request.urlretrieve(url, tmp_file.name)
            tmp_path = Path(tmp_file.name)

        # Extract XML from ZIP
        with zipfile.ZipFile(tmp_path, "r") as zip_ref:
            xml_files = [f for f in zip_ref.namelist() if f.endswith(".xml")]

            if not xml_files:
                logger.error(f"No XML file found in {url}")
                tmp_path.unlink()
                return None

            xml_filename = xml_files[0]

            # Extract to temporary location first
            with tempfile.TemporaryDirectory() as temp_extract_dir:
                zip_ref.extract(xml_filename, temp_extract_dir)
                temp_xml_path = Path(temp_extract_dir) / xml_filename

                # Extract jurabk to determine final filename
                jurabk = extract_jurabk_from_xml(temp_xml_path)

                if not jurabk:
                    logger.error(f"Could not extract jurabk from {url}")
                    tmp_path.unlink()
                    return None

                # Use original filename
                final_xml_path = target_dir / xml_filename

                # Copy to final location
                target_dir.mkdir(parents=True, exist_ok=True)
                with (
                    open(temp_xml_path, "rb") as src,
                    open(final_xml_path, "wb") as dst,
                ):
                    dst.write(src.read())

        # Clean up temporary ZIP file
        tmp_path.unlink()

        logger.info(
            f"Successfully downloaded and extracted {jurabk} to {final_xml_path}"
        )
        return (final_xml_path, jurabk)

    except Exception as e:
        logger.error(f"Error downloading law from {url}: {e}")
        return None


def download_laws_batch(
    toc_entries: list[tuple[str, TOCEntry]],
    target_dir: Path,
    max_downloads: int = 0,
    skip_existing: bool = True,
    save_interval: int = 10,
    base_path: Optional[Path] = None,
) -> DownloadResult:
    """
    Batch download laws and update mapping file.

    Args:
        toc_entries: List of (title, toc_entry) tuples to download
        target_dir: Directory where to save downloaded laws
        max_downloads: Maximum number to download (0 = unlimited)
        skip_existing: Skip laws that already exist locally
        save_interval: Save mapping every N downloads
        base_path: Base directory for law_mapping.json (default: project root)

    Returns:
        Download statistics
    """
    import time

    if base_path is None:
        base_path = Path(__file__).parent.parent

    mapping = load_law_mapping(base_path)
    downloaded = 0
    failed = 0
    skipped = 0

    start_time = time.time()

    for idx, (title, entry) in enumerate(toc_entries, 1):
        # Check download limit
        if max_downloads > 0 and downloaded >= max_downloads:
            logger.info(f"Reached download limit of {max_downloads}")
            break

        # Skip if exists
        if skip_existing:
            for jurabk, law_info in mapping.items():
                if law_info.get("url_path", "").lower() == entry["url_path"].lower():
                    xml_path = target_dir / law_info["filename"]
                    if xml_path.exists():
                        skipped += 1
                        break
            else:
                pass

            if skipped > 0 and idx == skipped:
                continue

        # Download
        logger.info(f"Downloading {idx}/{len(toc_entries)}: {title[:60]}...")
        result = download_and_extract_law(entry["url"], target_dir)

        if result:
            xml_path, jurabk = result
            builddate = extract_builddate_from_xml(xml_path)

            mapping[jurabk] = {
                "filename": xml_path.name,
                "title": title,
                "category": entry.get("category", ""),
                "builddate": builddate or "",
                "url_path": entry.get("url_path", ""),
            }
            downloaded += 1

            # Save periodically
            if downloaded % save_interval == 0:
                save_law_mapping(mapping, base_path)
                elapsed = time.time() - start_time
                rate = downloaded / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Progress: {idx}/{len(toc_entries)} - Rate: {rate:.2f} laws/sec"
                )
        else:
            failed += 1
            logger.warning(f"Failed to download: {title}")

    # Save final mapping
    save_law_mapping(mapping, base_path)

    return {
        "downloaded": downloaded,
        "failed": failed,
        "skipped": skipped,
    }
