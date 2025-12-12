# -*- coding: utf-8 -*-
"""
CSV to Dataverse DDI JSON Converter
Converts CSV metadata files to complete Dataverse-compatible JSON format
with all system fields, metadata blocks, and file information.
"""

import os
import csv
import json
import re
import pandas as pd
from datetime import datetime
import uuid
import argparse


def ensure_required_fields(dataset_json, row, defaults=None):
    """Ensure Dataverse-required fields exist; fill with placeholders if missing."""
    try:
        citation_fields = dataset_json["datasetVersion"]["metadataBlocks"]["citation"][
            "fields"
        ]
    except Exception:
        return

    def find_field(name):
        for f in citation_fields:
            if f.get("typeName") == name:
                return f
        return None

    # 1) Author (authorName required)
    author_field = find_field("author")
    if not author_field or not author_field.get("value"):
        # try pull from depositor or CSV 'author' raw string
        raw_author = None
        if "author" in row and not pd.isna(row["author"]):
            raw_author = str(row["author"]).split(";")[0].split("|")[0].strip()
        elif "depositor" in row and not pd.isna(row["depositor"]):
            raw_author = str(row["depositor"]).strip()
        else:
            # fallback to provided default author, environment, or generic
            raw_author = (
                defaults.get("author")
                if defaults and defaults.get("author")
                else (
                    os.getenv("DATAVERSE_DEFAULT_AUTHOR")
                    if os.getenv("DATAVERSE_DEFAULT_AUTHOR")
                    else "Unknown Author"
                )
            )

        new_author = {
            "typeName": "author",
            "multiple": True,
            "typeClass": "compound",
            "value": [
                {
                    "authorName": {
                        "typeName": "authorName",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": raw_author,
                    }
                }
            ],
        }
        # replace or append
        if author_field:
            citation_fields.remove(author_field)
        citation_fields.append(new_author)

    # 2) Dataset contact email (datasetContact -> datasetContactEmail required)
    contact_field = find_field("datasetContact")
    if (
        not contact_field
        or not contact_field.get("value")
        or not any(
            "datasetContactEmail" in v for v in (contact_field.get("value") or [])
        )
    ):
        # try CSV values
        contact_name = None
        contact_email = None
        if "datasetContact" in row and not pd.isna(row["datasetContact"]):
            parts = [p.strip() for p in str(row["datasetContact"]).split(";")]
            if len(parts) >= 1:
                contact_name = parts[0]
            if len(parts) >= 3:
                contact_email = parts[2]
        if not contact_name and "depositor" in row and not pd.isna(row["depositor"]):
            contact_name = str(row["depositor"]).strip()
        if (
            not contact_email
            and "datasetContactEmail" in row
            and not pd.isna(row["datasetContactEmail"])
        ):
            contact_email = str(row["datasetContactEmail"]).strip()
        if not contact_email:
            contact_email = (
                defaults.get("email")
                if defaults and defaults.get("email")
                else (
                    os.getenv("DATAVERSE_DEFAULT_EMAIL")
                    if os.getenv("DATAVERSE_DEFAULT_EMAIL")
                    else "no-reply@example.com"
                )
            )
        if not contact_name:
            contact_name = (
                defaults.get("author")
                if defaults and defaults.get("author")
                else (
                    os.getenv("DATAVERSE_DEFAULT_AUTHOR")
                    if os.getenv("DATAVERSE_DEFAULT_AUTHOR")
                    else "Dataset Contact"
                )
            )

        new_contact = {
            "typeName": "datasetContact",
            "multiple": True,
            "typeClass": "compound",
            "value": [
                {
                    "datasetContactName": {
                        "typeName": "datasetContactName",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": contact_name,
                    },
                    "datasetContactAffiliation": {
                        "typeName": "datasetContactAffiliation",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": str(row.get("datasetContactAffiliation", "")).strip(),
                    },
                    "datasetContactEmail": {
                        "typeName": "datasetContactEmail",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": contact_email,
                    },
                }
            ],
        }
        if contact_field:
            citation_fields.remove(contact_field)
        citation_fields.append(new_contact)

    # 3) Description (dsDescription -> dsDescriptionValue required)
    desc_field = find_field("dsDescription")
    if (
        not desc_field
        or not desc_field.get("value")
        or not any("dsDescriptionValue" in v for v in (desc_field.get("value") or []))
    ):
        desc_text = None
        if "dsDescription" in row and not pd.isna(row["dsDescription"]):
            desc_text = str(row["dsDescription"]).split(";")[0].strip()
        elif "citation" in row and not pd.isna(row["citation"]):
            desc_text = str(row["citation"]).strip()
        else:
            desc_text = (
                defaults.get("description")
                if defaults and defaults.get("description")
                else (
                    os.getenv("DATAVERSE_DEFAULT_DESCRIPTION")
                    if os.getenv("DATAVERSE_DEFAULT_DESCRIPTION")
                    else "No description provided."
                )
            )

        new_desc = {
            "typeName": "dsDescription",
            "multiple": True,
            "typeClass": "compound",
            "value": [
                {
                    "dsDescriptionValue": {
                        "typeName": "dsDescriptionValue",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": desc_text,
                    }
                }
            ],
        }
        if desc_field:
            citation_fields.remove(desc_field)
        citation_fields.append(new_desc)

    return


