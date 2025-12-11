# CSV to Dataverse DDI JSON Converter

Convert CSV metadata files to complete Dataverse/Borealis-compatible DDI JSON format with all required system fields, metadata blocks, and dataset information.

## Key Features

✅ **Full Dataverse JSON Structure** - Generates complete JSON with top-level fields, datasetVersion, and all metadata blocks  
✅ **System Fields** - Automatically generates or accepts dataset IDs, identifiers, persistent URLs  
✅ **License Information** - Includes CC0 license (customizable)  
✅ **Multiple Metadata Blocks** - Citation, Geospatial, Social Science support  
✅ **Flexible Input** - Use defaults or provide custom values via CSV  
✅ **DDI Compatible** - Ready for upload to Dataverse and Borealis

## Installation

1. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

1. **Prepare your CSV file** with the proper column headers (see CSV Format section below)

2. **Run the conversion script:**
   ```bash
   python csv_to_dataverse_json.py
   ```

   This will:
   - Read `Csv_to_json - Citation.csv`
   - Generate `output_metadata.json`

### Command Line Options

The script supports command line arguments for flexible usage:

```bash
python csv_to_dataverse_json.py [input.csv] [output.json] [options]
```

**Default behavior** (if no arguments provided):
```bash
python csv_to_dataverse_json.py
# Reads: Csv_to_json - Citation.csv
# Outputs: output_metadata.json
```

**Custom file paths:**
```bash
python csv_to_dataverse_json.py my_data.csv my_output.json
```

### Customizing Default Placeholders

When required fields (author name, contact email, dataset description) are missing from your CSV, the script automatically fills them with sensible defaults. You can customize these defaults using:

#### Option 1: Command Line Arguments
```bash
python csv_to_dataverse_json.py input.csv output.json \
  --default-author "Prof. Jane Smith" \
  --default-email "jane.smith@university.edu" \
  --default-description "My custom dataset description"
```

#### Option 2: Environment Variables
```bash
export DATAVERSE_DEFAULT_AUTHOR="Prof. Jane Smith"
export DATAVERSE_DEFAULT_EMAIL="jane.smith@university.edu"
export DATAVERSE_DEFAULT_DESCRIPTION="My custom dataset description"

python csv_to_dataverse_json.py input.csv output.json
```

#### Option 3: CSV Values Take Precedence
If your CSV contains values for `author`, `datasetContact`, or `dsDescription`, they will be used **instead** of defaults:

```csv
title,author,datasetContact,dsDescription
"My Dataset","Dr. John Smith; University X","Contact Person; Org; contact@email.com","Data collected in 2024"
```

**Priority order** (highest to lowest):
1. Values from CSV (if present)
2. Command line arguments (--default-*)
3. Environment variables (DATAVERSE_DEFAULT_*)
4. Hard-coded defaults (generic placeholders)

## CSV Format

### System Fields (Top-Level - Optional, have defaults)

These fields define the dataset at the system level. If not provided, the script generates sensible defaults:

- `id` - Dataset ID (auto-generated if missing: 1000+row_index)
- `identifier` - Persistent identifier (auto-generated if missing: FK2/random)
- `protocol` - Protocol for identifier, typically `doi` or `hdl` (default: `doi`)
- `authority` - Authority prefix, e.g., `10.70122` (default: `10.70122`)
- `publisher` - Publisher name (default: `Dataverse`)
- `publicationDate` - Publication date in YYYY-MM-DD format (default: today)
- `datasetType` - Type of dataset (default: `dataset`)
- `versionId` - Version ID (auto-generated if missing: 2000+row_index)
- `versionNumber` - Version number (default: `1`)
- `versionMinorNumber` - Minor version (default: `0`)
- `versionState` - Version state: `DRAFT`, `RELEASED`, etc. (default: `DRAFT`)
- `latestVersionPublishingState` - Publishing state (default: `DRAFT`)
- `storageIdentifier` - Storage location (auto-generated if missing)
- `UNF` - Universal Numeric Fingerprint (optional)
- `lastUpdateTime` - Last update timestamp (auto-generated)
- `createTime` - Creation timestamp (auto-generated)
- `citationDate` - Citation date (default: today)
- `termsOfUse` - Terms of use text (optional)
- `citationRequirements` - Citation requirements (optional)
- `conditions` - Access conditions (optional)
- `termsOfAccess` - Terms of access (optional)
- `fileAccessRequest` - Allow file access requests: `true` or `false` (default: `true`)

