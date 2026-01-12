"""
Pydantic Models für das gii-norm.dtd Schema
Vollständige Abbildung der offiziellen DTD-Definition von gesetze-im-internet.de
"""

from datetime import date
from typing import List, Literal, Optional, TypedDict, Union

from pydantic import BaseModel, ConfigDict, Field


# TypedDicts für API-Responses und Suchergebnisse
class SearchResult(TypedDict):
    """Search result entry for term searches in laws"""

    paragraph: str
    title: str
    context: str


class LawMapping(TypedDict):
    """Law mapping entry from law_mapping.json"""

    filename: str
    title: str
    category: str
    builddate: str
    url_path: str


class LawReference(TypedDict):
    """Parsed law reference (e.g., '§ 52 Absatz 1 Satz 1' or 'BGB § 52 Absatz 1')"""

    law: Optional[str]  # Optional: Law code (e.g., "BGB", "HGB")
    paragraph: str  # Required: e.g., "52", "8b"
    section: Optional[str]  # Optional: Absatz number
    number: Optional[str]  # Optional: Nummer
    letter: Optional[str]  # Optional: Buchstabe (a, b, c)
    sentence: Optional[str]  # Optional: Satz number


class Anlageabgabe(BaseModel):
    """Anlage- und Abgabedaten in Fundstelle"""

    anlagedat: Optional[str] = None
    dokst: Optional[str] = None
    abgabedat: Optional[str] = None


class Fundstelle(BaseModel):
    """Veröffentlichungsangaben eines Gesetzes"""

    typ: Optional[Literal["amtlich", "nichtamtlich"]] = None
    periodikum: Optional[str] = None
    zitstelle: Optional[str] = None
    anlageabgabe: Optional[Anlageabgabe] = None


class Standangabe(BaseModel):
    """Aktualitätsinformation des Gesetzes"""

    checked: Optional[Literal["ja", "nein"]] = None
    standtyp: Optional[str] = None
    standkommentar: Optional[str] = None


class Gliederungseinheit(BaseModel):
    """Strukturelemente wie Buch, Abschnitt, Kapitel"""

    gliederungskennzahl: Optional[str] = None
    gliederungsbez: Optional[str] = None
    gliederungstitel: Optional[str] = None


class AusfertigungsDatum(BaseModel):
    """Ausfertigungsdatum mit manuell-Attribut"""

    manuell: Literal["ja", "nein"]
    datum: Optional[date] = None


class Metadaten(BaseModel):
    """Metadaten einer Norm (Paragraph oder Gliederungseinheit)"""

    jurabk: List[str] = Field(default_factory=list)
    amtabk: Optional[str] = None
    ausfertigung_datum: Optional[AusfertigungsDatum] = Field(
        None, alias="ausfertigung-datum"
    )
    fundstelle: List[Fundstelle] = Field(default_factory=list)
    kurzue: Optional[str] = None
    langue: Optional[str] = None
    standangabe: List[Standangabe] = Field(default_factory=list)

    enbez: Optional[str] = None
    titel: Optional[str] = None

    gliederungseinheit: Optional[Gliederungseinheit] = None

    model_config = ConfigDict(populate_by_name=True)


class IMG(BaseModel):
    """Bild-Element"""

    src: str
    alt: Optional[str] = None
    title: Optional[str] = None
    orient: Optional[str] = None
    pos: Optional[str] = None
    align: Optional[str] = None
    size: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    units: Optional[str] = None
    type: Optional[str] = None


class FILE(BaseModel):
    """Datei-Anhang"""

    src: str
    preview: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None


class DT(BaseModel):
    """Definition Term (Nummer/Buchstabe in Liste)"""

    id: Optional[str] = None
    text: Optional[str] = None


class LA(BaseModel):
    """Listen-Absatz"""

    id: Optional[str] = None
    size: Optional[Literal["normal", "small", "tiny"]] = None
    value: Optional[str] = None
    text: Optional[str] = None
    children: List["ContentElement"] = Field(default_factory=list)


class DD(BaseModel):
    """Definition Description (Text zu DT)"""

    id: Optional[str] = None
    la: Optional[LA] = None
    revisions: List["Revision"] = Field(default_factory=list)


class DLItem(BaseModel):
    """Ein DT/DD-Paar in einer Definition List"""

    dt: DT
    dd: DD


class DL(BaseModel):
    """Definition List (nummerierte/alphabetische Liste)"""

    id: Optional[str] = None
    indent: Optional[str] = None
    font: Optional[str] = None
    type: Optional[str] = None
    items: List[DLItem] = Field(default_factory=list)


class Entry(BaseModel):
    """Tabellenzelle"""

    id: Optional[str] = None
    align: Optional[str] = None
    valign: Optional[str] = None
    colname: Optional[str] = None
    namest: Optional[str] = None
    nameend: Optional[str] = None
    morerows: Optional[int] = None
    colsep: Optional[str] = None
    rowsep: Optional[str] = None
    content: List["ContentElement"] = Field(default_factory=list)


class Row(BaseModel):
    """Tabellenzeile"""

    id: Optional[str] = None
    rowsep: Optional[str] = None
    valign: Optional[str] = None
    entries: List[Entry] = Field(default_factory=list)


class Colspec(BaseModel):
    """Spaltendefinition"""

    colname: Optional[str] = None
    colnum: Optional[int] = None
    colwidth: Optional[str] = None
    align: Optional[str] = None
    colsep: Optional[str] = None
    rowsep: Optional[str] = None


class THead(BaseModel):
    """Tabellenkopf"""

    rows: List[Row] = Field(default_factory=list)


class TBody(BaseModel):
    """Tabellenkörper"""

    rows: List[Row] = Field(default_factory=list)