def csv_to_dataverse_json(csv_file_path, output_json_path, defaults=None):
    """
    Convert CSV file to complete Dataverse JSON format.
    Includes all top-level fields, datasetVersion, license, and metadata blocks.
    """

    # Field type directory - defines structure for all citation fields
    directory = {
        "title": {"typeName": "title", "multiple": False, "typeClass": "primitive"},
        "subtitle": {
            "typeName": "subtitle",
            "multiple": False,
            "typeClass": "primitive",
        },
        "alternativeTitle": {
            "typeName": "alternativeTitle",
            "multiple": True,
            "typeClass": "primitive",
        },
        "otherId": {"typeName": "otherId", "multiple": True, "typeClass": "compound"},
        "author": {"typeName": "author", "multiple": True, "typeClass": "compound"},
        "datasetContact": {
            "typeName": "datasetContact",
            "multiple": True,
            "typeClass": "compound",
        },
        "dsDescription": {
            "typeName": "dsDescription",
            "multiple": True,
            "typeClass": "compound",
        },
        "subject": {
            "typeName": "subject",
            "multiple": True,
            "typeClass": "controlledVocabulary",
        },
        "keyword": {"typeName": "keyword", "multiple": True, "typeClass": "compound"},
        "topicClassification": {
            "typeName": "topicClassification",
            "multiple": True,
            "typeClass": "compound",
        },
        "publication": {
            "typeName": "publication",
            "multiple": True,
            "typeClass": "compound",
        },
        "notesText": {
            "typeName": "notesText",
            "multiple": False,
            "typeClass": "primitive",
        },
        "language": {
            "typeName": "language",
            "multiple": True,
            "typeClass": "controlledVocabulary",
        },
        "producer": {"typeName": "producer", "multiple": True, "typeClass": "compound"},
        "productionDate": {
            "typeName": "productionDate",
            "multiple": False,
            "typeClass": "primitive",
        },
        "productionPlace": {
            "typeName": "productionPlace",
            "multiple": True,
            "typeClass": "primitive",
        },
        "contributor": {
            "typeName": "contributor",
            "multiple": True,
            "typeClass": "compound",
        },
        "grantNumber": {
            "typeName": "grantNumber",
            "multiple": True,
            "typeClass": "compound",
        },
        "distributor": {
            "typeName": "distributor",
            "multiple": True,
            "typeClass": "compound",
        },
        "distributionDate": {
            "typeName": "distributionDate",
            "multiple": False,
            "typeClass": "primitive",
        },
        "depositor": {
            "typeName": "depositor",
            "multiple": False,
            "typeClass": "primitive",
        },
        "dateOfDeposit": {
            "typeName": "dateOfDeposit",
            "multiple": False,
            "typeClass": "primitive",
        },
        "timePeriodCovered": {
            "typeName": "timePeriodCovered",
            "multiple": True,
            "typeClass": "compound",
        },
        "dateOfCollection": {
            "typeName": "dateOfCollection",
            "multiple": True,
            "typeClass": "compound",
        },
        "kindOfData": {
            "typeName": "kindOfData",
            "multiple": True,
            "typeClass": "primitive",
        },
        "series": {"typeName": "series", "multiple": True, "typeClass": "compound"},
        "software": {"typeName": "software", "multiple": True, "typeClass": "compound"},
        "relatedMaterial": {
            "typeName": "relatedMaterial",
            "multiple": True,
            "typeClass": "primitive",
        },
        "relatedDatasets": {
            "typeName": "relatedDatasets",
            "multiple": True,
            "typeClass": "primitive",
        },
        "otherReferences": {
            "typeName": "otherReferences",
            "multiple": True,
            "typeClass": "primitive",
        },
        "dataSources": {
            "typeName": "dataSources",
            "multiple": True,
            "typeClass": "primitive",
        },
        "originOfSources": {
            "typeName": "originOfSources",
            "multiple": False,
            "typeClass": "primitive",
        },
        "characteristicOfSources": {
            "typeName": "characteristicOfSources",
            "multiple": False,
            "typeClass": "primitive",
        },
        "accessToSources": {
            "typeName": "accessToSources",
            "multiple": False,
            "typeClass": "primitive",
        },
    }

    # Compound field subfield mappings
    compound_fields = {
        "otherId": ["otherIdAgency", "otherIdValue"],
        "author": [
            "authorName",
            "authorAffiliation",
            "authorIdentifierScheme",
            "authorIdentifier",
        ],
        "datasetContact": [
            "datasetContactName",
            "datasetContactAffiliation",
            "datasetContactEmail",
        ],
        "dsDescription": ["dsDescriptionValue", "dsDescriptionDate"],
        "keyword": ["keywordValue", "keywordVocabulary", "keywordVocabularyURI"],
        "topicClassification": [
            "topicClassValue",
            "topicClassVocab",
            "topicClassVocabURI",
        ],
        "publication": [
            "publicationRelationType",
            "publicationCitation",
            "publicationIDType",
            "publicationIDNumber",
            "publicationURL",
        ],
        "producer": [
            "producerName",
            "producerAffiliation",
            "producerAbbreviation",
            "producerURL",
            "producerLogoURL",
        ],
        "contributor": ["contributorType", "contributorName"],
        "grantNumber": ["grantNumberAgency", "grantNumberValue"],
        "distributor": [
            "distributorName",
            "distributorAffiliation",
            "distributorAbbreviation",
            "distributorURL",
            "distributorLogoURL",
        ],
        "timePeriodCovered": ["timePeriodCoveredStart", "timePeriodCoveredEnd"],
        "dateOfCollection": ["dateOfCollectionStart", "dateOfCollectionEnd"],
        "series": ["seriesName", "seriesInformation"],
        "software": ["softwareName", "softwareVersion"],
    }

    # Get current date and time for defaults
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().strftime("%Y")
    current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Helper function to convert dates to year-only format
    def format_date_to_year(date_value):
        """Convert any date format to YYYY format"""
        if pd.isna(date_value) or not date_value:
            return current_year

        date_str = str(date_value).strip()

        # Extract year using regex
        year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
        if year_match:
            return year_match.group(0)

        return current_year

    # Read CSV file and process each row
    df = pd.read_csv(csv_file_path)
    all_datasets = []

    for idx, row in df.iterrows():
        # Generate unique IDs if not provided
        dataset_id = (
            int(row.get("id", 0))
            if row.get("id") and not pd.isna(row.get("id"))
            else 1000 + idx
        )
        version_id = (
            int(row.get("versionId", 0))
            if row.get("versionId") and not pd.isna(row.get("versionId"))
            else 2000 + idx
        )

        # Generate identifier/DOI if not provided
        if row.get("identifier") and not pd.isna(row.get("identifier")):
            identifier = str(row.get("identifier"))
        else:
            identifier = f"FK2/{uuid.uuid4().hex[:8].upper()}"

        # Get protocol and authority
        protocol = (
            str(row.get("protocol", "doi")).strip()
            if row.get("protocol") and not pd.isna(row.get("protocol"))
            else "doi"
        )
        authority = (
            str(row.get("authority", "10.70122")).strip()
            if row.get("authority") and not pd.isna(row.get("authority"))
            else "10.70122"
        )

        # Build complete JSON structure with all top-level fields
        dataset_json = {
            "id": dataset_id,
            "identifier": identifier,
            "persistentUrl": (
                f"https://doi.org/{authority}/{identifier}"
                if protocol == "doi"
                else f"hdl:{authority}/{identifier}"
            ),
            "protocol": protocol,
            "authority": authority,
            "separator": "/",
            "publisher": (
                str(row.get("publisher", "Dataverse")).strip()
                if row.get("publisher") and not pd.isna(row.get("publisher"))
                else "Dataverse"
            ),
            "publicationDate": (
                str(row.get("publicationDate", current_date)).strip()
                if row.get("publicationDate")
                and not pd.isna(row.get("publicationDate"))
                else current_date
            ),
            "storageIdentifier": (
                f"s3://{authority}/{identifier}"
                if row.get("storageIdentifier") is None
                or pd.isna(row.get("storageIdentifier"))
                else str(row.get("storageIdentifier"))
            ),
            "datasetType": (
                str(row.get("datasetType", "dataset")).strip()
                if row.get("datasetType") and not pd.isna(row.get("datasetType"))
                else "dataset"
            ),
            "datasetVersion": {
                "id": version_id,
                "datasetId": dataset_id,
                "datasetPersistentId": f"{protocol}:{authority}/{identifier}",
                "datasetType": (
                    str(row.get("datasetType", "dataset")).strip()
                    if row.get("datasetType") and not pd.isna(row.get("datasetType"))
                    else "dataset"
                ),
                "storageIdentifier": (
                    f"s3://{authority}:{uuid.uuid4().hex[:12]}-{uuid.uuid4().hex[:12]}"
                    if row.get("storageIdentifier") is None
                    or pd.isna(row.get("storageIdentifier"))
                    else str(row.get("storageIdentifier"))
                ),
                "versionNumber": (
                    int(row.get("versionNumber", 1))
                    if row.get("versionNumber")
                    and not pd.isna(row.get("versionNumber"))
                    else 1
                ),
                "internalVersionNumber": (
                    int(row.get("internalVersionNumber", 1))
                    if row.get("internalVersionNumber")
                    and not pd.isna(row.get("internalVersionNumber"))
                    else 1
                ),
                "versionMinorNumber": (
                    int(row.get("versionMinorNumber", 0))
                    if row.get("versionMinorNumber")
                    and not pd.isna(row.get("versionMinorNumber"))
                    else 0
                ),
                "versionState": (
                    str(row.get("versionState", "DRAFT")).strip()
                    if row.get("versionState") and not pd.isna(row.get("versionState"))
                    else "DRAFT"
                ),
                "latestVersionPublishingState": (
                    str(row.get("latestVersionPublishingState", "DRAFT")).strip()
                    if row.get("latestVersionPublishingState")
                    and not pd.isna(row.get("latestVersionPublishingState"))
                    else "DRAFT"
                ),
                "UNF": (
                    str(row.get("UNF", "")).strip()
                    if row.get("UNF") and not pd.isna(row.get("UNF"))
                    else ""
                ),
                "lastUpdateTime": (
                    str(row.get("lastUpdateTime", current_datetime)).strip()
                    if row.get("lastUpdateTime")
                    and not pd.isna(row.get("lastUpdateTime"))
                    else current_datetime
                ),
                "releaseTime": (
                    str(row.get("releaseTime", "")).strip()
                    if row.get("releaseTime") and not pd.isna(row.get("releaseTime"))
                    else ""
                ),
                "createTime": (
                    str(row.get("createTime", current_datetime)).strip()
                    if row.get("createTime") and not pd.isna(row.get("createTime"))
                    else current_datetime
                ),
                "publicationDate": (
                    str(row.get("publicationDate", current_date)).strip()
                    if row.get("publicationDate")
                    and not pd.isna(row.get("publicationDate"))
                    else current_date
                ),
                "citationDate": (
                    str(row.get("citationDate", current_date)).strip()
                    if row.get("citationDate") and not pd.isna(row.get("citationDate"))
                    else current_date
                ),
                "termsOfUse": (
                    str(row.get("termsOfUse", "")).strip()
                    if row.get("termsOfUse") and not pd.isna(row.get("termsOfUse"))
                    else ""
                ),
                "citationRequirements": (
                    str(row.get("citationRequirements", "")).strip()
                    if row.get("citationRequirements")
                    and not pd.isna(row.get("citationRequirements"))
                    else ""
                ),
                "conditions": (
                    str(row.get("conditions", "")).strip()
                    if row.get("conditions") and not pd.isna(row.get("conditions"))
                    else ""
                ),
                "termsOfAccess": (
                    str(row.get("termsOfAccess", "")).strip()
                    if row.get("termsOfAccess")
                    and not pd.isna(row.get("termsOfAccess"))
                    else ""
                ),
                "license": {
                    "name": (
                        str(row.get("licenseName", "CC0 1.0")).strip()
                        if row.get("licenseName")
                        and not pd.isna(row.get("licenseName"))
                        else "CC0 1.0"
                    ),
                    "uri": (
                        str(
                            row.get(
                                "licenseUri",
                                "http://creativecommons.org/publicdomain/zero/1.0",
                            )
                        ).strip()
                        if row.get("licenseUri") and not pd.isna(row.get("licenseUri"))
                        else "http://creativecommons.org/publicdomain/zero/1.0"
                    ),
                    "iconUri": (
                        str(
                            row.get(
                                "licenseIconUri",
                                "https://licensebuttons.net/p/zero/1.0/88x31.png",
                            )
                        ).strip()
                        if row.get("licenseIconUri")
                        and not pd.isna(row.get("licenseIconUri"))
                        else "https://licensebuttons.net/p/zero/1.0/88x31.png"
                    ),
                    "rightsIdentifier": (
                        str(row.get("rightsIdentifier", "CC0-1.0")).strip()
                        if row.get("rightsIdentifier")
                        and not pd.isna(row.get("rightsIdentifier"))
                        else "CC0-1.0"
                    ),
                    "rightsIdentifierScheme": (
                        str(row.get("rightsIdentifierScheme", "SPDX")).strip()
                        if row.get("rightsIdentifierScheme")
                        and not pd.isna(row.get("rightsIdentifierScheme"))
                        else "SPDX"
                    ),
                    "schemeUri": (
                        str(row.get("schemeUri", "https://spdx.org/licenses/")).strip()
                        if row.get("schemeUri") and not pd.isna(row.get("schemeUri"))
                        else "https://spdx.org/licenses/"
                    ),
                    "languageCode": (
                        str(row.get("languageCode", "en")).strip()
                        if row.get("languageCode")
                        and not pd.isna(row.get("languageCode"))
                        else "en"
                    ),
                },
                "fileAccessRequest": (
                    bool(row.get("fileAccessRequest", True))
                    if row.get("fileAccessRequest")
                    and not pd.isna(row.get("fileAccessRequest"))
                    else True
                ),
                "metadataBlocks": {
                    "citation": {
                        "displayName": "Citation Metadata",
                        "name": "citation",
                        "fields": [],
                    }
                },
            },
        }

        fields = dataset_json["datasetVersion"]["metadataBlocks"]["citation"]["fields"]

        # Process each metadata field
        for field_name, field_config in directory.items():
            if (
                field_name not in row
                or pd.isna(row[field_name])
                or row[field_name] == ""
            ):
                continue

            value = str(row[field_name]).strip()
            if not value:
                continue

            # Build field structure
            field_entry = {
                "typeName": field_config["typeName"],
                "multiple": field_config["multiple"],
                "typeClass": field_config["typeClass"],
            }

            # Process based on type
            if field_config["typeClass"] == "primitive":
                # Convert date fields to year-only format
                if field_name in [
                    "productionDate",
                    "distributionDate",
                    "dateOfDeposit",
                ]:
                    value = format_date_to_year(value)
                if field_config["multiple"]:
                    # Multiple primitive: split by pipe
                    field_entry["value"] = [
                        v.strip() for v in value.split("|") if v.strip()
                    ]
                else:
                    # Single primitive
                    field_entry["value"] = value

            elif field_config["typeClass"] == "controlledVocabulary":
                # Controlled vocabulary: split by pipe
                field_entry["value"] = [
                    v.strip() for v in value.split("|") if v.strip()
                ]

            elif field_config["typeClass"] == "compound":
                # Compound: parse with subfields
                field_entry["value"] = parse_compound(
                    value, field_name, compound_fields
                )

            # Add to fields list
            if field_entry.get("value"):
                fields.append(field_entry)

        # Add geospatial metadata block if present
        if any(
            col in row
            for col in ["geographicCoverage", "geographicUnit", "geographicBoundingBox"]
        ):
            geo_block = create_geospatial_block(row)
            if geo_block:
                dataset_json["datasetVersion"]["metadataBlocks"][
                    "geospatial"
                ] = geo_block

        # Add social science metadata block if present
        if any(
            col in row
            for col in ["unitOfAnalysis", "universe", "timeMethod", "samplingProcedure"]
        ):
            social_block = create_socialscience_block(row)
            if social_block:
                dataset_json["datasetVersion"]["metadataBlocks"][
                    "socialscience"
                ] = social_block

        # Add files array if present
        if "files" in row and row["files"] and not pd.isna(row["files"]):
            try:
                files_data = (
                    json.loads(row["files"])
                    if isinstance(row["files"], str)
                    else row["files"]
                )
                dataset_json["datasetVersion"]["files"] = (
                    files_data if isinstance(files_data, list) else [files_data]
                )
            except json.JSONDecodeError:
                print(f"  ⚠ Warning: Could not parse files JSON in row {idx + 1}")

        # Add citation field if present
        if "citation" in row and row["citation"] and not pd.isna(row["citation"]):
            dataset_json["citation"] = str(row["citation"]).strip()

        # Ensure required fields exist (author, datasetContact email, description)
        ensure_required_fields(dataset_json, row, defaults)

        all_datasets.append(dataset_json)
        print(
            f"✓ Row {idx + 1}: Dataset ID={dataset_id}, Processed {len(fields)} citation fields"
        )

    # Write output JSON file
    # If single row, write as single object; if multiple rows, write as array
    output_data = all_datasets[0] if len(all_datasets) == 1 else all_datasets

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Successfully converted CSV to JSON: {output_json_path}")
    print(f"✓ Total rows processed: {len(all_datasets)}")
    return output_data


