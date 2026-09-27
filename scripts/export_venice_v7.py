#!/usr/bin/env python3

import json
from pathlib import Path

SOURCE_JSON = Path(
    "/Users/sedakirakosyan/Desktop/inscriptions_calfa/venice_full/json"
)

SOURCE_IMAGES = Path(
    "/Users/sedakirakosyan/Desktop/inscriptions_calfa/Venice_V7"
)

REPO = Path(
    "/Users/sedakirakosyan/Desktop/calfa-catalogs/"
    "catalog-manuscripts-venice"
)

RECORDS_DIR = REPO / "records"
CATALOG_PATH = REPO / "catalog.json"

VOLUME = "Venice_V7"
COLLECTION = "Venice"
COLLECTION_CODE = "V"


def clean_fields(data):
    return {
        key: value
        for key, value in data.items()
        if not key.startswith("_")
    }


records = []

RECORDS_DIR.mkdir(parents=True, exist_ok=True)

# Remove previously generated public records only.
for old in RECORDS_DIR.glob("V*.json"):
    old.unlink()


folders = sorted(
    [
        p for p in SOURCE_IMAGES.iterdir()
        if p.is_dir() and p.name.isdigit()
    ],
    key=lambda p: int(p.name),
)


for folder in folders:
    numero = folder.name
    source_json = SOURCE_JSON / f"{numero}.json"

    if not source_json.exists():
        raise RuntimeError(
            f"Missing source JSON for {numero}: {source_json}"
        )

    data = json.loads(
        source_json.read_text(encoding="utf-8")
    )

    source_numero = str(data.get("numero", "")).strip()

    if source_numero != numero:
        raise RuntimeError(
            f"numero mismatch: folder={numero}, "
            f"JSON numero={source_numero}"
        )

    image_files = sorted(
        [
            p.name
            for p in folder.iterdir()
            if p.is_file()
            and p.suffix.lower() in {".jpg", ".jpeg"}
        ]
    )

    if not image_files:
        raise RuntimeError(
            f"No source images for manuscript {numero}"
        )

    manuscript_images = [
        {
            "volume": VOLUME,
            "file": filename,
        }
        for filename in image_files
    ]

    fields = clean_fields(data)

    title = data.get("titre")

    date_from = data.get("date_debut")
    date_to = data.get("date_fin")
    date_display = data.get("details_date")

    public_id = f"V{numero}"

    record = {
        "id": public_id,
        "source": COLLECTION,
        "collection_code": COLLECTION_CODE,
        "number": numero,

        # For source-image routing this is the image folder name.
        "notice": numero,

        "volume": VOLUME,
        "title": title,

        "date": {
            "from": date_from,
            "to": date_to,
            "display": date_display,
        },

        "fields": fields,

        # These are source catalogue scans.
        # fields["images"], if present, remains untouched and
        # continues to mean manuscript illustration metadata.
        "images": manuscript_images,

        "provenance": {
            "source_file": f"{numero}.json",
            "source_volume": VOLUME,
        },
    }

    output = RECORDS_DIR / f"{public_id}.json"

    output.write_text(
        json.dumps(
            record,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    records.append(
        {
            "id": public_id,
            "source": COLLECTION,
            "number": numero,
            "title": title,
            "date_from": date_from,
            "date_to": date_to,
            "date_display": date_display,
            "volume": VOLUME,
            "record": f"records/{public_id}.json",
        }
    )


catalog = {
    "collection": COLLECTION,
    "collection_code": COLLECTION_CODE,
    "record_count": len(records),
    "records": records,
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


total_images = sum(
    len(
        json.loads(
            (RECORDS_DIR / f"V{r['number']}.json")
            .read_text(encoding="utf-8")
        )["images"]
    )
    for r in records
)

print("========== VENICE V7 EXPORT ==========")
print("Records:", len(records))
print("Source images:", total_images)
print("First:", records[0]["id"])
print("Last:", records[-1]["id"])
print("Catalog:", CATALOG_PATH)
print("Records directory:", RECORDS_DIR)
