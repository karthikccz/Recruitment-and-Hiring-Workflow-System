
import csv
import hashlib
import json
from pathlib import Path


def generate_source_manifest(data_dir):
    data_dir = Path(data_dir)
    manifest = []

    for file_path in sorted(data_dir.glob("*.csv")):
        # Calculate SHA-256
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                sha256.update(chunk)

        # Count data rows (excluding header)
        with open(
            file_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:
            row_count = max(sum(1 for _ in csv.reader(file)) - 1, 0)

        manifest.append({
            "file_name": file_path.name,
            "row_count": row_count,
            "size_bytes": file_path.stat().st_size,
            "sha256": sha256.hexdigest()
        })

    manifest_path = data_dir / "SourceManifest.json"

    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4)

    print(f"Source manifest created: {manifest_path}")
    return manifest
