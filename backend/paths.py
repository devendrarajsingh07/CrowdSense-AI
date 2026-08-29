from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

STATE_PATH = PROJECT_ROOT / "crowd_data.json"
HISTORY_PATH = DATA_DIR / "crowd_history.csv"
DB_PATH = PROJECT_ROOT / "crowd.db"
MODEL_PATH = PROJECT_ROOT / "yolov8n.pt"
