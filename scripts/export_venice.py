#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Any


REPO = Path.home() / "Desktop" / "calfa-catalogs" / "catalog-manuscripts-venice"

V1_V6_JSON = REPO / "bibliographic_records_json"

V7_JSON = (
    Path.home()
    / "Desktop"
    / "inscriptions_calfa"
    / "venice_full"
    / "json"
)

V7_IMAGES = (
    Path.home()
    / "Desktop"
    / "inscriptions_calfa"
    / "Venice_V7"
)

RECORDS_DIR = REPO / "records"
CATALOG_PATH = REPO / "catalog.json"

COLLECTION = "Venice"
COLLECTION_CODE = "V"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def clean_fields(
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if not key.startswith("_")
    }


def make_date(
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "from": data.get("date_debut"),
        "to": data.get("date_fin"),
        "display": data.get("details_date"),
    }


def make_index_entry(
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": record["id"],
        "source": record["source"],
        "number": record["number"],
        "title": record["title"],
        "date_from": record["date"]["from"],
        "date_to": record["date"]["to"],
        "date_display": record["date"]["display"],
        "volume": record["volume"],
        "record": f"records/{record['id']}.json",
    }


def write_record(
    record: dict[str, Any],
) -> None:
    path = (
        RECORDS_DIR
        / f"{record['id']}.json"
    )

    path.write_text(
        json.dumps(
            record,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


# ============================================================
# V1–V6
# ============================================================

def export_v1_v6() -> list[dict[str, Any]]:
    records = []

    source_files = sorted(
        [
            p
            for p in V1_V6_JSON.glob("*.json")
            if (
                p.stem.isdigit()
                and int(p.stem) <= 1205
            )
        ],
        key=lambda p: int(p.stem),
    )

    for path in source_files:
        file_number = path.stem
        data = load_json(path)

        original_numero = str(
            data.get("numero", "")
        ).strip()

        # 1178.json contains duplicated internal numero 1177.
        # Public catalogue number follows the source filename.
        if file_number == "1178":
            number = "1178"
        else:
            number = original_numero

        if not number:
            raise RuntimeError(
                f"Missing numero in {path}"
            )

        public_id = f"V{number}"

        fields = clean_fields(data)

        # Expose normalized public number.
        fields["numero"] = number

        provenance = {
            "source_collection": COLLECTION,
            "source_group": "Venice_V1-V6",
            "source_file": path.name,
        }

        if original_numero != number:
            provenance["original_numero"] = (
                original_numero
            )
            provenance["normalization_note"] = (
                "Source file 1178.json contains "
                "numero 1177; public number "
                "normalized to 1178 from filename "
                "and catalogue sequence."
            )

        record = {
            "id": public_id,
            "source": COLLECTION,
            "collection_code": COLLECTION_CODE,
            "number": number,

            # No source scans have been mapped yet
            # for V1–V6.
            "notice": number,

            # Exact per-volume boundaries are not
            # encoded in the supplied JSON.
            "volume": "Venice_V1-V6",

            "title": data.get("titre"),
            "date": make_date(data),
            "fields": fields,
            "images": [],
            "provenance": provenance,
        }

        records.append(record)

    # Combined catalogue record explicitly supplied
    # as one JSON source record.
    combined_path = (
        V1_V6_JSON
        / "1181-1182.json"
    )

    if not combined_path.exists():
        raise RuntimeError(
            "Missing 1181-1182.json"
        )

    data = load_json(combined_path)

    number = str(
        data["numero"]
    ).strip()

    record = {
        "id": f"V{number}",
        "source": COLLECTION,
        "collection_code": COLLECTION_CODE,
        "number": number,
        "notice": number,
        "volume": "Venice_V1-V6",
        "title": data.get("titre"),
        "date": make_date(data),
        "fields": clean_fields(data),
        "images": [],
        "provenance": {
            "source_collection": COLLECTION,
            "source_group": "Venice_V1-V6",
            "source_file": combined_path.name,
        },
    }

    records.append(record)

    return records


# ============================================================
# V7
# ============================================================

def export_v7() -> list[dict[str, Any]]:
    records = []

    folders = sorted(
        [
            p
            for p in V7_IMAGES.iterdir()
            if p.is_dir()
            and p.name.isdigit()
        ],
        key=lambda p: int(p.name),
    )

    for folder in folders:
        number = folder.name

        source_json = (
            V7_JSON
            / f"{number}.json"
        )

        if not source_json.exists():
            raise RuntimeError(
                f"Missing V7 JSON: {source_json}"
            )

        data = load_json(source_json)

        source_numero = str(
            data.get("numero", "")
        ).strip()

        if source_numero != number:
            raise RuntimeError(
                f"V7 numero mismatch: "
                f"folder={number}, "
                f"JSON={source_numero}"
            )

        files = sorted(
            [
                p.name
                for p in folder.iterdir()
                if (
                    p.is_file()
                    and p.suffix.lower()
                    in {".jpg", ".jpeg"}
                )
            ]
        )

        if not files:
            raise RuntimeError(
                f"No V7 images: {folder}"
            )

        images = [
            {
                "volume": "Venice_V7",
                "file": filename,
            }
            for filename in files
        ]

        record = {
            "id": f"V{number}",
            "source": COLLECTION,
            "collection_code": COLLECTION_CODE,
            "number": number,
            "notice": number,
            "volume": "Venice_V7",
            "title": data.get("titre"),
            "date": make_date(data),
            "fields": clean_fields(data),
            "images": images,
            "provenance": {
                "source_collection": COLLECTION,
                "source_volume": "Venice_V7",
                "source_file": source_json.name,
            },
        }

        records.append(record)

    return records


# ============================================================
# Export
# ============================================================

RECORDS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

for old in RECORDS_DIR.glob("V*.json"):
    old.unlink()

records = (
    export_v1_v6()
    + export_v7()
)


def sort_key(
    record: dict[str, Any],
):
    number = record["number"]

    if number == "1181-1182":
        return (1181, 1)

    return (
        int(number),
        0,
    )


records.sort(
    key=sort_key
)

ids = [
    record["id"]
    for record in records
]

if len(ids) != len(set(ids)):
    duplicates = sorted(
        {
            x
            for x in ids
            if ids.count(x) > 1
        }
    )

    raise RuntimeError(
        f"Duplicate public IDs: {duplicates}"
    )

for record in records:
    write_record(record)


catalog = {
    "collection": COLLECTION,
    "collection_code": COLLECTION_CODE,
    "record_count": len(records),
    "records": [
        make_index_entry(record)
        for record in records
    ],
}

CATALOG_PATH.write_text(
    json.dumps(
        catalog,
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)


v1_v6_count = sum(
    1
    for r in records
    if r["volume"] == "Venice_V1-V6"
)

v7_count = sum(
    1
    for r in records
    if r["volume"] == "Venice_V7"
)

image_count = sum(
    len(r["images"])
    for r in records
)

print("========== VENICE EXPORT ==========")
print("Total records:", len(records))
print("V1-V6 records:", v1_v6_count)
print("V7 records:", v7_count)
print("Source scans:", image_count)
print("First ID:", records[0]["id"])
print("Last ID:", records[-1]["id"])
