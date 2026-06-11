from pathlib import Path
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

COMPETITION = "haks-airbus-x-ibm-x-aws-2026"
DATA_DIR = Path("data")

DATA_DIR.mkdir(parents=True, exist_ok=True)

api = KaggleApi()
api.authenticate()

api.competition_download_files(
    competition=COMPETITION,
    path=str(DATA_DIR),
    quiet=False,
)

for zip_path in DATA_DIR.glob("*.zip"):
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(DATA_DIR)
    zip_path.unlink()

print(f"Dataset extracted to {DATA_DIR.resolve()}")
