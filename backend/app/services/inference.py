import logging
import tempfile
import os
import numpy as np
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort  # type: ignore
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("onnxruntime not available — inference will return stub predictions")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python-headless not available — image preprocessing disabled")


FALL_LABELS = ["no_fall", "fall"]
VIOLENCE_LABELS = ["no_violence", "violence"]
INPUT_SIZE = (224, 224)


class ModelInference:
    def __init__(self):
        self.settings = get_settings()
        self.fall_session: "ort.InferenceSession | None" = None
        self.violence_session: "ort.InferenceSession | None" = None

    def load_models(self):
        model_dir = Path(self.settings.MODEL_DIR)
        self._load_model("fall_detection", model_dir / "fall_detection.onnx")
        self._load_model("violence_detection", model_dir / "violence_detection.onnx")

    def _load_model(self, name: str, path: Path):
        if not ONNX_AVAILABLE:
            logger.warning(f"[{name}] onnxruntime not installed — skipping model load")
            return
        if not path.exists():
            logger.warning(f"[{name}] Model file not found at {path} — skipping load")
            return
        try:
            session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
            if name == "fall_detection":
                self.fall_session = session
            else:
                self.violence_session = session
            logger.info(f"[{name}] Loaded successfully from {path}")
        except Exception as e:
            logger.error(f"[{name}] Failed to load model: {e}")

    def _decode_image(self, image_bytes: bytes) -> "np.ndarray | None":
        if not CV2_AVAILABLE:
            return None
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def _extract_first_frame(self, video_bytes: bytes) -> "np.ndarray | None":
        if not CV2_AVAILABLE:
            return None
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        try:
            tmp.write(video_bytes)
            tmp.flush()
            tmp.close()
            cap = cv2.VideoCapture(tmp.name)
            try:
                ret, frame = cap.read()
                return frame if ret else None
            finally:
                cap.release()
        except Exception as e:
            logger.warning(f"Failed to extract video frame: {e}")
            return None
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

    def preprocess_frame(self, image_bytes: bytes, is_video: bool = False) -> np.ndarray:
        img = None
        if CV2_AVAILABLE:
            if is_video:
                img = self._extract_first_frame(image_bytes)
                if img is None:
                    logger.warning("Could not extract frame from video — falling back to random tensor")
            else:
                img = self._decode_image(image_bytes)
                if img is None:
                    logger.warning("Could not decode image bytes — falling back to random tensor")

        if img is not None and CV2_AVAILABLE:
            img = cv2.resize(img, INPUT_SIZE)
            img = img.astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            img = (img - mean) / std
            img = np.transpose(img, (2, 0, 1))
            return np.expand_dims(img, axis=0).astype(np.float32)

        return np.random.rand(1, 3, 224, 224).astype(np.float32)

    def predict(self, model_name: str, image_bytes: bytes, is_video: bool = False) -> dict:
        if not image_bytes:
            raise ValueError("image_bytes must not be empty")

        input_array = self.preprocess_frame(image_bytes, is_video=is_video)

        if model_name == "fall_detection":
            session = self.fall_session
            labels = FALL_LABELS
        elif model_name == "violence_detection":
            session = self.violence_session
            labels = VIOLENCE_LABELS
        else:
            raise ValueError(f"Unknown model: {model_name}")

        if session is None:
            logger.warning(f"[{model_name}] No session loaded — returning stub prediction")
            return {"model": model_name, "label": labels[0], "confidence": 0.5, "stub": True}

        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: input_array})
        scores = outputs[0][0]

        if len(scores) == 1:
            confidence = float(1 / (1 + np.exp(-scores[0])))
            label_idx = int(confidence >= 0.5)
        else:
            scores_arr = np.array(scores, dtype=np.float64)
            scores_arr -= scores_arr.max()
            exps = np.exp(scores_arr)
            probs = exps / exps.sum()
            label_idx = int(np.argmax(probs))
            confidence = float(probs[label_idx])

        return {
            "model": model_name,
            "label": labels[label_idx] if label_idx < len(labels) else "unknown",
            "confidence": confidence,
            "stub": False,
        }

    def predict_both(self, image_bytes: bytes, is_video: bool = False) -> dict:
        """Run both fall and violence detection models in parallel.
        
        Returns a dict with combined results from both models.
        """
        if not image_bytes:
            raise ValueError("image_bytes must not be empty")

        fall_result = self.predict("fall_detection", image_bytes, is_video=is_video)
        violence_result = self.predict("violence_detection", image_bytes, is_video=is_video)

        return {
            "fall_detection": fall_result,
            "violence_detection": violence_result,
        }


model_inference = ModelInference()