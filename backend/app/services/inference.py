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


FALL_LABELS     = ["no_fall", "fall"]
VIOLENCE_LABELS = ["no_violence", "violence"]
INPUT_SIZE      = 640
CONF_THRESH     = 0.4
IOU_THRESH      = 0.45


class ModelInference:
    def __init__(self):
        self.settings = get_settings()
        self.fall_session:     "ort.InferenceSession | None" = None
        self.violence_session: "ort.InferenceSession | None" = None

    def load_models(self):
        model_dir = Path(self.settings.MODEL_DIR)
        self._load_model("fall_detection",     model_dir / "fall_detection.onnx")
        self._load_model("violence_detection", model_dir / "violence_detection.onnx")

    def _load_model(self, name: str, path: Path):
        if not ONNX_AVAILABLE:
            logger.warning(f"[{name}] onnxruntime not installed — skipping model load")
            return
        if not path.exists():
            logger.warning(f"[{name}] Model file not found at {path} — skipping load")
            return
        try:
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = os.cpu_count()
            sess_options.inter_op_num_threads = os.cpu_count()
            session = ort.InferenceSession(
                str(path),
                sess_options=sess_options,
                providers=["CPUExecutionProvider"],
            )
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
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
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

    def preprocess_frame(self, image_bytes: bytes, is_video: bool = False) -> tuple:
        img = None
        if CV2_AVAILABLE:
            if is_video:
                img = self._extract_first_frame(image_bytes)
                if img is None:
                    logger.warning("Could not extract video frame — using blank image")
            else:
                img = self._decode_image(image_bytes)
                if img is None:
                    logger.warning("Could not decode image bytes — using blank image")

        if img is None:
            img = np.zeros((640, 640, 3), dtype=np.uint8)

        orig_shape = img.shape
        size       = INPUT_SIZE
        h, w       = img.shape[:2]
        scale      = size / max(h, w)
        nh, nw     = int(h * scale), int(w * scale)

        resized = cv2.resize(img, (nw, nh))

        pad_h = (size - nh) // 2
        pad_w = (size - nw) // 2
        padded = cv2.copyMakeBorder(
            resized,
            pad_h, size - nh - pad_h,
            pad_w, size - nw - pad_w,
            cv2.BORDER_CONSTANT, value=(114, 114, 114),
        )

        rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        arr = rgb.astype(np.float32) / 255.0
        arr = np.transpose(arr, (2, 0, 1))
        arr = np.expand_dims(arr, 0)

        return arr, scale, pad_w, pad_h, orig_shape

    def _predict_from_array(self, model_name: str, preprocessed: tuple) -> dict:
        input_array, scale, pad_w, pad_h, orig_shape = preprocessed

        if model_name == "fall_detection":
            session = self.fall_session
            labels  = FALL_LABELS
        elif model_name == "violence_detection":
            session = self.violence_session
            labels  = VIOLENCE_LABELS
        else:
            raise ValueError(f"Unknown model: {model_name}")

        if session is None:
            logger.warning(f"[{model_name}] No session — returning stub")
            return {"model": model_name, "label": labels[0], "confidence": 0.5, "stub": True}

        input_name = session.get_inputs()[0].name
        raw        = session.run(None, {input_name: input_array})

        pred         = raw[0][0].T
        class_scores = pred[:, 4:]
        scores       = class_scores.max(axis=1)
        class_ids    = class_scores.argmax(axis=1)

        mask      = scores >= CONF_THRESH
        scores    = scores[mask]
        class_ids = class_ids[mask]
        boxes     = pred[mask, :4]

        if len(scores) == 0:
            return {"model": model_name, "label": labels[0], "confidence": 0.0, "stub": False}

        x1 = (boxes[:, 0] - boxes[:, 2] / 2 - pad_w) / scale
        y1 = (boxes[:, 1] - boxes[:, 3] / 2 - pad_h) / scale
        x2 = (boxes[:, 0] + boxes[:, 2] / 2 - pad_w) / scale
        y2 = (boxes[:, 1] + boxes[:, 3] / 2 - pad_h) / scale

        oh, ow = orig_shape[:2]
        x1 = np.clip(x1, 0, ow)
        y1 = np.clip(y1, 0, oh)
        x2 = np.clip(x2, 0, ow)
        y2 = np.clip(y2, 0, oh)

        indices = cv2.dnn.NMSBoxes(
            np.stack([x1, y1, x2, y2], axis=1).tolist(),
            scores.tolist(),
            CONF_THRESH,
            IOU_THRESH,
        )

        if len(indices) == 0:
            return {"model": model_name, "label": labels[0], "confidence": 0.0, "stub": False}

        best_idx   = int(indices[0]) if isinstance(indices[0], (int, np.integer)) else int(indices[0][0])
        confidence = float(scores[best_idx])
        label_idx  = int(class_ids[best_idx])
        label      = labels[label_idx] if label_idx < len(labels) else "unknown"

        return {
            "model":      model_name,
            "label":      label,
            "confidence": round(confidence, 4),
            "stub":       False,
        }

    def predict(self, model_name: str, image_bytes: bytes, is_video: bool = False) -> dict:
        if not image_bytes:
            raise ValueError("image_bytes must not be empty")
        preprocessed = self.preprocess_frame(image_bytes, is_video=is_video)
        return self._predict_from_array(model_name, preprocessed)

    def predict_both(self, image_bytes: bytes, is_video: bool = False) -> dict:
        if not image_bytes:
            raise ValueError("image_bytes must not be empty")
        preprocessed = self.preprocess_frame(image_bytes, is_video=is_video)
        return {
            "fall_detection":     self._predict_from_array("fall_detection",     preprocessed),
            "violence_detection": self._predict_from_array("violence_detection", preprocessed),
        }


model_inference = ModelInference()