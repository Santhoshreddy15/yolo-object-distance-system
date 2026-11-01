import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SAMPLE_FOLDER = os.path.join(BASE_DIR, "sample_images")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_FOLDER, exist_ok=True)

def resolve_model_path() -> str:
    """
    Resolve yolov8n.pt using an absolute path anchored to project root, backend folder,
    or via YOLO_WEIGHTS_PATH / YOLO_MODEL environment variable.
    Ensures running backend from any working directory finds the existing 6.5MB model
    file and never attempts online downloads.
    """
    env_path = os.environ.get("YOLO_WEIGHTS_PATH") or os.environ.get("YOLO_MODEL")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return str(p.resolve())
        # Try resolving relative to PROJECT_ROOT or BASE_DIR
        cand_root = PROJECT_ROOT / env_path
        if cand_root.is_file():
            return str(cand_root.resolve())
        cand_base = BASE_DIR / env_path
        if cand_base.is_file():
            return str(cand_base.resolve())
        return env_path

    # Check project root first (standard location for cached weights)
    root_model = PROJECT_ROOT / "yolov8n.pt"
    if root_model.is_file():
        return str(root_model.resolve())

    # Check backend directory
    backend_model = BASE_DIR / "yolov8n.pt"
    if backend_model.is_file():
        return str(backend_model.resolve())

    # Fallback to absolute path at project root
    return str(root_model.resolve())

class Config:
    PROJECT_ROOT = PROJECT_ROOT
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
    UPLOAD_FOLDER = UPLOAD_FOLDER
    SAMPLE_FOLDER = SAMPLE_FOLDER
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    
    # YOLO Model Configuration (Modular & Absolute Path Anchored)
    YOLO_MODEL_NAME = resolve_model_path()
    DEFAULT_CONF_THRESHOLD = 0.25
    DEFAULT_IOU_THRESHOLD = 0.45
    
    # Camera / Distance calibration defaults
    DEFAULT_FOCAL_LENGTH_PX = 800.0  # approximate focal length in pixels
    DEFAULT_REAL_OBJECT_HEIGHT = 1.65 # meters
