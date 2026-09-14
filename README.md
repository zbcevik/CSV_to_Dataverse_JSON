# CSV to Dataverse JSON

Convert CSV metadata into JSON for Borealis or another Dataverse installation.
A quick upload script is also included so you can test generated metadata by
creating draft datasets in your collection. Sample CSV inputs and JSON outputs
are provided to try the workflow.

## Tools in this repository

- `scripts/csv_to_dataverse_json.py` converts CSV rows using metadata field definitions.
- `scripts/upload_metadata_to_borealis.py` submits metadata as new draft datasets.

The workflow is: prepare CSV metadata, convert it to JSON, preview the dataset
information, then upload to the selected collection.

## Installation

Requires Python 3 and pandas. Development checks use Python 3.13.
Run commands from the repository root. Install dependencies in your preferred
Python environment:

```bash
python3 -m pip install -r requirements.txt
```

The upload tool uses only the Python standard library.

## Configuration

Copy `config.sample.ini` to `config.ini` if you do not already have a local
configuration, then enter your destination and credentials:

```ini
[dataverse]
server_url = https://demo.borealisdata.ca
collection = YOUR_COLLECTION_ALIAS
api_key =
```

Leave `api_key` blank if you want to enter it at a hidden terminal prompt during upload.
`config.ini` is excluded from Git. Keep the public template free of credentials.

The uploader reads the root `config.ini` regardless of the working directory.
Use `--config path/to/config.ini` for another configuration. `--server-url` and
`--collection` override configured values; missing values are requested in the
terminal. `DATAVERSE_API_TOKEN` overrides the configured API key.

## Convert metadata

Replace `your_metadata.csv` with your CSV path and `your_metadata.json` with the
output filename you want to create. These are placeholders, not supplied files.

```bash
python3 scripts/csv_to_dataverse_json.py \
  your_metadata.csv your_metadata.json
```

The converter uses `Examples/metadata/all-metadata-blocks.json` by default.
Use `--metadef path/to/definitions.json` to select another definitions file.
Each CSV row represents one dataset. A single row produces a JSON object;
multiple rows produce an array. Existing output files are overwritten.

CSV headers use `block:field` notation, such as `citation:title`. Use `|` for
multiple values where permitted and `;` for child values in compound fields:

```text
Example Author;Example University;ORCID;0000-0001-1111-1111
```

Child order follows the metadata definitions. Single-choice fields accept one
value. Controlled vocabulary values must match the destination installation.

## Upload draft datasets

Replace `your_metadata.json` with your generated file, or use the supplied
`Examples/all_blocks_expanded.json` to test an upload of three sample datasets.
After uploading, open the destination collection to inspect the draft metadata.

Preview locally without sending requests:

```bash
python3 scripts/upload_metadata_to_borealis.py your_metadata.json --dry-run
```

Create drafts using the configured server and collection:

```bash
python3 scripts/upload_metadata_to_borealis.py your_metadata.json --apply
```

The expanded example contains three datasets. Each submission creates a new draft;
rerunning the command can create duplicates. The tool does not publish drafts or
update existing datasets. It submits metadata blocks only; generated identifiers,
file records, license defaults and access policies are omitted.

Local checks verify required field presence. The server validates vocabulary
values, metadata blocks and collection requirements. On failure, the upload stops;
previous successful drafts remain. Check the collection before retrying after a
timeout or uncertain response.

## Example files

Examples contain synthetic data. Not every example is ready for upload.

| Files | Purpose |
| --- | --- |
| `Examples/all_blocks_example.*` | Minimal coverage of eight blocks; lacks required creation fields |
| `Examples/all_blocks_expanded.*` | Three datasets with compound and repeated values; used for demo uploads |
| `Examples/all_blocks_full.*` | Parent and explicit child-column examples |
| `Examples/all_blocks_complete.*` | Broad field coverage with placeholder values |
| `Examples/metadata/all-metadata-blocks.json` | Field definitions used by the converter |

Metadata requirements can differ between Dataverse installations. Check the
converted metadata against your destination before uploading. Generated JSON
files are local output and can be recreated from your CSV inputs.

## Limitations

Explicit child columns currently require the corresponding parent column to exist.
Use parent-column formatting for repeated compound entries. Unknown blocks may be
silently skipped, and missing identifiers or some dates receive generated defaults.
Inspect conversion results before uploading.

## License

[MIT](LICENSE).

## Reference

[Dataverse dataset creation API](https://guides.dataverse.org/en/latest/api/native-api.html#create-a-dataset-in-a-dataverse-collection).