def parse_compound(value, field_name, compound_fields):
    """
    Parse compound field values.
    Format: "value1; value2; value3 | value1; value2; value3"
    """
    if field_name not in compound_fields:
        return []

    subfield_names = compound_fields[field_name]
    entries = [e.strip() for e in value.split("|") if e.strip()]
    result = []

    for entry in entries:
        parts = [p.strip() for p in entry.split(";")]
        entry_obj = {}

        for i, subfield in enumerate(subfield_names):
            if i < len(parts) and parts[i] and parts[i].lower() != "nan":
                # Special handling for dsDescriptionDate - convert to year
                if subfield == "dsDescriptionDate":
                    year_match = re.search(r"\b(19|20)\d{2}\b", parts[i])
                    if year_match:
                        parts[i] = year_match.group(0)
                    else:
                        continue  # Skip invalid dates

                entry_obj[subfield] = {
                    "typeName": subfield,
                    "multiple": False,
                    "typeClass": "primitive",
                    "value": parts[i],
                }

        if entry_obj:
            result.append(entry_obj)

    return result


def create_geospatial_block(row):
    """Create geospatial metadata block if fields are present."""
    geospatial = {
        "displayName": "Geospatial Metadata",
        "name": "geospatial",
        "fields": [],
    }

    # Geographic Coverage
    if (
        "geographicCoverage" in row
        and row["geographicCoverage"]
        and not pd.isna(row["geographicCoverage"])
    ):
        countries = [
            c.strip() for c in str(row["geographicCoverage"]).split("|") if c.strip()
        ]
        geospatial["fields"].append(
            {
                "typeName": "geographicCoverage",
                "multiple": True,
                "typeClass": "compound",
                "value": [
                    {
                        "country": {
                            "typeName": "country",
                            "multiple": False,
                            "typeClass": "controlledVocabulary",
                            "value": c,
                        }
                    }
                    for c in countries
                ],
            }
        )

    # Geographic Unit
    if (
        "geographicUnit" in row
        and row["geographicUnit"]
        and not pd.isna(row["geographicUnit"])
    ):
        units = [u.strip() for u in str(row["geographicUnit"]).split("|") if u.strip()]
        geospatial["fields"].append(
            {
                "typeName": "geographicUnit",
                "multiple": True,
                "typeClass": "primitive",
                "value": units,
            }
        )

    return geospatial if geospatial["fields"] else None


