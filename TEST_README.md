# Test Documentation

This document describes the test suite for the CSV to Dataverse JSON converter.

## Running Tests

### Prerequisites

Install the required test dependencies:

```bash
pip install --break-system-packages pytest pandas
```

Or install all dev dependencies:

```bash
pip install --break-system-packages -e ".[dev]"
```

### Basic Test Commands

**Run all tests:**
```bash
python -m pytest test_csv_to_dataverse_json.py
```

**Run with verbose output:**
```bash
python -m pytest test_csv_to_dataverse_json.py -v
```

**Run with coverage report:**
```bash
python -m pytest test_csv_to_dataverse_json.py --cov=csv_to_dataverse_json
```

**Run a specific test class:**
```bash
python -m pytest test_csv_to_dataverse_json.py::TestUTF8Encoding -v
```

**Run a specific test:**
```bash
python -m pytest test_csv_to_dataverse_json.py::TestIntegration::test_full_conversion_with_all_fields -v
```

## Test Structure

The test suite is organized into the following test classes:

### TestUTF8Encoding
Tests UTF-8 character encoding handling.

- `test_utf8_french_text_in_csv` - Verifies French accented characters are preserved
- `test_utf8_special_characters` - Tests various special characters (Japanese, Chinese, Arabic, etc.)

### TestParseCompound
Tests the `parse_compound()` function for parsing compound field values.

- `test_parse_author_single` - Single author with name and affiliation
- `test_parse_author_multiple` - Multiple authors separated by pipe
- `test_parse_contact_with_email` - Contact with name, affiliation, and email
- `test_parse_empty_subfields` - Handling of empty subfield values

### TestEnsureRequiredFields
Tests the `ensure_required_fields()` function for adding missing required fields.

- `test_adds_default_author_when_missing` - Adds default author when none provided
- `test_uses_depositor_as_fallback_author` - Uses depositor field as fallback
- `test_adds_default_contact_email_when_missing` - Adds default contact email
- `test_adds_default_description_when_missing` - Adds default description

### TestIntegration
Integration tests for the complete conversion process.

- `test_full_conversion_with_all_fields` - Tests conversion with various field types including custom subfield headers
- `test_conversion_with_defaults` - Tests conversion with default values
- `test_multiple_rows_conversion` - Tests converting CSV with multiple rows

### TestGeospatialBlock
Tests the `create_geospatial_block()` function.

- `test_create_geospatial_block_with_coverage` - Creates geospatial block with geographic coverage
- `test_create_geospatial_block_returns_none_when_empty` - Returns None when no geospatial fields present

### TestSocialscienceBlock
Tests the `create_socialscience_block()` function.

- `test_create_socialscience_block_with_unit` - Creates social science block with unit of analysis

## Test Features

### Custom Subfield Headers
The converter supports CSV headers with custom subfield specifications:

```csv
"author: authorName; authorAffiliation","keyword: keywordValue; keywordVocabulary"
```

This allows you to specify which subfields to use for compound fields directly in the CSV header.

### Temporary Files
Tests use Python's `tempfile` module to create temporary CSV and JSON files, which are automatically cleaned up after each test.

### UTF-8 Encoding
All tests verify that UTF-8 encoding is properly preserved throughout the conversion process.

## Expected Test Results

When all tests pass, you should see:

```
============================= test session starts ==============================
...
test_csv_to_dataverse_json.py::TestUTF8Encoding::test_utf8_french_text_in_csv PASSED
test_csv_to_dataverse_json.py::TestUTF8Encoding::test_utf8_special_characters PASSED
...
============================== 16 passed in X.XXs ==============================
```

## Troubleshooting

**Import errors:**
Make sure `csv_to_dataverse_json.py` is in the same directory as the test file, or install the package in development mode:
```bash
pip install --break-system-packages -e .
```

**Missing dependencies:**
Install pytest and pandas:
```bash
pip install --break-system-packages pytest pandas
```

**Permission errors:**
If you get permission errors, use the `--break-system-packages` flag or create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install pytest pandas
```

## Writing New Tests

To add new tests:

1. Create a new test class or add to an existing one
2. Test method names must start with `test_`
3. Use descriptive docstrings to explain what the test does
4. Clean up any temporary files in a `finally` block
5. Use assertions to verify expected behavior

Example:
```python
class TestMyFeature:
    """Test description"""

    def test_my_new_feature(self):
        """Test that my feature works correctly"""
        # Arrange
        input_data = "test"

        # Act
        result = my_function(input_data)

        # Assert
        assert result == "expected_output"
```
