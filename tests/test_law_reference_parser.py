"""
Test suite for law reference parser (parse_law_reference).

Tests various formats of German law references:
- Simple paragraphs (§ 1)
- Paragraphs with letters (§ 8b)
- Paragraphs with sections (§ 7 Absatz 2)
- Full references with sentences (§ 52 Absatz 1 Satz 1)
- Article references (Artikel 20 Absatz 3)
- Abbreviated forms (Art. 1 Abs. 2)
"""

import pytest

from gesetzessuche.utils import parse_law_reference


class TestLawReferenceParser:
    """Test cases for parse_law_reference function."""

    def test_simple_paragraph(self):
        """Test simple paragraph reference: § 1"""
        result = parse_law_reference("§ 1")
        assert result is not None
        assert result["paragraph"] == "1"
        assert result["section"] is None
        assert result["sentence"] is None

    def test_paragraph_with_letter(self):
        """Test paragraph with letter suffix: § 8b"""
        result = parse_law_reference("§ 8b")
        assert result is not None
        assert result["paragraph"] == "8b"
        assert result["section"] is None
        assert result["sentence"] is None

    def test_paragraph_with_section(self):
        """Test paragraph with section: § 7 Absatz 2"""
        result = parse_law_reference("§ 7 Absatz 2")
        assert result is not None
        assert result["paragraph"] == "7"
        assert result["section"] == "2"
        assert result["sentence"] is None

    def test_paragraph_with_section_abbreviated(self):
        """Test paragraph with abbreviated section: § 7 Abs. 2"""
        result = parse_law_reference("§ 7 Abs. 2")
        assert result is not None
        assert result["paragraph"] == "7"
        assert result["section"] == "2"
        assert result["sentence"] is None

    def test_full_reference_with_sentence(self):
        """Test full reference: § 52 Absatz 1 Satz 1"""
        result = parse_law_reference("§ 52 Absatz 1 Satz 1")
        assert result is not None
        assert result["paragraph"] == "52"
        assert result["section"] == "1"
        assert result["sentence"] == "1"

    def test_article_reference(self):
        """Test article reference: Artikel 20 Absatz 3"""
        result = parse_law_reference("Artikel 20 Absatz 3")
        assert result is not None
        assert result["paragraph"] == "20"
        assert result["section"] == "3"
        assert result["sentence"] is None

    def test_article_abbreviated(self):
        """Test abbreviated article: Art. 1 Abs. 2"""
        result = parse_law_reference("Art. 1 Abs. 2")
        assert result is not None
        assert result["paragraph"] == "1"
        assert result["section"] == "2"
        assert result["sentence"] is None

    def test_article_without_dot(self):
        """Test article without dot: Art 1"""
        result = parse_law_reference("Art 1")
        assert result is not None
        assert result["paragraph"] == "1"
        assert result["section"] is None
        assert result["sentence"] is None

    def test_extra_whitespace(self):
        """Test that extra whitespace is handled correctly"""
        result = parse_law_reference("§  7   Absatz   2")
        assert result is not None
        assert result["paragraph"] == "7"
        assert result["section"] == "2"
        assert result["sentence"] is None

    def test_case_insensitive(self):
        """Test case insensitive matching"""
        result = parse_law_reference("§ 1 absatz 2 satz 3")
        assert result is not None
        assert result["paragraph"] == "1"
        assert result["section"] == "2"
        assert result["sentence"] == "3"

    def test_embedded_in_text(self):
        """Test parsing reference embedded in text"""
        text = "Siehe auch § 52 Absatz 1 Satz 1 für weitere Details"
        result = parse_law_reference(text)
        assert result is not None
        assert result["paragraph"] == "52"
        assert result["section"] == "1"
        assert result["sentence"] == "1"

    def test_invalid_reference_no_paragraph(self):
        """Test that invalid reference returns None"""
        result = parse_law_reference("Absatz 2")
        assert result is None

    def test_invalid_reference_empty_string(self):
        """Test that empty string returns None"""
        result = parse_law_reference("")
        assert result is None

    def test_invalid_reference_random_text(self):
        """Test that random text without reference returns None"""
        result = parse_law_reference("This is just some random text")
        assert result is None

    @pytest.mark.parametrize(
        "reference,expected_paragraph,expected_section,expected_sentence",
        [
            ("§ 1", "1", None, None),
            ("§ 8b", "8b", None, None),
            ("§ 7 Absatz 2", "7", "2", None),
            ("§ 52 Absatz 1 Satz 1", "52", "1", "1"),
            ("Artikel 20 Absatz 3", "20", "3", None),
            ("Art. 1 Abs. 2", "1", "2", None),
            ("§ 8a", "8a", None, None),
            ("§ 8c", "8c", None, None),
            ("§ 100 Absatz 1", "100", "1", None),
            ("§ 1 Satz 2", "1", None, "2"),
        ],
    )
    def test_parametrized_references(
        self, reference, expected_paragraph, expected_section, expected_sentence
    ):
        """Test multiple reference formats with parameterized tests"""
        result = parse_law_reference(reference)
        assert result is not None
        assert result["paragraph"] == expected_paragraph
        assert result["section"] == expected_section
        assert result["sentence"] == expected_sentence


