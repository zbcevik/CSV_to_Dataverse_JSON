# CSV to Dataverse JSON Converter

**Simple tool to convert your Excel/CSV file into a format ready for uploading to Dataverse or Borealis data repositories.**

No coding experience needed! Just follow the simple steps below.

---

## What Does This Tool Do?

✅ Takes your dataset information from a **CSV file**  
✅ Automatically creates a **JSON file** that Dataverse/Borealis can understand  
✅ Fills in missing required information automatically  
✅ Ready to upload directly to your data repository  

---

## Installation (Do This First)

1. Open your terminal/command prompt
2. Go to the folder with this tool:
   ```bash
   cd /workspaces/csv_to_DDI_json
   ```

3. Install the required software:
   ```bash
   pip install -r requirements.txt
   ```

---

## Quick Start: Step by Step

### Step 1: Prepare Your CSV File
Create a CSV (Excel) file with your dataset information. See examples below in the **CSV Format** section.

### Step 2: Run One of These Commands

**Option 1: Super Simple (Uses Default Values)**
```bash
python csv_to_dataverse_json.py
```
This reads: `Csv_to_json - Citation.csv`  
Creates: `output_metadata.json`

---

**Option 2: Add Your Own Author, Email & Description (✓ Tested and Works!)**
```bash
python csv_to_dataverse_json.py "Csv_to_json - Citation.csv" "my_dataset.json" \
  --default-author "Your Name" \
  --default-email "your.email@organization.edu" \
  --default-description "What is this dataset about?"
```

**What to change:**
- `"Your Name"` → Your name
- `"your.email@organization.edu"` → Your email
- `"What is this dataset about?"` → Brief description of your dataset

**Example:**
```bash
python csv_to_dataverse_json.py "Csv_to_json - Citation.csv" "my_dataset.json" \
  --default-author "Dr. Jane Smith" \
  --default-email "jane.smith@university.edu" \
  --default-description "Survey data from 2024 research project"
```

---

**Option 3: Use Environmental Variables (Save Your Defaults)**
```bash
export DATAVERSE_DEFAULT_AUTHOR="Your Name"
export DATAVERSE_DEFAULT_EMAIL="your.email@organization.edu"
export DATAVERSE_DEFAULT_DESCRIPTION="Your description"

python csv_to_dataverse_json.py input.csv output.json
```

---

**Option 4: Use Custom CSV File**
```bash
python csv_to_dataverse_json.py your_file.csv your_output.json
```

---

### Step 3: Check Your Output
Your new file will be created (e.g., `my_dataset.json` or `output_metadata.json`).

To view it:
```bash
cat my_dataset.json
```

---

## Understanding the Options

| What to Do | Command |
|-----------|---------|
| Simple conversion with defaults | `python csv_to_dataverse_json.py` |
| **Add your info** (Recommended) | `python csv_to_dataverse_json.py input.csv output.json --default-author "Name" --default-email "email@org.edu" --default-description "Description"` |
| Custom input/output files | `python csv_to_dataverse_json.py my_data.csv result.json` |

---

## How Does the Tool Fill Missing Information?

When your CSV is missing required fields like author name, contact email, or description:

1. **First:** Uses values from your CSV (if you provided them)
2. **Second:** Uses the values you gave with `--default-author`, `--default-email`, etc.
3. **Third:** Uses environment variables you set earlier
4. **Last:** Uses generic placeholders like "Unknown Author" or "No description provided"

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

### I get an error when I run the command
**Solution 1:** Make sure you're in the right folder:
```bash
cd /workspaces/csv_to_DDI_json
```

**Solution 2:** Check that `Csv_to_json - Citation.csv` exists in the folder

**Solution 3:** Make sure you installed the required software:
```bash
pip install -r requirements.txt
```

### The output file is empty or missing values
- Check that your CSV file has the same column names as shown in the examples
- Make sure column names are spelled exactly right
- Empty cells in your CSV are automatically skipped (this is fine)

### I want to use my own CSV file name
Use this command:
```bash
python csv_to_dataverse_json.py your_file.csv output.json
```
Change `your_file.csv` to your actual filename.

### I need help with dates
- Dates should be in this format: `YYYY-MM-DD` (example: `2024-12-11`)
- If you just have the year, that's fine too: `2024`

---

## What's Included

- `csv_to_dataverse_json.py` - Main tool (do not edit)
- `Csv_to_json - Citation.csv` - Example CSV file
- `requirements.txt` - List of required software
- `README.md` - This file (instructions)
- `TEMPLATE_CSV_WITH_ALL_COLUMNS.csv` - Full template with all possible fields

---

## Questions or Issues?

See the `GETTING_STARTED.md` file for more detailed instructions, or check the `CHANGES.md` file to see what's new in this version.
