#!/usr/bin/env python3
"""Create draft datasets from converter JSON. Standard library only; preview by default."""

import argparse
import configparser
import getpass
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    """Never forward an API token to a redirected destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def prepare_payload(record):
    """Keep metadata only; generated IDs, timestamps and storage fields are not submitted."""
    if not isinstance(record, dict):
        raise ValueError('Each dataset must be a JSON object.')
    version = record.get('datasetVersion', record)
    if not isinstance(version, dict):
        raise ValueError('datasetVersion must be an object.')
    blocks = version.get('metadataBlocks')
    if not isinstance(blocks, dict) or not blocks:
        raise ValueError('Missing or empty metadataBlocks.')
    for name, block in blocks.items():
        if not isinstance(block, dict) or not isinstance(block.get('fields'), list):
            raise ValueError(f'Invalid fields list in block {name}.')
        if any(not isinstance(field, dict) for field in block['fields']):
            raise ValueError(f'Invalid field in block {name}.')
    # Intentionally do not copy converter-generated license or access-policy defaults.
    return {'datasetVersion': {'metadataBlocks': blocks}}


def missing_required(payload):
    fields = payload['datasetVersion']['metadataBlocks'].get('citation', {}).get('fields', [])
    indexed = {field.get('typeName'): field.get('value') for field in fields}

    def present(value):
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list):
            return any(present(item) for item in value)
        return False

    def child_present(parent, child):
        values = indexed.get(parent)
        return isinstance(values, list) and any(
            isinstance(item, dict) and isinstance(item.get(child), dict)
            and present(item[child].get('value')) for item in values
        )

    checks = {
        'title': present(indexed.get('title')),
        'author name': child_present('author', 'authorName'),
        'contact email': child_present('datasetContact', 'datasetContactEmail'),
        'description': child_present('dsDescription', 'dsDescriptionValue'),
        'subject': present(indexed.get('subject')),
    }
    return [name for name, valid in checks.items() if not valid]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('json_files', nargs='+', type=Path)
    parser.add_argument('--config', type=Path, help='INI file (default: config.ini in the repository root).')
    parser.add_argument('--server-url', help='Dataverse HTTPS URL; prompted when omitted.')
    parser.add_argument('--collection', help='Destination collection alias or numeric ID; prompted when omitted.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true', help='Create new drafts (otherwise preview locally).')
    mode.add_argument('--dry-run', action='store_true', help='Preview locally without an API token or network.')
    args = parser.parse_args()
    config_path = args.config or Path(__file__).resolve().parent.parent / 'config.ini'
    config = configparser.ConfigParser(interpolation=None)
    try:
        with config_path.open(encoding='utf-8-sig') as handle:
            config.read_file(handle)
    except FileNotFoundError:
        if args.config:
            parser.error('The specified configuration file does not exist.')
    except (OSError, configparser.Error):
        # Parser exceptions can include raw lines containing credentials.
        parser.error('Cannot read configuration. Check its permissions and INI format.')
    args.server_url = args.server_url or config.get('dataverse', 'server_url', fallback='').strip()
    args.collection = args.collection or config.get('dataverse', 'collection', fallback='').strip()
    try:
        if not args.server_url:
            args.server_url = input('Server URL (e.g. https://borealisdata.ca): ').strip()
        if not args.collection:
            args.collection = input('Collection alias or numeric ID: ').strip()
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled; nothing uploaded.', file=sys.stderr)
        return 1
    server = args.server_url.strip().rstrip('/')
    url = urlsplit(server)
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
            or url.query or url.fragment or url.path not in ('', '/')):
        parser.error('--server-url must be an HTTPS origin, e.g. https://borealisdata.ca')
    if not args.collection.strip():
        parser.error('--collection cannot be empty')
    endpoint = f'{server}/api/dataverses/{quote(args.collection, safe="")}/datasets'
    pending = []
    invalid = False
    try:
        for path in args.json_files:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            records = data if isinstance(data, list) else [data]
            if not records:
                raise ValueError(f'{path}: no datasets.')
            for index, record in enumerate(records, 1):
                payload = prepare_payload(record)
                missing = missing_required(payload)
                fields = payload['datasetVersion']['metadataBlocks'].get('citation', {}).get('fields', [])
                title = next((f.get('value') for f in fields if f.get('typeName') == 'title'), '(missing)')
                label = f'{path} record {index}'
                print(f'{label}: title={title!r}')
                print('  Blocks: ' + ', '.join(payload['datasetVersion']['metadataBlocks']))
                if missing:
                    print('  Missing required metadata: ' + ', '.join(missing))
                    invalid = True
                pending.append((label, payload))
    except (OSError, ValueError) as exc:
        print(f'Input error: {exc}', file=sys.stderr)
        return 1
    print(f'Destination: {endpoint}')
    if invalid:
        print('Fix missing metadata in the source CSV and regenerate JSON. Nothing uploaded.')
        return 1
    if not args.apply:
        print(f'Preview: {len(pending)} draft(s). No requests sent. Use --apply to upload.')
        print('Local checks cover required field presence; Borealis validates vocabulary and collection rules.')
        return 0
    token = (os.environ.get('DATAVERSE_API_TOKEN') or
             config.get('dataverse', 'api_key', fallback='').strip())
    if not token:
        try:
            token = getpass.getpass('Borealis API token (hidden): ')
        except (EOFError, KeyboardInterrupt):
            print('\nCancelled; nothing uploaded.', file=sys.stderr)
            return 1
    if not token.strip():
        print('API token is empty.', file=sys.stderr)
        return 1
    opener = build_opener(NoRedirect())
    for label, payload in pending:
        request = Request(endpoint, data=json.dumps(payload, allow_nan=False).encode('utf-8'),
                          headers={'X-Dataverse-key': token, 'Content-Type': 'application/json'}, method='POST')
        try:
            with opener.open(request, timeout=60) as response:
                result = json.load(response)
            if not isinstance(result, dict) or result.get('status') != 'OK':
                raise ValueError('Unexpected API response.')
        except HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace').replace(token, '[REDACTED]')
            print(f'{label}: HTTP {exc.code}: {detail[:4000]}', file=sys.stderr)
            print('Stopped. Earlier successful drafts remain; check Borealis before rerunning.', file=sys.stderr)
            return 1
        except (URLError, OSError, ValueError) as exc:
            print(f'{label}: {str(exc).replace(token, "[REDACTED]")}', file=sys.stderr)
            print('Result uncertain. Check Borealis before retrying to avoid duplicate drafts.', file=sys.stderr)
            return 1
        print(f'Created draft for {label}: {json.dumps(result.get("data", {}))}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