### License Information (Nested in datasetVersion)

- `licenseName` - License name (default: `CC0 1.0`)
- `licenseUri` - License URI (default: CC0 URI)
- `licenseIconUri` - License icon URL (default: CC0 icon)
- `rightsIdentifier` - Rights identifier (default: `CC0-1.0`)
- `rightsIdentifierScheme` - Scheme name (default: `SPDX`)
- `schemeUri` - Scheme URI (default: SPDX URL)
- `languageCode` - Language code (default: `en`)

### Citation Metadata Fields

Your CSV should have the following column headers for citation metadata:

#### Basic Fields
- `title` - Dataset title
- `subtitle` - Dataset subtitle
- `alternativeTitle` - Alternative title (use `|` for multiple values)
- `notesText` - Additional notes
- `language` - Language (use `|` for multiple; controlled vocabulary)

### People/Organizations (Compound Fields)
Use semicolon (`;`) to separate subfields and pipe (`|`) for multiple entries:

- `author: authorName; authorAffiliation` 
  - Example: `John Smith; Harvard University | Jane Doe; MIT`

- `datasetContact: datasetContactName; datasetContactAffiliation; datasetContactEmail`
  - Example: `Contact Person; University; contact@email.com`

- `producer: producerName; producerAffiliation; producerAbbreviation`
  - Example: `Statistics Canada; Statistics; StatCan`

- `contributor: contributorType; contributorName`
  - Example: `Researcher; John Smith`

### Description Fields
- `dsDescription: dsDescriptionValue; dsDescriptionDate`
  - Example: `This is a dataset description; 2025-01-01`

### Keywords & Subjects
- `subject` - Subject category (use `|` for multiple; controlled vocabulary)
  - Example: `Social Sciences | Medicine, Health and Life Sciences`

- `keyword: keywordValue; keywordVocabulary`
  - Example: `sample; | test; | data`

- `topicClassification: topicClassValue; topicClassVocab`
  - Example: `survey; | statistics;`

### Dates
- `productionDate` - Year produced
- `distributionDate` - Year distributed
- `dateOfDeposit` - Deposit date
- `timePeriodCovered: timePeriodCoveredStart; timePeriodCoveredEnd`
  - Example: `2025-01-01; 2025-12-31`

- `dateOfCollection: dateOfCollectionStart; dateOfCollectionEnd`
  - Example: `2024-01-01; 2024-12-31`

### Data Information
- `kindOfData` - Type of data (use `|` for multiple)
  - Example: `Quantitative | Qualitative`

- `software: softwareName; softwareVersion`
  - Example: `R; 4.0.0`

- `series: seriesName; seriesInformation`
  - Example: `Annual Statistics; Volume 5`

### Related Materials
- `relatedMaterial` - Related materials (use `|` for multiple)
- `relatedDatasets` - Related datasets (use `|` for multiple)
- `otherReferences` - Other references (use `|` for multiple)
- `dataSources` - Data sources (use `|` for multiple)

### Source Information
- `originOfSources` - Origin of sources
- `characteristicOfSources` - Characteristics of sources
- `accessToSources` - Access to sources

### Publication Information
- `publication: publicationRelationType; publicationCitation; publicationIDType; publicationIDNumber`
  - Example: `IsCitedBy; Smith et al. 2024; DOI; 10.1234/example`

### Funding & Distribution
- `grantNumber: grantNumberAgency; grantNumberValue`
  - Example: `NSERC; GRANT-12345`

- `distributor: distributorName; distributorAffiliation; distributorAbbreviation; distributorURL`

### Other Fields
- `depositor` - Person depositing the dataset
- `doi` - Digital Object Identifier (optional, for reference)
- `citation` - Full citation (optional, for reference)

## Example CSV Entry