class TFoot(BaseModel):
    """Tabellenfuß"""

    rows: List[Row] = Field(default_factory=list)


class TGroup(BaseModel):
    """Tabellengruppe"""

    cols: int
    colspecs: List[Colspec] = Field(default_factory=list)
    thead: Optional[THead] = None
    tbody: TBody
    tfoot: Optional[TFoot] = None


class Table(BaseModel):
    """Tabelle"""

    id: Optional[str] = None
    frame: Optional[str] = None
    colsep: Optional[str] = None
    rowsep: Optional[str] = None
    title: Optional[str] = None
    tgroups: List[TGroup] = Field(default_factory=list)


class P(BaseModel):
    """Absatz"""

    id: Optional[str] = None
    content: List["ContentElement"] = Field(default_factory=list)
    raw_text: Optional[str] = None


class Footnote(BaseModel):
    """Einzelne Fußnote"""

    id: str
    prefix: Optional[str] = None
    fn_z: Optional[str] = None
    postfix: Optional[str] = None
    pos: Optional[str] = None
    group: Optional[str] = None
    content: List["ContentElement"] = Field(default_factory=list)


class Footnotes(BaseModel):
    """Fußnoten-Container"""

    footnotes: List[Footnote] = Field(default_factory=list)


class FnR(BaseModel):
    """Fußnoten-Referenz"""

    id: str


class FnArea(BaseModel):
    """Fußnoten-Referenzbereich"""

    line: Literal["0", "1"] = "1"
    size: Literal["normal", "large", "small"] = "normal"
    fn_refs: List[FnR] = Field(default_factory=list)


class TOC(BaseModel):
    """Table of Contents"""

    id: Optional[str] = None
    content: List["ContentElement"] = Field(default_factory=list)


class Kommentar(BaseModel):
    """Kommentar-Element"""

    typ: Literal["Stand", "Stand-Hinweis", "Hinweis", "Fundstelle", "Verarbeitung"]
    text: Optional[str] = None


class Pre(BaseModel):
    """Vorformatierter Text"""

    text: Optional[str] = None


class FormatElement(BaseModel):
    """Formatierungselement (B, I, U, SUP, SUB, etc.)"""

    tag: str
    id: Optional[str] = None
    cls: Optional[str] = Field(default=None, alias="class")
    text: Optional[str] = None
    children: List["ContentElement"] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


ContentElement = Union[
    str, P, DL, Table, IMG, FILE, FnArea, TOC, Kommentar, Pre, FormatElement, "Revision"
]


class Revision(BaseModel):
    """Änderungsblock"""

    id: Optional[str] = None
    postfix: Optional[str] = None
    content: List[ContentElement] = Field(default_factory=list)


class Content(BaseModel):
    """Content-Container für strukturierten Text"""

    id: Optional[str] = None
    elements: List[ContentElement] = Field(default_factory=list)
    raw_text: Optional[str] = None


class Text(BaseModel):
    """Haupttext einer Norm"""

    format: Optional[str] = None
    toc: Optional[TOC] = None
    content: Optional[Content] = None
    footnotes: Optional[Footnotes] = None


class Fussnoten(BaseModel):
    """Fußnotenbereich einer Norm"""

    format: Optional[str] = None
    toc: Optional[TOC] = None
    content: Optional[Content] = None
    footnotes: Optional[Footnotes] = None


class Textdaten(BaseModel):
    """Textdaten einer Norm (Inhalt)"""

    text: Optional[Text] = None
    fussnoten: Optional[Fussnoten] = None


class Norm(BaseModel):
    """Eine einzelne Norm (Paragraph, Artikel oder Gliederungseinheit)"""

    builddate: Optional[str] = None
    doknr: Optional[str] = None

    metadaten: Optional[Metadaten] = None
    textdaten: Optional[Textdaten] = None


class Dokumente(BaseModel):
    """Root-Element: Collection aller Normen eines Gesetzes"""

    builddate: Optional[str] = None
    doknr: Optional[str] = None
    normen: List[Norm] = Field(default_factory=list)

    def get_titel(self) -> Optional[str]:
        """Gibt den Gesetzestitel zurück"""
        if self.normen and self.normen[0].metadaten:
            return self.normen[0].metadaten.langue or self.normen[0].metadaten.titel
        return None

    def get_jurabk(self) -> List[str]:
        """Gibt die juristischen Abkürzungen zurück"""
        if self.normen and self.normen[0].metadaten:
            return self.normen[0].metadaten.jurabk
        return []

    def get_paragraphen(self) -> List[Norm]:
        """Gibt nur Paragraphen zurück (keine Gliederungseinheiten)"""
        return [norm for norm in self.normen if norm.metadaten and norm.metadaten.enbez]

    def get_gliederung(self) -> List[Norm]:
        """Gibt nur Gliederungseinheiten zurück"""
        return [
            norm
            for norm in self.normen
            if norm.metadaten and norm.metadaten.gliederungseinheit
        ]

    def find_paragraph(self, enbez: str) -> Optional[Norm]:
        """Findet einen Paragraphen nach seiner Bezeichnung (z.B. '§ 1')"""
        enbez_normalized = enbez.replace("§", "").strip()
        for norm in self.get_paragraphen():
            if norm.metadaten and norm.metadaten.enbez:
                norm_enbez = norm.metadaten.enbez.replace("§", "").strip()
                if norm_enbez == enbez_normalized:
                    return norm
        return None


# Rebuild all models with forward references to ContentElement
LA.model_rebuild()
DD.model_rebuild()
Entry.model_rebuild()
P.model_rebuild()
Footnote.model_rebuild()
TOC.model_rebuild()
FormatElement.model_rebuild()
Revision.model_rebuild()
Content.model_rebuild()