class TestLawReferenceParserEdgeCases:
    """Edge cases and complex scenarios."""

    def test_multiple_references_in_text(self):
        """Test that only the first reference is parsed"""
        text = "Siehe § 1 und § 2 Absatz 3"
        result = parse_law_reference(text)
        assert result is not None
        assert result["paragraph"] == "1"

    def test_paragraph_with_multiple_letters(self):
        """Test paragraph with multiple letters (though rare)"""
        result = parse_law_reference("§ 8abc")
        # Our pattern only matches single letter, should not match
        # or match only up to first letter
        # Let's check what happens
        assert result is None or result["paragraph"] in ["8", "8a"]

    def test_very_long_paragraph_number(self):
        """Test with very long paragraph number"""
        result = parse_law_reference("§ 12345")
        assert result is not None
        assert result["paragraph"] == "12345"

    def test_section_without_paragraph(self):
        """Test section without paragraph marker should fail"""
        result = parse_law_reference("Absatz 2 Satz 1")
        assert result is None

    def test_german_umlaut_in_context(self):
        """Test reference with German umlauts in surrounding text"""
        text = "Nach § 1 Absatz 2 müssen Änderungen vorgenommen werden"
        result = parse_law_reference(text)
        assert result is not None
        assert result["paragraph"] == "1"
        assert result["section"] == "2"


class TestLawReferenceParserRealWorldExamples:
    """Real-world examples from German laws."""

    def test_bgb_reference(self):
        """Test typical BGB reference"""
        result = parse_law_reference("§ 433 Absatz 1 Satz 1")
        assert result is not None
        assert result["paragraph"] == "433"
        assert result["section"] == "1"
        assert result["sentence"] == "1"

    def test_gg_reference(self):
        """Test Grundgesetz article reference"""
        result = parse_law_reference("Artikel 20 Absatz 3")
        assert result is not None
        assert result["paragraph"] == "20"
        assert result["section"] == "3"

    def test_kstg_reference(self):
        """Test KStG reference with letter"""
        result = parse_law_reference("§ 8b Absatz 2")
        assert result is not None
        assert result["paragraph"] == "8b"
        assert result["section"] == "2"

    def test_hgb_reference_in_sentence(self):
        """Test HGB reference embedded in German sentence"""
        text = "Gemäß § 238 Absatz 1 des Handelsgesetzbuchs ist jeder Kaufmann verpflichtet"
        result = parse_law_reference(text)
        assert result is not None
        assert result["paragraph"] == "238"
        assert result["section"] == "1"


