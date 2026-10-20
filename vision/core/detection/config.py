from pathlib import Path

# Paths
CORE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = CORE_DIR.parent / "model"
MODEL_ONNX_PATH = MODEL_DIR / "best.onnx"
MODEL_PT_PATH = MODEL_DIR / "best.pt"
CLASSES_JSON_PATH = MODEL_DIR / "classes.json"

# Preprocessing & inference defaults
DEFAULT_IMG_SIZE = 640
DEFAULT_CONFIDENCE_THRESHOLD = 0.25
DEFAULT_IOU_THRESHOLD = 0.45
DEFAULT_JPEG_QUALITY = 90

# Model identifier
MODEL_VERSION = "YOLOv8n-Coffee-ONNX-v1"
MODEL_VERSION_ONNX = MODEL_VERSION
