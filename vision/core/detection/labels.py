import json
import logging
from typing import Dict
from vision.core.detection.config import CLASSES_JSON_PATH

logger = logging.getLogger("bunavision.labels")

DEFAULT_CLASSES: Dict[int, str] = {
    0: "hitam",
    1: "hitam-sebagian",
    2: "kulit-kopi-kecil",
}

def load_class_mapping() -> Dict[int, str]:
    if CLASSES_JSON_PATH.exists():
        try:
            with open(CLASSES_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            names = data.get("names", {})
            return {int(k): v for k, v in names.items()}
        except Exception as e:
            logger.warning(f"Could not load classes.json: {e}")
    return DEFAULT_CLASSES.copy()

ONNX_CLASSES = load_class_mapping()

# Canonical English naming for the 3 supported defect classes
CLASS_NAME_MAP = {
    "hitam": "Full Black",
    "hitam-sebagian": "Partial Black",
    "kulit-kopi-kecil": "Coffee Husk / Parchment",
}

SUPPORTED_CLASSES = ["Full Black", "Partial Black", "Coffee Husk / Parchment"]

CLASS_COLORS = {
    "Primary Defect": (220, 38, 38),     # Red
    "Secondary Defect": (234, 179, 8),   # Amber
    "Healthy": (34, 197, 94),            # Green
}

# Raw and English aliases for category classification
PRIMARY_DEFECT_CLASSES = {"hitam", "full_black", "black"}
SECONDARY_DEFECT_CLASSES = {
    "hitam_sebagian",
    "partial_black",
    "kulit_kopi_kecil",
    "coffee_husk",
    "coffee_husk_/_parchment",
    "coffee_husk_parchment",
}

def classify_category(class_name: str) -> str:
    clean = class_name.lower().replace("-", "_").replace(" ", "_")
    if clean in PRIMARY_DEFECT_CLASSES:
        return "Primary Defect"
    elif clean in SECONDARY_DEFECT_CLASSES:
        return "Secondary Defect"

    raise ValueError(
        f"Unsupported defect class '{class_name}'. "
        f"The model only supports: {SUPPORTED_CLASSES}."
    )

def get_display_name(raw_name: str) -> str:
    lower_name = raw_name.lower()
    if lower_name in CLASS_NAME_MAP:
        return CLASS_NAME_MAP[lower_name]
    raise ValueError(
        f"Unknown defect class label '{raw_name}'. "
        f"Allowed raw labels: {list(CLASS_NAME_MAP.keys())}."
    )
