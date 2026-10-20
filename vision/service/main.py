"""
vision/service/main.py — Standalone Vision Inference Service
===========================================================
HTTP wrapper around vision.core.yolo_detector.
Runs independently on port 9000.
"""

import io
import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from vision.core.yolo_detector import yolo_service, MODEL_PATH
from vision.core.schemas import YOLODetectionResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bunavision.vision_service")

app = FastAPI(
    title="BunaVision - Defect Detection Service",
    description="Standalone YOLOv8 ONNX defect detection for green coffee beans.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


@app.get("/health", tags=["Health"])
async def health():
    """Health check showing model loading engine and status."""
    return {
        "status": "healthy" if yolo_service.is_loaded else "unavailable",
        "service": "vision-detector",
        "engine": yolo_service.engine_type,
        "model_loaded": yolo_service.is_loaded,
        "model_path": str(MODEL_PATH) if yolo_service.is_loaded else None,
        "supported_classes": list(yolo_service.CLASS_NAME_MAP.values())
    }


@app.post("/detect", response_model=YOLODetectionResult, tags=["Inference"])
async def detect_defects(
    file: UploadFile = File(..., description="Green coffee bean sample photo"),
    confidence: float = Query(0.25, ge=0.05, le=0.95, description="Confidence threshold")
):
    """
    Detects visible defects in an uploaded coffee sample photo.
    Returns localized bounding boxes, defect counts, and annotated base64 image.
    """
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty image uploaded."
        )
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds 10MB limit."
        )

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img.verify()
        if pil_img.format not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported image format: {pil_img.format}. Supported: {SUPPORTED_FORMATS}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )

    try:
        result = yolo_service.detect(image_bytes, confidence_threshold=confidence)
        return result
    except RuntimeError as re:
        logger.error(f"Model error: {re}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference processing failed."
        )


@app.post("/reload-model", tags=["Admin"])
async def reload_model():
    """Hot-reloads the YOLO weights from the model directory."""
    loaded = yolo_service.reload_model()
    return {
        "reloaded": loaded,
        "engine": yolo_service.engine_type,
        "model_path": str(MODEL_PATH)
    }
