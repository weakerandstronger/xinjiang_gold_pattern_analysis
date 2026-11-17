"""Read-only parsing, identical to v2 core.load; no semantic standardization."""
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

MISSING = {'', 'null', 'none', 'nan', 'n/a', 'unknown', '未知', '未记录'}

def normalize(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', s)).strip()

def parse_cell(s):
    s = normalize(s)
    if s.casefold() in MISSING:
        return None
    if s in ('[]', '{}', '∅'):
        return frozenset()
    values = frozenset(normalize(v) for v in s.split(';') if normalize(v).casefold() not in MISSING)
    return values if values else None

def load(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        raw = list(csv.DictReader(f))
    features = [f for f in raw[0] if f not in ('Deposit', 'doc_id', 'Isotope')]
    groups = defaultdict(list)
    records = []
    for idx, row in enumerate(raw):
        name = normalize(row['Deposit'])
        if name.casefold() in MISSING:
            raise ValueError(f'Empty Deposit at CSV record {idx + 2}')
        groups[name].append(idx)
        records.append([parse_cell(row[f]) for f in features])
    names = list(groups)
    samples = []
    for name in names:
        merged = []
        for j in range(len(features)):
            known = [records[i][j] for i in groups[name] if records[i][j] is not None]
            merged.append(frozenset().union(*known) if known else None)
        samples.append(merged)
    return raw, features, names, samples, records, dict(groups)

def write_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else ['empty']
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict, tuple)) else ('null' if v is None else v) for k, v in row.items()})

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