class TestLawReferenceParserWithNumberAndLetter:
    """Test cases for references with Nummer and Buchstabe."""

    def test_paragraph_with_number_and_letter(self):
        """Test § 10 Absatz 1 Nummer 4 Buchstabe a"""
        result = parse_law_reference("§ 10 Absatz 1 Nummer 4 Buchstabe a")
        assert result is not None
        assert result["paragraph"] == "10"
        assert result["section"] == "1"
        assert result["number"] == "4"
        assert result["letter"] == "a"
        assert result["sentence"] is None

    def test_article_with_letter(self):
        """Test Artikel 34 Absatz 6 Buchstabe a"""
        result = parse_law_reference("Artikel 34 Absatz 6 Buchstabe a")
        assert result is not None
        assert result["paragraph"] == "34"
        assert result["section"] == "6"
        assert result["number"] is None
        assert result["letter"] == "a"
        assert result["sentence"] is None

    def test_paragraph_with_buchstaben_plural(self):
        """Test § 1 Absatz 2 Buchstaben a (plural form)"""
        result = parse_law_reference("§ 1 Absatz 2 Buchstaben a")
        assert result is not None
        assert result["paragraph"] == "1"
        assert result["section"] == "2"
        assert result["letter"] == "a"

    def test_complex_reference_with_all_parts(self):
        """Test § 100b Absatz 2 Nummer 1 Buchstabe h"""
        result = parse_law_reference("§ 100b Absatz 2 Nummer 1 Buchstabe h")
        assert result is not None
        assert result["paragraph"] == "100b"
        assert result["section"] == "2"
        assert result["number"] == "1"
        assert result["letter"] == "h"

    def test_abbreviated_nummer(self):
        """Test § 10 Abs. 1 Nr. 4 Buchstabe a"""
        result = parse_law_reference("§ 10 Abs. 1 Nr. 4 Buchstabe a")
        assert result is not None
        assert result["paragraph"] == "10"
        assert result["section"] == "1"
        assert result["number"] == "4"
        assert result["letter"] == "a"

    def test_buchstaben_with_und(self):
        """Test § 1 Absatz 2 Buchstaben a und b (only captures first)"""
        result = parse_law_reference("§ 1 Absatz 2 Buchstaben a und b")
        assert result is not None
        assert result["paragraph"] == "1"
        assert result["section"] == "2"
        assert result["letter"] == "a"

    def test_buchstaben_with_bis(self):
        """Test § 1 Absatz 2 Buchstaben a bis c (only captures first)"""
        result = parse_law_reference("§ 1 Absatz 2 Buchstaben a bis c")
        assert result is not None
        assert result["paragraph"] == "1"
        assert result["section"] == "2"
        assert result["letter"] == "a"

    @pytest.mark.parametrize(
        "reference,expected_para,expected_sec,expected_num,expected_letter",
        [
            ("§ 10 Absatz 1 Nummer 4 Buchstabe a", "10", "1", "4", "a"),
            ("§ 26 Absatz 4 Buchstabe b", "26", "4", None, "b"),
            ("Artikel 6 Absatz 2 Buchstabe a", "6", "2", None, "a"),
            ("§ 100b Absatz 2 Nummer 1 Buchstabe h", "100b", "2", "1", "h"),
            ("§ 75 Absatz 1 Buchstabe d", "75", "1", None, "d"),
        ],
    )
    def test_parametrized_number_letter_references(
        self, reference, expected_para, expected_sec, expected_num, expected_letter
    ):
        """Test multiple number/letter formats with parameterized tests"""
        result = parse_law_reference(reference)
        assert result is not None
        assert result["paragraph"] == expected_para
        assert result["section"] == expected_sec
        assert result["number"] == expected_num
        assert result["letter"] == expected_letter


