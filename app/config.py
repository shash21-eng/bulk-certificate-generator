import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("CERTGEN_DB_PATH", BASE_DIR / "data" / "certificates.db"))
OUTPUT_DIR = Path(os.getenv("CERTGEN_OUTPUT_DIR", BASE_DIR / "certificates"))