```csv
title,author: authorName; authorAffiliation,subject,keyword: keywordValue; keywordVocabulary,dsDescription: dsDescriptionValue; dsDescriptionDate
"My Research Dataset","John Smith; University of Toronto | Jane Doe; MIT","Social Sciences | Computer Science","research; | data; | survey;","This dataset contains survey responses; 2025"
```

## Output JSON Format

The script generates **complete Dataverse-compatible DDI JSON** with all system fields, version information, and metadata blocks:

```json
{
  "id": 1000,
  "identifier": "FK2/DBEC899D",
  "persistentUrl": "https://doi.org/10.70122/FK2/DBEC899D",
  "protocol": "doi",
  "authority": "10.70122",
  "separator": "/",
  "publisher": "Dataverse",
  "publicationDate": "2025-12-11",
  "storageIdentifier": "s3://10.70122/FK2/DBEC899D",
  "datasetType": "dataset",
  "datasetVersion": {
    "id": 2000,
    "datasetId": 1000,
    "datasetPersistentId": "doi:10.70122/FK2/DBEC899D",
    "datasetType": "dataset",
    "storageIdentifier": "s3://10.70122:...",
    "versionNumber": 1,
    "internalVersionNumber": 1,
    "versionMinorNumber": 0,
    "versionState": "DRAFT",
    "latestVersionPublishingState": "DRAFT",
    "UNF": "",
    "lastUpdateTime": "2025-12-11T16:49:19Z",
    "releaseTime": "",
    "createTime": "2025-12-11T16:49:19Z",
    "publicationDate": "2025-12-11",
    "citationDate": "2025-12-11",
    "termsOfUse": "",
    "citationRequirements": "",
    "conditions": "",
    "termsOfAccess": "",
    "license": {
      "name": "CC0 1.0",
      "uri": "http://creativecommons.org/publicdomain/zero/1.0",
      "iconUri": "https://licensebuttons.net/p/zero/1.0/88x31.png",
      "rightsIdentifier": "CC0-1.0",
      "rightsIdentifierScheme": "SPDX",
      "schemeUri": "https://spdx.org/licenses/",
      "languageCode": "en"
    },
    "fileAccessRequest": true,
    "metadataBlocks": {
      "citation": {
        "displayName": "Citation Metadata",
        "name": "citation",
        "fields": [
          {
            "typeName": "title",
            "multiple": false,
            "typeClass": "primitive",
            "value": "My Research Dataset"
          },
          {
            "typeName": "author",
            "multiple": true,
            "typeClass": "compound",
            "value": [
              {
                "authorName": {
                  "typeName": "authorName",
                  "multiple": false,
                  "typeClass": "primitive",
                  "value": "John Smith"
                },
                "authorAffiliation": {
                  "typeName": "authorAffiliation",
                  "multiple": false,
                  "typeClass": "primitive",
                  "value": "Harvard University"
                }
              }
            ]
          }
        ]
      },
      "geospatial": {...},
      "socialscience": {...}
    },
    "files": [...]
  },
  "citation": "Full citation string (optional)"
}
```

## Importing into Dataverse/Borealis

1. **In Dataverse:**
   - Go to your dataset → Edit → Metadata
   - Use the JSON API endpoint or direct metadata upload
   - POST the generated JSON to: `/api/datasets/{id}/metadata`

2. **In Borealis:**
   - Follow similar import procedures for DDI JSON formats

## Troubleshooting

### "File not found" error
- Ensure your CSV file is in the same directory as the script, or provide the full path

### Missing or incorrect values in output
- Check that your CSV headers exactly match the field names
- Verify semicolon and pipe delimiters are used correctly
- Empty cells are automatically skipped

### Date format issues
- Dates are converted to year-only format (YYYY) by default
- Ensure dates contain a valid 4-digit year

## File Structure

```
csv_to_DDI_json/
├── csv_to_dataverse_json.py      # Main conversion script
├── Csv_to_json - Citation.csv    # Input CSV file
├── output_metadata.json           # Generated output (after running)
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── samplemetadata.json            # Reference sample output
```

## License

This project is open source and available for research and data curation purposes.
