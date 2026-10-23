"""
Pydantic schemas shared by vision.core and vision.service.
Defines the inference contract shapes for defect detection.
"""

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
    validator_version: str = Field(
        ...,
        description="Coffee-domain model identifier, e.g. 'MobileNetV3-Small-Coffee-ONNX-v1'",
    )
    is_coffee: bool = Field(True, description="Whether the image contains green coffee beans based on domain validator")
    coffee_confidence: Optional[float] = Field(None, description="Confidence score from the domain validator")
    total_beans: int = Field(
        ...,
        ge=-1,
        description="Total sample bean count; -1 means YOLO does not estimate this count",
    )
    healthy_beans: int = Field(
        ...,
        ge=-1,
        description=(
            "Healthy bean count. -1 means 'not determinable by YOLO' — "
            "this model was trained only on defect classes and cannot count healthy beans. "
            "The backend estimates the real value from the full image."
        )
    )
    defect_beans: int = Field(..., ge=0, description="Count of defective bean instances")
    defect_counts: Dict[str, int] = Field(default_factory=dict, description="Raw count per defect class e.g. {'Full Black': 2}")
    detected_beans: List[DetectedBean] = Field(default_factory=list, description="Full list of bounding box detections")
    annotated_image_base64: Optional[str] = Field(None, description="Base64-encoded JPEG with colored bounding boxes drawn")

class HealthResponse(BaseModel):
    status: str = Field(..., description="'healthy' or 'unavailable'")
    service: str = Field(..., description="Service identifier")
    engine: str = Field(..., description="Inference engine type: 'onnx' or 'none'")
    model_loaded: bool = Field(..., description="Whether model weights are loaded")
    model_path: Optional[str] = Field(None, description="Path to loaded model weights")
    supported_classes: List[str] = Field(default_factory=list, description="Defect classes this model detects")

class DomainRejectionDetail(BaseModel):
    code: str = Field("IMAGE_NOT_COFFEE", description="Error code for domain rejection")
    message: str = Field(..., description="Explanation of rejection")
    confidence: float = Field(..., description="Validator confidence score that image is coffee")
    threshold: float = Field(..., description="Required threshold for coffee classification")

class DomainRejectionResponse(BaseModel):
    detail: DomainRejectionDetail

class HTTPErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="Error message",
    )

class ReloadModelResponse(BaseModel):
    reloaded: bool
    engine: str
    model_path: Optional[str] = None
