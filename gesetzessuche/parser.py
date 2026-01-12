"""
XML Parser für deutsche Gesetzestexte
Konvertiert gii-norm.dtd konforme XML-Dateien in Pydantic Models
"""

import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path
from typing import List, Literal, Optional, cast

from .models import (
    DD,
    DL,
    DT,
    FILE,
    IMG,
    LA,
    TOC,
    Anlageabgabe,
    AusfertigungsDatum,
    Colspec,
    Content,
    ContentElement,
    DLItem,
    Dokumente,
    Entry,
    FnArea,
    FnR,
    Footnote,
    Footnotes,
    FormatElement,
    Fundstelle,
    Fussnoten,
    Gliederungseinheit,
    Kommentar,
    Metadaten,
    Norm,
    P,
    Pre,
    Revision,
    Row,
    Standangabe,
    Table,
    TBody,
    Text,
    Textdaten,
    TFoot,
    TGroup,
    THead,
)


class GesetzParser:
    """Parser für Gesetzes-XML-Dateien gemäß gii-norm.dtd"""

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize whitespace without destroying word boundaries"""
        # Replace line breaks and tabs with spaces
        text = (
            text.replace("\r\n", " ")
            .replace("\r", " ")
            .replace("\n", " ")
            .replace("\t", " ")
        )
        # Collapse multiple spaces into one
        while "  " in text:
            text = text.replace("  ", " ")
        return text

    @staticmethod
    def _get_attr(elem: ET.Element, *names: str) -> Optional[str]:
        """Robust attribute reading - tries multiple case variants"""
        for name in names:
            val = elem.get(name)
            if val:
                return val
        return None

    @staticmethod
    def _get_text(elem: ET.Element, tag: str) -> Optional[str]:
        """Extrahiert Text aus Child-Element"""
        child = elem.find(tag)
        return child.text.strip() if child is not None and child.text else None

    @staticmethod
    def _get_all_text(elem: ET.Element, tag: str) -> List[str]:
        """Extrahiert Text aus allen Child-Elementen mit Tag"""
        return [
            child.text.strip()
            for child in elem.findall(tag)
            if child.text and child.text.strip()
        ]

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[date]:
        """Parst Datumsstring im Format YYYY-MM-DD"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def parse_anlageabgabe(self, elem: Optional[ET.Element]) -> Optional[Anlageabgabe]:
        """Parst Anlageabgabe-Element"""
        if elem is None:
            return None

        return Anlageabgabe(
            anlagedat=self._get_text(elem, "anlagedat"),
            dokst=self._get_text(elem, "dokst"),
            abgabedat=self._get_text(elem, "abgabedat"),
        )

    def parse_fundstelle(self, elem: Optional[ET.Element]) -> Optional[Fundstelle]:
        """Parst Fundstelle-Element"""
        if elem is None:
            return None

        typ_raw = elem.get("typ")
        typ: Optional[Literal["amtlich", "nichtamtlich"]] = None
        if typ_raw in ("amtlich", "nichtamtlich"):
            typ = cast(Literal["amtlich", "nichtamtlich"], typ_raw)

        return Fundstelle(
            typ=typ,
            periodikum=self._get_text(elem, "periodikum"),
            zitstelle=self._get_text(elem, "zitstelle"),
            anlageabgabe=self.parse_anlageabgabe(elem.find("anlageabgabe")),
        )

    def parse_standangabe(self, elem: Optional[ET.Element]) -> Optional[Standangabe]:
        """Parst Standangabe-Element"""
        if elem is None:
            return None

        checked_raw = elem.get("checked")
        checked: Optional[Literal["ja", "nein"]] = None
        if checked_raw in ("ja", "nein"):
            checked = cast(Literal["ja", "nein"], checked_raw)

        return Standangabe(
            checked=checked,
            standtyp=self._get_text(elem, "standtyp"),
            standkommentar=self._get_text(elem, "standkommentar"),
        )

    def parse_gliederungseinheit(
        self, elem: Optional[ET.Element]
    ) -> Optional[Gliederungseinheit]:
        """Parst Gliederungseinheit-Element"""
        if elem is None:
            return None

        return Gliederungseinheit(
            gliederungskennzahl=self._get_text(elem, "gliederungskennzahl"),
            gliederungsbez=self._get_text(elem, "gliederungsbez"),
            gliederungstitel=self._get_text(elem, "gliederungstitel"),
        )

    def parse_ausfertigung_datum(
        self, elem: Optional[ET.Element]
    ) -> Optional[AusfertigungsDatum]:
        """Parst ausfertigung-datum-Element"""
        if elem is None:
            return None

        manuell_raw = elem.get("manuell") or "nein"
        manuell: Literal["ja", "nein"] = "nein"
        if manuell_raw in ("ja", "nein"):
            manuell = cast(Literal["ja", "nein"], manuell_raw)
        datum = self._parse_date(elem.text) if elem.text else None

        return AusfertigungsDatum(manuell=manuell, datum=datum)

    def parse_metadaten(self, elem: Optional[ET.Element]) -> Optional[Metadaten]:
        """Parst Metadaten-Element"""
        if elem is None:
            return None

        fundstelle_list = []
        for f in elem.findall("fundstelle"):
            parsed_f = self.parse_fundstelle(f)
            if parsed_f is not None:
                fundstelle_list.append(parsed_f)

        standangabe_list = []
        for s in elem.findall("standangabe"):
            parsed_s = self.parse_standangabe(s)
            if parsed_s is not None:
                standangabe_list.append(parsed_s)

        return Metadaten(
            jurabk=self._get_all_text(elem, "jurabk"),
            amtabk=self._get_text(elem, "amtabk"),
            **{
                "ausfertigung-datum": self.parse_ausfertigung_datum(
                    elem.find("ausfertigung-datum")
                )
            },
            fundstelle=fundstelle_list,
            kurzue=self._get_text(elem, "kurzue"),
            langue=self._get_text(elem, "langue"),
            standangabe=standangabe_list,
            enbez=self._get_text(elem, "enbez"),
            titel=self._get_text(elem, "titel"),
            gliederungseinheit=self.parse_gliederungseinheit(
                elem.find("gliederungseinheit")
            ),
        )

    def parse_img(self, elem: ET.Element) -> IMG:
        """Parst IMG-Element"""
        return IMG(
            src=elem.get("SRC", ""),
            alt=elem.get("alt"),
            title=elem.get("title"),
            orient=elem.get("orient"),
            pos=elem.get("Pos"),
            align=elem.get("Align"),
            size=elem.get("Size"),
            width=elem.get("Width"),
            height=elem.get("Height"),
            units=elem.get("Units"),
            type=elem.get("Type"),
        )

    def parse_file_element(self, elem: ET.Element) -> FILE:
        """Parst FILE-Element"""
        return FILE(
            src=elem.get("SRC", ""),
            preview=elem.get("PREVIEW"),
            type=elem.get("Type"),
            title=elem.get("title"),
        )

    def parse_fnr(self, elem: ET.Element) -> FnR:
        """Parst FnR-Element"""
        return FnR(id=elem.get("ID", ""))

    def parse_fnarea(self, elem: ET.Element) -> FnArea:
        """Parst FnArea-Element"""
        line_raw = elem.get("Line", "1")
        line: Literal["0", "1"] = "1"
        if line_raw in ("0", "1"):
            line = cast(Literal["0", "1"], line_raw)

        size_raw = elem.get("Size", "normal")
        size: Literal["normal", "large", "small"] = "normal"
        if size_raw in ("normal", "large", "small"):
            size = cast(Literal["normal", "large", "small"], size_raw)

        return FnArea(
            line=line,
            size=size,
            fn_refs=[self.parse_fnr(fnr) for fnr in elem.findall("FnR")],
        )

    def parse_kommentar(self, elem: ET.Element) -> Kommentar:
        """Parst kommentar-Element"""
        typ_raw = elem.get("typ", "Hinweis")
        typ: Literal[
            "Stand", "Stand-Hinweis", "Hinweis", "Fundstelle", "Verarbeitung"
        ] = "Hinweis"
        if typ_raw in (
            "Stand",
            "Stand-Hinweis",
            "Hinweis",
            "Fundstelle",
            "Verarbeitung",
        ):
            typ = cast(
                Literal[
                    "Stand", "Stand-Hinweis", "Hinweis", "Fundstelle", "Verarbeitung"
                ],
                typ_raw,
            )
        return Kommentar(typ=typ, text=elem.text)

    def parse_pre(self, elem: ET.Element) -> Pre:
        """Parst pre-Element"""
        return Pre(text=self._extract_raw_text(elem))

    def parse_dt(self, elem: ET.Element) -> DT:
        """Parst DT-Element"""
        return DT(id=elem.get("ID"), text=self._extract_raw_text(elem))

    def parse_la(self, elem: ET.Element) -> LA:
        """Parst LA-Element"""
        size_raw = elem.get("Size")
        size: Optional[Literal["normal", "small", "tiny"]] = None
        if size_raw in ("normal", "small", "tiny"):
            size = cast(Literal["normal", "small", "tiny"], size_raw)

        return LA(
            id=elem.get("ID"),
            size=size,
            value=elem.get("Value"),
            text=self._extract_raw_text(elem) if not list(elem) else None,
            children=self.parse_content_elements(elem) if list(elem) else [],
        )

    def parse_dd(self, elem: ET.Element) -> DD:
        """Parst DD-Element"""
        la_elem = elem.find("LA")
        revisions = [self.parse_revision(r) for r in elem.findall("Revision")]

        return DD(
            id=elem.get("ID"),
            la=self.parse_la(la_elem) if la_elem is not None else None,
            revisions=revisions,
        )

    def parse_dl(self, elem: ET.Element) -> DL:
        """Parst DL-Element (Definition List)"""
        items = []
        current_dt = None

        for child in elem:
            if child.tag == "DT":
                current_dt = self.parse_dt(child)
            elif child.tag == "DD" and current_dt:
                dd = self.parse_dd(child)
                items.append(DLItem(dt=current_dt, dd=dd))
                current_dt = None

        return DL(
            id=self._get_attr(elem, "ID", "Id", "id"),
            indent=elem.get("Indent"),
            font=elem.get("Font"),
            type=elem.get("Type"),
            items=items,
        )

    def parse_colspec(self, elem: ET.Element) -> Colspec:
        """Parst colspec-Element"""
        colnum_str = elem.get("colnum")
        return Colspec(
            colname=elem.get("colname"),
            colnum=int(colnum_str) if colnum_str else None,
            colwidth=elem.get("colwidth"),
            align=elem.get("align"),
            colsep=elem.get("colsep"),
            rowsep=elem.get("rowsep"),
        )

    def parse_entry(self, elem: ET.Element) -> Entry:
        """Parst entry-Element (Tabellenzelle)"""
        morerows_str = elem.get("morerows")
        return Entry(
            id=elem.get("ID"),
            align=elem.get("align"),
            valign=elem.get("valign"),
            colname=elem.get("colname"),
            namest=elem.get("namest"),
            nameend=elem.get("nameend"),
            morerows=int(morerows_str) if morerows_str else None,
            colsep=elem.get("colsep"),
            rowsep=elem.get("rowsep"),
            content=self.parse_content_elements(elem),
        )

    def parse_row(self, elem: ET.Element) -> Row:
        """Parst row-Element (Tabellenzeile)"""
        return Row(
            id=elem.get("ID"),
            rowsep=elem.get("rowsep"),
            valign=elem.get("valign"),
            entries=[self.parse_entry(e) for e in elem.findall("entry")],
        )

    def parse_thead(self, elem: ET.Element) -> THead:
        """Parst thead-Element"""
        return THead(rows=[self.parse_row(r) for r in elem.findall("row")])

    def parse_tbody(self, elem: ET.Element) -> TBody:
        """Parst tbody-Element"""
        return TBody(rows=[self.parse_row(r) for r in elem.findall("row")])

    def parse_tfoot(self, elem: ET.Element) -> TFoot:
        """Parst tfoot-Element"""
        return TFoot(rows=[self.parse_row(r) for r in elem.findall("row")])

    def parse_tgroup(self, elem: ET.Element) -> TGroup:
        """Parst tgroup-Element"""
        thead_elem = elem.find("thead")
        tbody_elem = elem.find("tbody")
        tfoot_elem = elem.find("tfoot")

        if tbody_elem is None:
            tbody_elem = ET.Element("tbody")

        return TGroup(
            cols=int(elem.get("cols", "1")),
            colspecs=[self.parse_colspec(c) for c in elem.findall("colspec")],
            thead=self.parse_thead(thead_elem) if thead_elem is not None else None,
            tbody=self.parse_tbody(tbody_elem),
            tfoot=self.parse_tfoot(tfoot_elem) if tfoot_elem is not None else None,
        )

    def parse_table(self, elem: ET.Element) -> Table:
        """Parst table-Element"""
        title_elem = elem.find("Title")

        return Table(
            id=self._get_attr(elem, "ID", "Id", "id"),
            frame=elem.get("frame"),
            colsep=elem.get("colsep"),
            rowsep=elem.get("rowsep"),
            title=title_elem.text if title_elem is not None else None,
            tgroups=[self.parse_tgroup(tg) for tg in elem.findall("tgroup")],
        )

    def parse_format_element(self, elem: ET.Element) -> FormatElement:
        """Parst Formatierungselement (B, I, U, SUP, SUB, etc.)"""
        return FormatElement(
            tag=elem.tag,
            id=self._get_attr(elem, "ID", "Id", "id"),
            **{"class": self._get_attr(elem, "Class", "class")},
            text=elem.text,
            children=self.parse_content_elements(elem),
        )

    def parse_p(self, elem: ET.Element) -> P:
        """Parst P-Element (Absatz)"""
        return P(
            id=elem.get("ID"),
            content=self.parse_content_elements(elem),
            raw_text=self._extract_raw_text(elem),
        )

    def parse_revision(self, elem: ET.Element) -> Revision:
        """Parst Revision-Element"""
        return Revision(
            id=elem.get("ID"),
            postfix=elem.get("Postfix"),
            content=self.parse_content_elements(elem),
        )

    def parse_toc(self, elem: ET.Element) -> TOC:
        """Parst TOC-Element"""
        return TOC(id=elem.get("ID"), content=self.parse_content_elements(elem))

    def parse_content_elements(self, elem: ET.Element) -> List[ContentElement]:
        """Parst Content-Elemente rekursiv"""
        elements: List[ContentElement] = []

        if elem.text:
            text = self._normalize_whitespace(elem.text)
            # Only strip leading/trailing whitespace from the entire text block
            text = text.strip()
            if text:
                elements.append(text)

        for child in elem:
            if child.tag == "SUP" and (
                child.get("class") == "Rec" or child.get("Class") == "Rec"
            ):
                pass
            elif child.tag == "P":
                elements.append(self.parse_p(child))
            elif child.tag == "DL":
                elements.append(self.parse_dl(child))
            elif child.tag == "table":
                elements.append(self.parse_table(child))
            elif child.tag == "IMG":
                elements.append(self.parse_img(child))
            elif child.tag == "FILE":
                elements.append(self.parse_file_element(child))
            elif child.tag == "FnArea":
                elements.append(self.parse_fnarea(child))
            elif child.tag == "TOC":
                elements.append(self.parse_toc(child))
            elif child.tag == "kommentar":
                elements.append(self.parse_kommentar(child))
            elif child.tag == "pre":
                elements.append(self.parse_pre(child))
            elif child.tag == "Revision":
                elements.append(self.parse_revision(child))
            elif child.tag in ("B", "I", "U", "SUP", "SUB", "SP", "small", "Citation"):
                elements.append(self.parse_format_element(child))
            elif child.tag == "BR":
                elements.append("\n")
            else:
                text = self._extract_raw_text(child)
                if text:
                    elements.append(text)

            if child.tail:
                tail = self._normalize_whitespace(child.tail)
                # Preserve spacing between elements - only strip if empty
                if tail and tail != " ":
                    # Keep leading/trailing space if not just whitespace
                    elements.append(tail)

        return elements

    def parse_content(self, elem: Optional[ET.Element]) -> Optional[Content]:
        """Parst Content-Element"""
        if elem is None:
            return None

        return Content(
            id=elem.get("ID"),
            elements=self.parse_content_elements(elem),
            raw_text=self._extract_raw_text(elem),
        )

    def parse_footnote(self, elem: ET.Element) -> Footnote:
        """Parst Footnote-Element"""
        return Footnote(
            id=elem.get("ID", ""),
            prefix=elem.get("Prefix"),
            fn_z=elem.get("FnZ"),
            postfix=elem.get("Postfix"),
            pos=elem.get("Pos"),
            group=elem.get("Group"),
            content=self.parse_content_elements(elem),
        )

    def parse_footnotes(self, elem: Optional[ET.Element]) -> Optional[Footnotes]:
        """Parst Footnotes-Element"""
        if elem is None:
            return None

        return Footnotes(
            footnotes=[self.parse_footnote(fn) for fn in elem.findall("Footnote")]
        )

    def _extract_raw_text(self, elem: ET.Element) -> str:
        """Extrahiert reinen Text aus Element (ohne Tags)"""
        text_parts = []

        if elem.text:
            text_parts.append(elem.text)

        for child in elem:
            if child.tag == "SUP" and (
                child.get("class") == "Rec" or child.get("Class") == "Rec"
            ):
                if child.tail:
                    text_parts.append(child.tail)
                continue

            text_parts.append(self._extract_raw_text(child))
            if child.tail:
                text_parts.append(child.tail)

        text = " ".join(text_parts)
        text = " ".join(text.split())
        return text.strip()

    def parse_text(self, elem: Optional[ET.Element]) -> Optional[Text]:
        """Parst Text-Element"""
        if elem is None:
            return None

        toc_elem = elem.find("TOC")
        content_elem = elem.find("Content")
        footnotes_elem = elem.find("Footnotes")

        return Text(
            format=elem.get("format"),
            toc=self.parse_toc(toc_elem) if toc_elem is not None else None,
            content=self.parse_content(content_elem),
            footnotes=self.parse_footnotes(footnotes_elem),
        )

    def parse_fussnoten(self, elem: Optional[ET.Element]) -> Optional[Fussnoten]:
        """Parst fussnoten-Element"""
        if elem is None:
            return None

        toc_elem = elem.find("TOC")
        content_elem = elem.find("Content")
        footnotes_elem = elem.find("Footnotes")

        return Fussnoten(
            format=elem.get("format"),
            toc=self.parse_toc(toc_elem) if toc_elem is not None else None,
            content=self.parse_content(content_elem),
            footnotes=self.parse_footnotes(footnotes_elem),
        )

    def parse_textdaten(self, elem: Optional[ET.Element]) -> Optional[Textdaten]:
        """Parst Textdaten-Element"""
        if elem is None:
            return None

        return Textdaten(
            text=self.parse_text(elem.find("text")),
            fussnoten=self.parse_fussnoten(elem.find("fussnoten")),
        )

    def parse_norm(self, elem: ET.Element) -> Norm:
        """Parst Norm-Element"""
        return Norm(
            builddate=elem.get("builddate"),
            doknr=elem.get("doknr"),
            metadaten=self.parse_metadaten(elem.find("metadaten")),
            textdaten=self.parse_textdaten(elem.find("textdaten")),
        )

    def parse_dokumente(self, root: ET.Element) -> Dokumente:
        """Parst Dokumente-Root-Element"""
        # Use direct children only to avoid nested duplicates
        normen = [self.parse_norm(norm) for norm in root.findall("./norm")]

        return Dokumente(
            builddate=root.get("builddate"), doknr=root.get("doknr"), normen=normen
        )

    def parse_xml_file(self, file_path: Path | str) -> Dokumente:
        """
        Parst eine Gesetzes-XML-Datei

        Args:
            file_path: Pfad zur XML-Datei

        Returns:
            Dokumente-Objekt mit allen Normen
        """
        tree = ET.parse(file_path)
        root = tree.getroot()
        return self.parse_dokumente(root)


def parse_gesetz(file_path: Path | str) -> Dokumente:
    """
    Convenience-Funktion zum Parsen einer Gesetzes-XML-Datei

    Args:
        file_path: Pfad zur XML-Datei

    Returns:
        Dokumente-Objekt mit allen Normen
    """
    parser = GesetzParser()
    return parser.parse_xml_file(file_path)
