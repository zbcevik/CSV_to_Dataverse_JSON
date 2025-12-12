# -*- coding: utf-8 -*-
"""
Tests for CSV to Dataverse JSON Converter
"""

import os
import json
import tempfile
import pytest
import pandas as pd
from csv_to_dataverse_json import (
    ensure_required_fields,
    parse_compound,
    csv_to_dataverse_json,
    create_geospatial_block,
    create_socialscience_block,
)


class TestUTF8Encoding:
    """Test UTF-8 encoding handling"""

    def test_utf8_french_text_in_csv(self):
        """Test that French UTF-8 characters are correctly processed"""
        # Create a temporary CSV file with French text
        csv_content = """title,notesText
"Test Dataset","L'enquête a révélé que plusieurs ménages n'avaient pas reçu le courriel initial à cause d'une défaillance technique."
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            csv_path = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json_path = f.name

        try:
            # Convert CSV to JSON
            csv_to_dataverse_json(csv_path, json_path)

            # Read the output JSON
            with open(json_path, "r", encoding="utf-8") as f:
                result = json.load(f)

            # Check that the French text is preserved
            notes_field = None
            for field in result["datasetVersion"]["metadataBlocks"]["citation"][
                "fields"
            ]:
                if field["typeName"] == "notesText":
                    notes_field = field
                    break

            assert notes_field is not None
            assert (
                "L'enquête a révélé"
                in notes_field["value"]
            )
            assert "ménages" in notes_field["value"]
            assert "défaillance" in notes_field["value"]

        finally:
            # Cleanup
            os.unlink(csv_path)
            os.unlink(json_path)

    def test_utf8_special_characters(self):
        """Test various UTF-8 special characters"""
        special_chars = "Ñoño: café, naïve, 日本語, 中文, العربية"
        csv_content = f"""title,notesText
"Test Dataset","{special_chars}"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            csv_path = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json_path = f.name

        try:
            csv_to_dataverse_json(csv_path, json_path)

            with open(json_path, "r", encoding="utf-8") as f:
                result = json.load(f)

            notes_field = None
            for field in result["datasetVersion"]["metadataBlocks"]["citation"][
                "fields"
            ]:
                if field["typeName"] == "notesText":
                    notes_field = field
                    break

            assert notes_field is not None
            assert special_chars in notes_field["value"]

        finally:
            os.unlink(csv_path)
            os.unlink(json_path)


class TestParseCompound:
    """Test parse_compound function"""

    def test_parse_author_single(self):
        """Test parsing single author with name and affiliation"""
        compound_fields = {
            "author": ["authorName", "authorAffiliation"],
        }

        result = parse_compound(
            "John Smith; Harvard University", "author", compound_fields
        )

        assert len(result) == 1
        assert result[0]["authorName"]["value"] == "John Smith"
        assert result[0]["authorAffiliation"]["value"] == "Harvard University"

    def test_parse_author_multiple(self):
        """Test parsing multiple authors separated by pipe"""
        compound_fields = {
            "author": ["authorName", "authorAffiliation"],
        }

        result = parse_compound(
            "John Smith; Harvard University | Jane Doe; MIT", "author", compound_fields
        )

        assert len(result) == 2
        assert result[0]["authorName"]["value"] == "John Smith"
        assert result[0]["authorAffiliation"]["value"] == "Harvard University"
        assert result[1]["authorName"]["value"] == "Jane Doe"
        assert result[1]["authorAffiliation"]["value"] == "MIT"

    def test_parse_contact_with_email(self):
        """Test parsing dataset contact with name, affiliation, and email"""
        compound_fields = {
            "datasetContact": [
                "datasetContactName",
                "datasetContactAffiliation",
                "datasetContactEmail",
            ],
        }

        result = parse_compound(
            "Contact Person; University; contact@email.com",
            "datasetContact",
            compound_fields,
        )

        assert len(result) == 1
        assert result[0]["datasetContactName"]["value"] == "Contact Person"
        assert result[0]["datasetContactAffiliation"]["value"] == "University"
        assert result[0]["datasetContactEmail"]["value"] == "contact@email.com"

    def test_parse_empty_subfields(self):
        """Test parsing with empty subfields"""
        compound_fields = {
            "keyword": ["keywordValue", "keywordVocabulary"],
        }

        result = parse_compound("sample; | test;", "keyword", compound_fields)

        assert len(result) == 2
        assert result[0]["keywordValue"]["value"] == "sample"
        # keywordVocabulary should be omitted when empty
        assert "keywordVocabulary" not in result[0]


