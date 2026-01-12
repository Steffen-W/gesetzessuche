#!/usr/bin/env python3
"""
Script to download all laws from gesetze-im-internet.de and create a mapping file.
"""

import logging
from pathlib import Path

# Relative imports since we're inside the package
from .utils import download_laws_batch, load_toc_index

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_all_laws(skip_existing: bool = True) -> dict[str, int | str]:
    """Download all laws and create mapping file."""
    # base_path is the project root (parent of gesetzessuche package)
    base_path = Path(__file__).parent.parent
    toc_index = load_toc_index(base_path)
    target_dir = base_path / "data"
    toc_entries = list(toc_index.items())

    logger.info("Starting download of all laws")

    result = download_laws_batch(
        toc_entries=toc_entries,
        target_dir=target_dir,
        max_downloads=0,
        skip_existing=skip_existing,
        base_path=base_path,
    )

    logger.info("\n=== Download Complete ===")
    logger.info(f"Downloaded: {result['downloaded']}")
    logger.info(f"Failed: {result['failed']}")
    logger.info(f"Skipped: {result['skipped']}")

    return {
        "downloaded": result["downloaded"],
        "failed": result["failed"],
        "skipped": result["skipped"],
        "mapping_file": str(base_path / "law_mapping.json"),
    }


def download_essential_laws() -> dict[str, int | str]:
    """
    Download a curated set of essential German laws.

    Returns:
        Dictionary with download statistics
    """
    # Essential laws url_paths
    essential_url_paths = [
        "agg",
        "aktg",
        "ao_1977",
        "arbzg",
        "bbaug",
        "bdsg_2018",
        "betrvg",
        "bgb",
        "burlg",
        "erbstg_1974",
        "estg",
        "famfg",
        "famgkg",
        "geng",
        "gewstg",
        "gg",
        "gmbhg",
        "grestg_1983",
        "gwb",
        "gwg_2017",
        "hgb",
        "inso",
        "kschg",
        "kstg_1977",
        "lstdv",
        "muschg_2018",
        "owig_1968",
        "partgg",
        "prodhaftg",
        "pstg",
        "sgb_11",
        "sgb_12",
        "sgb_2",
        "stgb",
        "stvg",
        "stvo_2013",
        "ttdsg",
        "ustg_1980",
        "uwg_2004",
        "vwvfg",
        "woeigg",
        "zpo",
    ]

    base_path = Path(__file__).parent.parent
    toc_index = load_toc_index(base_path)
    target_dir = base_path / "data"

    # Filter TOC to essential laws
    essential_entries = []
    for title, entry in toc_index.items():
        if entry["url_path"] in essential_url_paths:
            essential_entries.append((title, entry))

    logger.info(f"Found {len(essential_entries)} essential laws to download")

    result = download_laws_batch(
        toc_entries=essential_entries,
        target_dir=target_dir,
        max_downloads=0,
        skip_existing=True,
        base_path=base_path,
    )

    logger.info(
        f"\n=== Downloaded: {result['downloaded']}, Skipped: {result['skipped']}, Failed: {result['failed']} ==="
    )

    return {
        "downloaded": result["downloaded"],
        "skipped": result["skipped"],
        "failed": result["failed"],
        "mapping_file": str(base_path / "law_mapping.json"),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download German laws")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all laws (default: essential laws only)",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Don't skip existing laws",
    )

    args = parser.parse_args()

    if args.all:
        download_all_laws(skip_existing=not args.no_skip)
    else:
        download_essential_laws()
