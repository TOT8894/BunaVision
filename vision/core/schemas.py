# ============================================================
# MIGRATED during repo restructure (monolith app/ -> 3 services).
# Code is UNCHANGED. Imports below still reference the old `app.*`
# monolith layout and WILL NOT RESOLVE until the owner rewires them.
# TODO(owner): none — self-contained.
# ============================================================

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x1: float = Field(..., description="Top-left X coordinate (pixels)")
    y1: float = Field(..., description="Top-left Y coordinate (pixels)")
    x2: float = Field(..., description="Bottom-right X coordinate (pixels)")
    y2: float = Field(..., description="Bottom-right Y coordinate (pixels)")


class DetectedBean(BaseModel):
    box: BoundingBox = Field(..., description="Bounding box coordinates")
    class_name: str = Field(..., description="Canonical English defect class name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score (0-1)")
    category: str = Field(..., description="'Primary Defect', 'Secondary Defect', or 'Healthy'")


class YOLODetectionResult(BaseModel):
    model_version: str = Field(..., description="Model identifier, e.g. 'YOLOv8n-Coffee-ONNX-v1'")
    total_beans: int = Field(..., ge=0, description="Total defect instances localized by YOLO")
    healthy_beans: int = Field(
        ...,
        ge=-1,
        description=(
            "Healthy bean count. -1 means 'not determinable by YOLO' — "
            "this model was trained only on defect classes and cannot count healthy beans. "
            "Gemini estimates the real value from the full image."
        )
    )
    defect_beans: int = Field(..., ge=0, description="Count of defective bean instances")
    defect_counts: Dict[str, int] = Field(default_factory=dict, description="Raw count per defect class e.g. {'Full Black': 2}")
    detected_beans: List[DetectedBean] = Field(default_factory=list, description="Full list of bounding box detections")
    annotated_image_base64: Optional[str] = Field(None, description="Base64-encoded JPEG with colored bounding boxes drawn")
