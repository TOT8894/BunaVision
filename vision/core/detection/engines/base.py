from dataclasses import dataclass
from typing import List, Protocol
from PIL import Image

@dataclass
class RawDetection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str

class DetectionEngine(Protocol):
    model_version: str
    engine_type: str
    is_loaded: bool

    def predict(self, pil_img: Image.Image, conf_threshold: float) -> List[RawDetection]:
        ...
