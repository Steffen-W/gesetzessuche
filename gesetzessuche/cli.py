#!/usr/bin/env python3
"""
CLI tool for searching German laws - Uses law_mapping.json for all available laws

USAGE:
    # Show law info
    python gesetzessuche.cli.py AktG

    # List all paragraphs
    python gesetzessuche.cli.py AktG --liste

    # Show specific paragraph
    python gesetzessuche.cli.py AktG --paragraph 1
    python gesetzessuche.cli.py KStG -p 8b

    # Show specific section
    python gesetzessuche.cli.py KStG --paragraph 1 --absatz 3
    python gesetzessuche.cli.py HGB -p 8b -a 2

    # Use reference string (with law code in reference)
    python gesetzessuche.cli.py --reference "BGB § 1"
    python gesetzessuche.cli.py -r "KStG § 8b Absatz 2"

    # Or without law code in reference (requires law argument)
    python gesetzessuche.cli.py BGB --reference "§ 1 Absatz 1 Satz 1"

    # Search for term
    python gesetzessuche.cli.py AktG --suche "Aufsichtsrat"
    python gesetzessuche.cli.py HGB -s "Handelsregister" --case-sensitive
"""

import argparse
import sys

# Relative imports since we're inside the package
from .search import LawSearch
from .utils import get_law


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search German law documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s AktG                             # Show law info
  %(prog)s AktG --liste                     # List all paragraphs
  %(prog)s AktG --paragraph 1               # Show paragraph 1
  %(prog)s KStG --paragraph 8b --absatz 2   # Show specific section
  %(prog)s --reference "BGB § 1"            # Use reference with law code
  %(prog)s -r "KStG § 8b Absatz 2"          # Reference with law code
  %(prog)s BGB --reference "§ 1"            # Reference without law code
  %(prog)s AktG --suche "Aufsichtsrat"      # Search for term
        """,
    )

    parser.add_argument(
        "gesetz",
        nargs="?",
        help="Law code (e.g., AktG, HGB, BGB) - optional if --reference includes law code",
    )

    parser.add_argument(
        "-p",
        "--paragraph",
        help="Show specific paragraph (e.g., 1, 8b)",
    )

    parser.add_argument(
        "-a",
        "--absatz",
        help="Show specific section (requires --paragraph)",
    )

    parser.add_argument(
        "-r",
        "--reference",
        help='Parse reference string (e.g., "§ 1", "§ 8b Absatz 2", "§ 1 Absatz 1 Satz 1")',
    )

    parser.add_argument(
        "-s",
        "--suche",
        help="Search for a term in the law",
    )

    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Case-sensitive search (default: case-insensitive)",
    )

    parser.add_argument(
        "-l",
        "--liste",
        action="store_true",
        help="List all paragraphs",
    )

    args = parser.parse_args()

    # Determine which law to load
    law_to_load = None

    if args.reference:
        # Parse reference to extract law code if present
        from .utils import parse_law_reference

        parsed = parse_law_reference(args.reference)
        if parsed and parsed["law"]:
            # Reference contains law code
            law_to_load = parsed["law"]
        elif args.gesetz:
            # Reference without law code, use positional argument
            law_to_load = args.gesetz
        else:
            print(
                "❌ Reference does not include law code, and no law argument provided!"
            )
            print(
                f'   Either use: python {sys.argv[0]} HGB --reference "{args.reference}"'
            )
            print(
                f'   Or include law in reference: python {sys.argv[0]} --reference "HGB {args.reference}"'
            )
            return 1
    else:
        # No reference, gesetz must be provided
        if not args.gesetz:
            print("❌ Law code required!")
            parser.print_help()
            return 1
        law_to_load = args.gesetz

    # Load law document
    print(f"📖 Loading {law_to_load}...", end=" ", flush=True)
    documents = get_law(law_to_load)

    if not documents:
        print(" ❌")
        print(f"\n❌ Law '{law_to_load}' not found!")
        print("Run: python download_all_laws.py --essential")
        return 1

    print(" ✓")

    # Get law code from jurabk
    law_key = documents.get_jurabk()[0] if documents.get_jurabk() else law_to_load

    # Initialize search
    search = LawSearch(documents, law_key)

    # Execute action
    if args.reference:
        # Use reference parser
        result = search.get_by_reference(args.reference)
        if result:
            print(f"\n{result}\n")
        else:
            print(f"❌ Could not parse or find reference: '{args.reference}'\n")

    elif args.liste:
        print(f"\n📋 All paragraphs in {law_key}:\n")
        paragraphs = search.list_all_paragraphs()
        for para in paragraphs:
            if para["title"]:
                print(f"  {para['number']:15} {para['title']}")
            else:
                print(f"  {para['number']}")
        print(f"\n✓ {len(paragraphs)} paragraphs found\n")

    elif args.paragraph:
        if args.absatz:
            # Search for paragraph and section
            result = search.find_paragraph_section(args.paragraph, args.absatz)
            if result:
                print(f"\n{result}\n")
            else:
                print(
                    f"❌ {law_key} § {args.paragraph} Absatz {args.absatz} not found\n"
                )
        else:
            # Search for paragraph
            result = search.find_paragraph(args.paragraph)
            if result:
                print(f"\n{result}\n")
            else:
                print(f"❌ {law_key} § {args.paragraph} not found\n")

    elif args.suche:
        print(f"\n🔍 Searching for '{args.suche}' in {law_key}...\n")
        results = search.search_term(args.suche, args.case_sensitive)

        if results:
            print(f"✓ {len(results)} match(es) found:\n")
            for idx, match in enumerate(results, 1):
                print(f"{idx}. {match['paragraph']}")
                if match["title"]:
                    print(f"   {match['title']}")
                print(f"   {match['context']}")
                print()
        else:
            print(f"❌ No matches for '{args.suche}' found\n")

    else:
        # Show law info (default action)
        print(f"\n{search.show_info()}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
