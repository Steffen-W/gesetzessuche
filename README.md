# Gesetzessuche

Python-Bibliothek und MCP-Server für komfortablen Zugriff auf deutsches Bundesrecht von [gesetze-im-internet.de](https://www.gesetze-im-internet.de).

**Verfügbar:** >1500 Gesetze, >2900 Verordnungen, >900 Abkommen, >500 Bekanntmachungen (~6500 Dokumente)
Siehe [gesetzessuche/law_mapping.json](gesetzessuche/law_mapping.json) für die vollständige Liste.

## Beispiele

```bash
$ gesetzessuche -r "BGB § 7"
📖 Bürgerliches Gesetzbuch...  ✓

BGB § 7 - Wohnsitz; Begründung und Aufhebung
======================================================================

(1) Wer sich an einem Orte ständig niederlässt, begründet an diesem Orte seinen Wohnsitz.

(2) Der Wohnsitz kann gleichzeitig an mehreren Orten bestehen.

(3) Der Wohnsitz wird aufgehoben, wenn die Niederlassung mit dem Willen aufgehoben wird, sie aufzugeben.
```

```bash
$ gesetzessuche -r "BGB § 7 Absatz 1"
📖 Bürgerliches Gesetzbuch...  ✓

BGB § 7 Absatz 1
======================================================================
Wer sich an einem Orte ständig niederlässt, begründet an diesem Orte seinen Wohnsitz.
```

## Schnellstart

### Installation

```bash
# Direkt von GitHub
pip install git+https://github.com/Steffen-W/gesetzessuche

# Oder von Source (Development)
git clone https://github.com/Steffen-W/gesetzessuche.git
cd gesetzessuche
pip install -e .
```

### Setup & Nutzung

```bash
# Gesetze herunterladen (einmalig)
gesetzessuche-download --essential
```

**CLI Hilfe:**

```
$ gesetzessuche -h

usage: gesetzessuche [-h] [-p PARAGRAPH] [-a ABSATZ] [-r REFERENCE] [-s SUCHE]
                     [--case-sensitive] [-l]
                     [gesetz]

Search German law documents

positional arguments:
  gesetz                Law code (e.g., AktG, HGB, BGB) - optional if
                        --reference includes law code

options:
  -h, --help            show this help message and exit
  -p PARAGRAPH, --paragraph PARAGRAPH
                        Show specific paragraph (e.g., 1, 8b)
  -a ABSATZ, --absatz ABSATZ
                        Show specific section (requires --paragraph)
  -r REFERENCE, --reference REFERENCE
                        Parse reference string (e.g., "§ 1", "§ 8b Absatz 2",
                        "§ 1 Absatz 1 Satz 1")
  -s SUCHE, --suche SUCHE
                        Search for a term in the law
  --case-sensitive      Case-sensitive search (default: case-insensitive)
  -l, --liste           List all paragraphs

Examples:
  gesetzessuche AktG                             # Show law info
  gesetzessuche AktG --liste                     # List all paragraphs
  gesetzessuche AktG --paragraph 1               # Show paragraph 1
  gesetzessuche KStG --paragraph 8b --absatz 2   # Show specific section
  gesetzessuche --reference "BGB § 1"            # Use reference with law code
  gesetzessuche -r "KStG § 8b Absatz 2"          # Reference with law code
  gesetzessuche BGB --reference "§ 1"            # Reference without law code
  gesetzessuche AktG --suche "Aufsichtsrat"      # Search for term
```

## MCP Server

**Claude Desktop Config** (`~/.config/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gesetzessuche": {
      "command": "python3",
      "args": ["-m", "gesetzessuche.server"]
    }
  }
}
```

**Verfügbare MCP Tools:**

- **`get_law_reference(reference)`** - Haupttool: `"KStG § 6 Absatz 1"`
- **`search_law(law, term)`** - Volltextsuche in Gesetz
- **`list_paragraphs(law)`** - Paragraphen-Übersicht
- **`list_laws()`** - Alle verfügbaren Gesetze

## Python API

```python
from gesetzessuche import LawSearch, get_law

# Gesetz laden
documents = get_law("BGB")
law_key = documents.get_jurabk()[0]
search = LawSearch(documents, law_key)

# Referenz-String nutzen (wie CLI)
text = search.get_by_reference("BGB § 1 Absatz 1")
print(text)

# Suchen
results = search.search_term("Rechtsfähigkeit")
for result in results:
    print(f"{result['paragraph']}: {result['context']}")

# Alle Paragraphen
paragraphs = search.list_all_paragraphs()
```

## Projektstruktur

```
gesetzessuche/
├── gesetzessuche/          # Python Package
│   ├── __init__.py        # Public API
│   ├── __version__.py     # Version info
│   ├── cli.py            # CLI entry point
│   ├── server.py         # MCP server entry point
│   ├── download.py       # Download entry point
│   ├── models.py         # Pydantic Models
│   ├── parser.py         # XML Parser
│   ├── search.py         # Search & Query API
│   ├── formatting.py     # Text formatting utilities
│   ├── utils.py          # Utilities
│   └── law_mapping.json  # Law index
├── tests/                 # Test suite
├── data/                  # Downloaded laws (XML)
└── pyproject.toml         # Package configuration
```

## Verfügbare Gesetze

Nach `gesetzessuche-download --essential`:

- **BGB** - Bürgerliches Gesetzbuch
- **HGB** - Handelsgesetzbuch
- **AktG** - Aktiengesetz
- **GmbHG** - GmbH-Gesetz
- **StGB** - Strafgesetzbuch
- **KStG** - Körperschaftsteuergesetz
- **UStG** - Umsatzsteuergesetz
- **ArbZG** - Arbeitszeitgesetz
- Und viele mehr...

Vollständige Liste: [gesetzessuche/law_mapping.json](gesetzessuche/law_mapping.json)

## Lizenz

- **Gesetzestexte**: Public Domain (Bundesministerium der Justiz)
- **Software**: MIT License
- **Quelle**: [gesetze-im-internet.de](https://www.gesetze-im-internet.de)
