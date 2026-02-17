# CSV to Dataverse JSON Converter

Small utility to convert CSV metadata into Dataverse-compatible JSON using the metadata
block definitions in `all-metadata-blocks.json`.

## 📦 Installation

It's recommended to use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🚀 Usage

Basic conversion:

```bash
.venv/bin/python csv_to_dataverse_json.py input.csv output.json --metadef all-metadata-blocks.json
```

### Optional flags

- `--metadef <path>` – path to metadata block definitions (default: `all-metadata-blocks.json`).
- `--defaults <json_file>` – JSON file containing default field values for empty cells.
- `--verbose` – print detailed processing information.

## 📝 CSV Format Guidelines

Headers must follow the `block:field` convention, such as:

- `citation:title`
- `geospatial:geographicCoverage`

### Compound fields

- Use `|` to separate multiple entries.
- Within a single column, separate child values with `;`.

Example (parent-column style):

```
Doe, John;University X;ORCID;0000-0001-2345-6789 | Roe, Jane;Org2;ORCID;0000-0009-8765-4321
```

Alternatively, specify explicit child columns:

```
citation:author.authorName,citation:author.authorAffiliation
```

The script will detect these and assemble compound values automatically. Explicit child
columns take precedence over the parent-column style when both are present.

## 📁 Example Files in This Repo

- `csv_to_dataverse_json.py`: main converter script.
- `all-metadata-blocks.json`: Dataverse metadata block definitions used for field mapping.
- `all_blocks_complete.csv`: generated CSV containing every field/child field defined in
  the metadata blocks.
- `all_blocks_complete.json`: JSON output created from `all_blocks_complete.csv`.

## 🔧 Quick Test

Convert the comprehensive CSV and inspect the output with `jq`:

```bash
.venv/bin/python csv_to_dataverse_json.py all_blocks_complete.csv all_blocks_complete.json \
    --metadef all-metadata-blocks.json --verbose
jq . all_blocks_complete.json | less
```

## 🧩 Next Steps (optional)

- Validate `all_blocks_complete.json` against a Dataverse schema.
- Generate multiple sample rows with richer, realistic values.
- Add unit tests covering common CSV patterns and edge cases.

---

**License:** see `LICENSE`.
