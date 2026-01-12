# Gesetzessuche

Python-Bibliothek und MCP-Server für komfortablen Zugriff auf >6400 deutsche Bundesgesetze von [gesetze-im-internet.de](https://www.gesetze-im-internet.de).

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

# CLI nutzen (nach Installation)
gesetzessuche -r "BGB § 1"
gesetzessuche -r "KStG § 6 Absatz 1"
gesetzessuche -r "HGB § 1 Absatz 1 Satz 1"

# Oder als Python-Modul (ohne Installation)
python -m gesetzessuche.cli -r "BGB § 1"
python -m gesetzessuche.download --essential

# Alternative Syntax
gesetzessuche BGB --paragraph 1
gesetzessuche KStG --paragraph 8b --absatz 2

# Weitere Funktionen
gesetzessuche AktG --liste              # Alle Paragraphen
gesetzessuche HGB --suche "Handelsregister"  # Volltextsuche
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
│   ├── cli.py            # CLI entry point
│   ├── server.py         # MCP server entry point
│   ├── download.py       # Download entry point
│   ├── models.py         # Pydantic Models
│   ├── parser.py         # XML Parser
│   ├── search.py         # Search & Query API
│   └── utils.py          # Utilities
├── tests/                 # Test suite
├── data/                  # Downloaded laws (XML)
├── law_mapping.json       # Law index
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

Vollständige Liste: `law_mapping.json`

## Tests

```bash
python tests/test_parser.py
python tests/test_mcp_server.py
python tests/test_mcp_cache.py
```

## Lizenz

- **Gesetzestexte**: Public Domain (Bundesministerium der Justiz)
- **Software**: MIT License
- **Quelle**: [gesetze-im-internet.de](https://www.gesetze-im-internet.de)