class TestLawReferenceParserWithLawCode:
    """Test cases for references with law codes (e.g., 'BGB § 26 Absatz 4')."""

    def test_simple_law_code_with_paragraph(self):
        """Test BGB § 26"""
        result = parse_law_reference("BGB § 26")
        assert result is not None
        assert result["law"] == "BGB"
        assert result["paragraph"] == "26"
        assert result["section"] is None

    def test_law_code_with_section(self):
        """Test BGB § 26 Absatz 4"""
        result = parse_law_reference("BGB § 26 Absatz 4")
        assert result is not None
        assert result["law"] == "BGB"
        assert result["paragraph"] == "26"
        assert result["section"] == "4"

    def test_law_code_with_letter_paragraph(self):
        """Test KStG § 8b Absatz 2"""
        result = parse_law_reference("KStG § 8b Absatz 2")
        assert result is not None
        assert result["law"] == "KStG"
        assert result["paragraph"] == "8b"
        assert result["section"] == "2"

    def test_law_code_with_full_reference(self):
        """Test HGB § 1 Absatz 2 Satz 1"""
        result = parse_law_reference("HGB § 1 Absatz 2 Satz 1")
        assert result is not None
        assert result["law"] == "HGB"
        assert result["paragraph"] == "1"
        assert result["section"] == "2"
        assert result["sentence"] == "1"

    def test_law_code_with_number_and_letter(self):
        """Test BGB § 10 Absatz 1 Nummer 4 Buchstabe a"""
        result = parse_law_reference("BGB § 10 Absatz 1 Nummer 4 Buchstabe a")
        assert result is not None
        assert result["law"] == "BGB"
        assert result["paragraph"] == "10"
        assert result["section"] == "1"
        assert result["number"] == "4"
        assert result["letter"] == "a"

    def test_various_law_codes(self):
        """Test different law code formats"""
        test_cases = [
            ("GmbHG § 13", "GmbHG", "13"),
            ("HGB § 238", "HGB", "238"),
            ("BGB § 433", "BGB", "433"),
            ("AktG § 1", "AktG", "1"),
        ]
        for reference, expected_law, expected_para in test_cases:
            result = parse_law_reference(reference)
            assert result is not None
            assert result["law"] == expected_law
            assert result["paragraph"] == expected_para

    def test_backward_compatibility_without_law_code(self):
        """Test that references without law code still work (law field is None)"""
        result = parse_law_reference("§ 1 Absatz 2")
        assert result is not None
        assert result["law"] is None
        assert result["paragraph"] == "1"
        assert result["section"] == "2"

    def test_law_code_with_artikel(self):
        """Test GG Artikel 1 Absatz 1"""
        result = parse_law_reference("GG Artikel 1 Absatz 1")
        assert result is not None
        assert result["law"] == "GG"
        assert result["paragraph"] == "1"
        assert result["section"] == "1"

    def test_law_code_embedded_in_text(self):
        """Test law code parsing when embedded in text"""
        text = "Nach BGB § 433 Absatz 1 hat der Verkäufer die Pflicht"
        result = parse_law_reference(text)
        assert result is not None
        assert result["law"] == "BGB"
        assert result["paragraph"] == "433"
        assert result["section"] == "1"

    @pytest.mark.parametrize(
        "reference,expected_law,expected_para,expected_section",
        [
            ("BGB § 26 Absatz 4", "BGB", "26", "4"),
            ("HGB § 1 Absatz 2", "HGB", "1", "2"),
            ("GmbHG § 13", "GmbHG", "13", None),
            ("KStG § 8b Absatz 2", "KStG", "8b", "2"),
            ("AktG § 100 Absatz 5", "AktG", "100", "5"),
            ("GG Artikel 20 Absatz 3", "GG", "20", "3"),
        ],
    )
    def test_parametrized_law_code_references(
        self, reference, expected_law, expected_para, expected_section
    ):
        """Test multiple law code formats with parameterized tests"""
        result = parse_law_reference(reference)
        assert result is not None
        assert result["law"] == expected_law
        assert result["paragraph"] == expected_para
        assert result["section"] == expected_section


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