class TestEnsureRequiredFields:
    """Test ensure_required_fields function"""

    def test_adds_default_author_when_missing(self):
        """Test that default author is added when missing"""
        dataset_json = {
            "datasetVersion": {"metadataBlocks": {"citation": {"fields": []}}}
        }
        row = pd.Series({})
        defaults = {"author": "Default Author"}

        ensure_required_fields(dataset_json, row, defaults)

        fields = dataset_json["datasetVersion"]["metadataBlocks"]["citation"]["fields"]
        author_field = next((f for f in fields if f["typeName"] == "author"), None)

        assert author_field is not None
        assert author_field["value"][0]["authorName"]["value"] == "Default Author"

    def test_uses_depositor_as_fallback_author(self):
        """Test that depositor is used as fallback author"""
        dataset_json = {
            "datasetVersion": {"metadataBlocks": {"citation": {"fields": []}}}
        }
        row = pd.Series({"depositor": "Jane Depositor"})

        ensure_required_fields(dataset_json, row)

        fields = dataset_json["datasetVersion"]["metadataBlocks"]["citation"]["fields"]
        author_field = next((f for f in fields if f["typeName"] == "author"), None)

        assert author_field is not None
        assert author_field["value"][0]["authorName"]["value"] == "Jane Depositor"

    def test_adds_default_contact_email_when_missing(self):
        """Test that default contact email is added when missing"""
        dataset_json = {
            "datasetVersion": {"metadataBlocks": {"citation": {"fields": []}}}
        }
        row = pd.Series({})
        defaults = {"email": "default@example.com"}

        ensure_required_fields(dataset_json, row, defaults)

        fields = dataset_json["datasetVersion"]["metadataBlocks"]["citation"]["fields"]
        contact_field = next(
            (f for f in fields if f["typeName"] == "datasetContact"), None
        )

        assert contact_field is not None
        assert (
            contact_field["value"][0]["datasetContactEmail"]["value"]
            == "default@example.com"
        )

    def test_adds_default_description_when_missing(self):
        """Test that default description is added when missing"""
        dataset_json = {
            "datasetVersion": {"metadataBlocks": {"citation": {"fields": []}}}
        }
        row = pd.Series({})
        defaults = {"description": "Default description"}

        ensure_required_fields(dataset_json, row, defaults)

        fields = dataset_json["datasetVersion"]["metadataBlocks"]["citation"]["fields"]
        desc_field = next(
            (f for f in fields if f["typeName"] == "dsDescription"), None
        )

        assert desc_field is not None
        assert (
            desc_field["value"][0]["dsDescriptionValue"]["value"]
            == "Default description"
        )


class TestIntegration:
    """Integration tests for the full conversion process"""

    def test_full_conversion_with_all_fields(self):
        """Test complete conversion with various field types"""
        csv_content = """title,subtitle,"author: authorName; authorAffiliation",subject,"keyword: keywordValue; keywordVocabulary"
"Research Dataset","Subtitle","John Smith; University | Jane Doe; MIT","Social Sciences","research; | data;"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            csv_path = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json_path = f.name

        try:
            csv_to_dataverse_json(csv_path, json_path)

            with open(json_path, "r", encoding="utf-8") as f:
                result = json.load(f)

            # Verify top-level structure
            assert "id" in result
            assert "identifier" in result
            assert "datasetVersion" in result

            # Verify citation metadata
            fields = result["datasetVersion"]["metadataBlocks"]["citation"]["fields"]

            # Check title
            title_field = next((f for f in fields if f["typeName"] == "title"), None)
            assert title_field is not None
            assert title_field["value"] == "Research Dataset"

            # Check subtitle
            subtitle_field = next(
                (f for f in fields if f["typeName"] == "subtitle"), None
            )
            assert subtitle_field is not None
            assert subtitle_field["value"] == "Subtitle"

            # Check authors
            author_field = next((f for f in fields if f["typeName"] == "author"), None)
            assert author_field is not None
            assert len(author_field["value"]) == 2
            assert author_field["value"][0]["authorName"]["value"] == "John Smith"
            assert (
                author_field["value"][0]["authorAffiliation"]["value"] == "University"
            )

            # Check subject
            subject_field = next(
                (f for f in fields if f["typeName"] == "subject"), None
            )
            assert subject_field is not None
            assert "Social Sciences" in subject_field["value"]

        finally:
            os.unlink(csv_path)
            os.unlink(json_path)

    def test_conversion_with_defaults(self):
        """Test conversion with default values"""
        csv_content = """title
