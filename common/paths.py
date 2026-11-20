from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"
METRICS_FILE = RESULTS_DIR / "metrics.csv"
TELEMETRY_FILE = DATA_DIR / "telemetry.jsonl"

RESULTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
