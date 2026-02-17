#!/usr/bin/env python3
"""
General CSV to Dataverse JSON converter.

Reads `all-metadata-blocks.json` to understand metadata block and field
definitions. CSV headers should use `block:field` notation (for example
`citation:author` or `geospatial:geographicCoverage`). Compound field
values use `|` to separate multiple entries and `;` to separate child
values (for example: "Name;Affiliation;ORCID | Name2;Aff2;ORCID2").

Usage:
  python csv_to_dataverse_json.py input.csv output.json

This script follows the patterns in the example `csv_to_dataverse_json (1).py`
but automatically uses `all-metadata-blocks.json` to build metadata blocks.
"""

import argparse
import json
import os
import re
from datetime import datetime

import pandas as pd


def load_metadata_blocks(def_path="all-metadata-blocks.json"):
    with open(def_path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    blocks = {}
    for key, val in raw.items():
        # file format: block -> {"status":..., "data":{...}}
        if isinstance(val, dict) and "data" in val:
            blocks[key] = val["data"]
        elif isinstance(val, dict) and "fields" in val:
            blocks[key] = val
        else:
            blocks[key] = val
    return blocks


def format_date_to_year(date_value):
    if pd.isna(date_value) or not date_value:
        return datetime.now().strftime("%Y")
    s = str(date_value)
    m = re.search(r'\b(19|20)\d{2}\b', s)
    return m.group(0) if m else datetime.now().strftime("%Y")


def parse_compound_field(value, field_def):
    """
    Parse compound field values. `value` can contain multiple entries
    separated by `|`. Each entry contains sub-values separated by `;`.
    `field_def` is the field definition from all-metadata-blocks.json and
    may include `childFields` describing child field names and order.
    """
    if pd.isna(value) or value == "":
        return []

    child_map = []
    if field_def and isinstance(field_def, dict) and "childFields" in field_def:
        # childFields is a dict; preserve insertion order when available
        child_map = list(field_def["childFields"].keys())

    entries = [e.strip() for e in str(value).split("|") if e.strip()]
    result = []
    for entry in entries:
        parts = [p.strip() for p in entry.split(";")]
        obj = {}
        for i, child in enumerate(child_map):
            if i < len(parts) and parts[i] and parts[i].lower() != 'nan':
                val = parts[i]
                if child.lower().endswith('date'):
                    val = format_date_to_year(val)
                obj[child] = {"typeName": child, "multiple": False, "typeClass": "primitive", "value": val}
        if obj:
            result.append(obj)
    return result


def build_field_entry(field_name, raw_value, block_def):
    """Build a Dataverse-style field entry using the block definition."""
    if block_def is None:
        return None

    field_defs = block_def.get("fields", {})
    fdef = field_defs.get(field_name)
    if not fdef:
        # unknown field - treat as primitive single
        return {"typeName": field_name, "multiple": False, "typeClass": "primitive", "value": str(raw_value)}

    type_class = fdef.get("typeClass") or fdef.get("type") or "primitive"
    multiple = fdef.get("multiple", False)

    entry = {"typeName": field_name, "multiple": multiple, "typeClass": type_class}

    if type_class == "compound":
        entry["value"] = parse_compound_field(raw_value, fdef)
    elif type_class == "controlledVocabulary":
        # split by pipe for multiple terms
        if multiple:
            entry["value"] = [v.strip() for v in str(raw_value).split("|") if v.strip()]
        else:
            entry["value"] = [v.strip() for v in str(raw_value).split("|") if v.strip()]
    else:
        if multiple:
            entry["value"] = [v.strip() for v in str(raw_value).split("|") if v.strip()]
        else:
            # some special date handling
            if field_name.lower() in ("productiondate", "distributiondate", "dateofdeposit", "productiondate"):
                entry["value"] = format_date_to_year(raw_value)
            else:
                entry["value"] = str(raw_value)

    return entry if entry.get("value") not in (None, [], "") else None


def csv_to_dataverse_json(csv_path, out_path, metadata_def_path="all-metadata-blocks.json", defaults=None, verbose=False):
    blocks = load_metadata_blocks(metadata_def_path)

    df = pd.read_csv(csv_path)
    results = []

    # Build mapping of explicit child-columns: (block, field) -> ordered list of (childName, colName)
    child_columns = {}
    for col in df.columns:
        if ':' not in col:
            continue
        block, rest = col.split(':', 1)
        if '.' in rest:
            field, child = rest.split('.', 1)
            child_columns.setdefault((block, field), []).append((child, col))

    # Order child columns according to metadata definition when possible
    for (block, field), lst in list(child_columns.items()):
        block_def = blocks.get(block, {})
        fdef = (block_def.get('fields') or {}).get(field) if isinstance(block_def, dict) else None
        if fdef and isinstance(fdef, dict) and 'childFields' in fdef and isinstance(fdef['childFields'], dict):
            order = list(fdef['childFields'].keys())
            ordered = []
            for cname in order:
                for child_name, colname in lst:
                    if child_name == cname:
                        ordered.append((child_name, colname))
                        break
            # append any remaining columns not in definition
            for child_name, colname in lst:
                if all(colname != c for _, c in ordered):
                    ordered.append((child_name, colname))
            child_columns[(block, field)] = ordered
        else:
            # keep provided order
            child_columns[(block, field)] = lst

    for idx, row in df.iterrows():
        # simple id/identifier generation
        dataset_id = int(row.get("id", 0)) if row.get("id") and not pd.isna(row.get("id")) else 1000 + idx
        identifier = str(row.get("identifier")) if row.get("identifier") and not pd.isna(row.get("identifier")) else f"FK2/{os.urandom(4).hex().upper()}"

        dataset = {
            "id": dataset_id,
            "identifier": identifier,
            "persistentUrl": f"doi:{identifier}",
            "protocol": str(row.get('protocol', 'doi')),
            "authority": str(row.get('authority', '')),
            "datasetVersion": {"metadataBlocks": {}}
        }

        metadata_blocks = {}

        # iterate columns named like block:field (skip explicit child columns)
        for col in df.columns:
            if ':' not in col:
                continue
            block_name, field_name = col.split(':', 1)
            # skip explicit child column headers like block:field.child
            if '.' in field_name:
                continue

            # If explicit child columns exist for this compound field, build raw_value from them
            raw = None
            if (block_name, field_name) in child_columns:
                parts = []
                for child_name, colname in child_columns[(block_name, field_name)]:
                    v = row.get(colname)
                    parts.append('' if pd.isna(v) else str(v).strip())
                # join using semicolon as compound parser expects
                raw = ';'.join(parts)
                # if all parts empty, treat as missing
                if all(p == '' for p in parts):
                    raw = None
            else:
                raw = row.get(col)

            if pd.isna(raw) or raw is None or raw == "":
                continue

            block_def = blocks.get(block_name)
            if block_def is None:
                # skip unknown blocks
                continue

            field_entry = build_field_entry(field_name, raw, block_def)
            if not field_entry:
                continue

            if block_name not in metadata_blocks:
                metadata_blocks[block_name] = {"displayName": block_def.get("displayName", block_name), "name": block_name, "fields": []}

            metadata_blocks[block_name]["fields"].append(field_entry)

        # attach populated blocks
        if metadata_blocks:
            dataset["datasetVersion"]["metadataBlocks"] = metadata_blocks

        # ensure minimal required citation fields if defaults provided
        if defaults:
            # simple fallback: if citation block exists and title missing, use defaults
            cit = dataset.get("datasetVersion", {}).get("metadataBlocks", {}).get("citation")
            if cit and defaults.get('author') and not any(f.get('typeName') == 'author' for f in cit.get('fields', [])):
                cit['fields'].append({"typeName": "author", "multiple": True, "typeClass": "compound", "value": [{"authorName": {"typeName": "authorName", "multiple": False, "typeClass": "primitive", "value": defaults['author']}}]})

        results.append(dataset)
        if verbose:
            total_fields = sum(len(b.get('fields', [])) for b in metadata_blocks.values()) if metadata_blocks else 0
            print(f"Row {idx+1}: id={dataset_id}, fields={total_fields}")

    # write output
    output_data = results[0] if len(results) == 1 else results
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output_data, fh, ensure_ascii=False, indent=2)

    print(f"Wrote {len(results)} dataset(s) to {out_path}")
    return output_data


def main():
    parser = argparse.ArgumentParser(description="Convert CSV to Dataverse JSON using metadata block definitions")
    parser.add_argument("csv_input", help="Input CSV file")
    parser.add_argument("json_output", help="Output JSON file")
    parser.add_argument("--metadef", default="all-metadata-blocks.json", help="Metadata blocks definition JSON")
    args = parser.parse_args()

    csv_to_dataverse_json(args.csv_input, args.json_output, metadata_def_path=args.metadef)


if __name__ == "__main__":
    main()
