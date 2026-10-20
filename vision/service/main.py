import io
import logging
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from vision.core.schemas import YOLODetectionResult, HealthResponse
from vision.core.detection import (
    YOLODetectorService,
    get_detector,
    SUPPORTED_CLASSES,
)
from vision.core.detection.config import MODEL_ONNX_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bunavision.vision_service")

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    detector = get_detector()
    if not detector.is_loaded:
        raise RuntimeError(
            f"YOLO ONNX model failed to load at startup. "
            f"Ensure '{MODEL_ONNX_PATH.name}' exists in '{MODEL_ONNX_PATH.parent}'."
        )
    logger.info(
        f"Vision service ready - engine={detector.engine_type}, "
        f"model_version={detector.model_version}"
    )
    yield

app = FastAPI(
    title="BunaVision - Defect Detection Service",
    description="Standalone YOLOv8 ONNX defect detection for green coffee beans.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health(detector: YOLODetectorService = Depends(get_detector)):
    return HealthResponse(
        status="healthy" if detector.is_loaded else "unavailable",
        service="vision-detector",
        engine=detector.engine_type,
        model_loaded=detector.is_loaded,
        model_path=str(detector.model_path) if detector.model_path else None,
        supported_classes=SUPPORTED_CLASSES,
    )

@app.post("/detect", response_model=YOLODetectionResult, tags=["Inference"])
async def detect_defects(
    file: UploadFile = File(..., description="Green coffee bean sample photo"),
    confidence: float = Query(0.25, ge=0.05, le=0.95, description="Confidence threshold"),
    detector: YOLODetectorService = Depends(get_detector),
):
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )

    try:
        result = await anyio.to_thread.run_sync(
            lambda: detector.detect(image_bytes, confidence_threshold=confidence)
        )
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
async def reload_model(detector: YOLODetectorService = Depends(get_detector)):
    loaded = await anyio.to_thread.run_sync(detector.reload_model)
    if not loaded:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model reload failed. Active model retained."
        )
    return {
        "reloaded": True,
        "engine": detector.engine_type,
        "model_path": str(detector.model_path) if detector.model_path else None,
    }
