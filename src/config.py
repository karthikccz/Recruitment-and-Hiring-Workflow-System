
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DOCS_DIR = BASE_DIR / "docs"

SEED = 20261022

FULL_CONFIG = {
    "hiring_managers": 40,  # Configurable; not specified by assignment
    "requisitions": 200,
    "candidates": 5000,
    "applications": 8000,
    "interviews": 2000,
}

STARTER_CONFIG = {
    "hiring_managers": 8,
    "requisitions": 20,
    "candidates": 500,
    "applications": 800,
    "interviews": 200,
}

for directory in [DATA_DIR, OUTPUT_DIR, DOCS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