"Minimal Dataset"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            csv_path = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json_path = f.name

        try:
            defaults = {
                "author": "Test Author",
                "email": "test@example.com",
                "description": "Test description",
            }
            csv_to_dataverse_json(csv_path, json_path, defaults)

            with open(json_path, "r", encoding="utf-8") as f:
                result = json.load(f)

            fields = result["datasetVersion"]["metadataBlocks"]["citation"]["fields"]

            # Check that defaults were applied
            author_field = next((f for f in fields if f["typeName"] == "author"), None)
            assert author_field is not None
            assert author_field["value"][0]["authorName"]["value"] == "Test Author"

            contact_field = next(
                (f for f in fields if f["typeName"] == "datasetContact"), None
            )
            assert contact_field is not None
            assert (
                contact_field["value"][0]["datasetContactEmail"]["value"]
                == "test@example.com"
            )

        finally:
            os.unlink(csv_path)
            os.unlink(json_path)

    def test_multiple_rows_conversion(self):
        """Test converting CSV with multiple rows"""
        csv_content = """title,subject
"Dataset 1","Social Sciences"
"Dataset 2","Medicine, Health and Life Sciences"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            csv_path = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json_path = f.name

        try:
            csv_to_dataverse_json(csv_path, json_path)

            with open(json_path, "r", encoding="utf-8") as f:
                result = json.load(f)

            # Should be a list of datasets
            assert isinstance(result, list)
            assert len(result) == 2

            # Check first dataset
            fields1 = result[0]["datasetVersion"]["metadataBlocks"]["citation"][
                "fields"
            ]
            title1 = next((f for f in fields1 if f["typeName"] == "title"), None)
            assert title1["value"] == "Dataset 1"

            # Check second dataset
            fields2 = result[1]["datasetVersion"]["metadataBlocks"]["citation"][
                "fields"
            ]
            title2 = next((f for f in fields2 if f["typeName"] == "title"), None)
            assert title2["value"] == "Dataset 2"

        finally:
            os.unlink(csv_path)
            os.unlink(json_path)


class TestGeospatialBlock:
    """Test geospatial metadata block creation"""

    def test_create_geospatial_block_with_coverage(self):
        """Test creating geospatial block with geographic coverage"""
        row = pd.Series({"geographicCoverage": "Canada | United States"})

        result = create_geospatial_block(row)

        assert result is not None
        assert result["name"] == "geospatial"
        assert "fields" in result
        # Check that geographicCoverage field exists
        geo_field = next(
            (f for f in result["fields"] if f["typeName"] == "geographicCoverage"),
            None,
        )
        assert geo_field is not None
        assert len(geo_field["value"]) == 2
        assert geo_field["value"][0]["country"]["value"] == "Canada"

    def test_create_geospatial_block_returns_none_when_empty(self):
        """Test that None is returned when no geospatial fields present"""
        row = pd.Series({"title": "Test Dataset"})

        result = create_geospatial_block(row)

        assert result is None


class TestSocialscienceBlock:
    """Test social science metadata block creation"""

    def test_create_socialscience_block_with_unit(self):
        """Test creating social science block with unit of analysis"""
        row = pd.Series({"unitOfAnalysis": "Individual"})

        result = create_socialscience_block(row)

        assert result is not None
        assert result["name"] == "socialscience"
        assert "fields" in result
        # Check that unitOfAnalysis field exists
        unit_field = next(
            (f for f in result["fields"] if f["typeName"] == "unitOfAnalysis"), None
        )
        assert unit_field is not None
        assert "Individual" in unit_field["value"]
