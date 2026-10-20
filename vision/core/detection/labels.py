import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from vision.core.detection.config import CLASSES_JSON_PATH

logger = logging.getLogger("bunavision.labels")

# Canonical English naming for the 3 supported defect classes
CLASS_NAME_MAP = {
    "hitam": "Full Black",
    "hitam-sebagian": "Partial Black",
    "kulit-kopi-kecil": "Coffee Husk / Parchment",
}

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

def load_class_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    path = manifest_path if manifest_path is not None else CLASSES_JSON_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Class manifest file not found at {path}. Model bundle is incomplete."
        )
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Corrupt or invalid JSON in class manifest at {path}: {e}") from e

    if "names" not in data or not isinstance(data["names"], dict):
        raise ValueError(
            f"Invalid class manifest at {path}: missing or invalid 'names' mapping."
        )
    return data

def load_class_mapping(manifest_path: Optional[Path] = None) -> Dict[int, str]:
    data = load_class_manifest(manifest_path)
    return {int(k): str(v) for k, v in data["names"].items()}

def get_display_name(raw_name: str) -> str:
    lower_name = raw_name.lower()
    if lower_name in CLASS_NAME_MAP:
        return CLASS_NAME_MAP[lower_name]
    raise ValueError(
        f"Unknown defect class label '{raw_name}'. "
        f"Allowed raw labels: {list(CLASS_NAME_MAP.keys())}."
    )

def get_supported_classes(class_mapping: Optional[Dict[int, str]] = None) -> List[str]:
    mapping = class_mapping if class_mapping is not None else ONNX_CLASSES
    return [get_display_name(name) for name in mapping.values()]

ONNX_CLASSES = load_class_mapping()
SUPPORTED_CLASSES = get_supported_classes(ONNX_CLASSES)

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