def create_socialscience_block(row):
    """Create social science metadata block if fields are present."""
    socialscience = {
        "displayName": "Social Science and Humanities Metadata",
        "name": "socialscience",
        "fields": [],
    }

    # Simple fields mapping
    simple_fields = {
        "unitOfAnalysis": {"multiple": True, "typeClass": "primitive"},
        "universe": {"multiple": True, "typeClass": "primitive"},
        "timeMethod": {"multiple": False, "typeClass": "primitive"},
        "frequencyOfDataCollection": {"multiple": False, "typeClass": "primitive"},
        "samplingProcedure": {"multiple": False, "typeClass": "primitive"},
        "collectionMode": {"multiple": True, "typeClass": "primitive"},
        "dataCollectionSituation": {"multiple": False, "typeClass": "primitive"},
        "weighting": {"multiple": False, "typeClass": "primitive"},
    }

    for field_name, config in simple_fields.items():
        if field_name in row and row[field_name] and not pd.isna(row[field_name]):
            field_entry = {
                "typeName": field_name,
                "multiple": config["multiple"],
                "typeClass": config["typeClass"],
            }

            if config["multiple"]:
                field_entry["value"] = [
                    v.strip() for v in str(row[field_name]).split("|") if v.strip()
                ]
            else:
                field_entry["value"] = str(row[field_name]).strip()

            socialscience["fields"].append(field_entry)

    return socialscience if socialscience["fields"] else None


# Main execution
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Convert CSV to Dataverse JSON with optional defaults"
    )
    parser.add_argument(
        "csv_input",
        nargs="?",
        default="Csv_to_json - Citation.csv",
        help="Input CSV file",
    )
    parser.add_argument(
        "json_output",
        nargs="?",
        default="output_metadata.json",
        help="Output JSON file",
    )
    parser.add_argument(
        "--default-author",
        dest="default_author",
        help="Default author name if none provided",
    )
    parser.add_argument(
        "--default-email",
        dest="default_email",
        help="Default contact email if none provided",
    )
    parser.add_argument(
        "--default-description",
        dest="default_description",
        help="Default description if none provided",
    )

    args = parser.parse_args()

    defaults = {}
    if args.default_author:
        defaults["author"] = args.default_author
    if args.default_email:
        defaults["email"] = args.default_email
    if args.default_description:
        defaults["description"] = args.default_description

    csv_to_dataverse_json(args.csv_input, args.json_output, defaults=defaults)
