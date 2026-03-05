"""
Face Analysis Module — dFace Integration
=========================================
Uses MTCNN for face detection and FaceNet for face embeddings.
Clusters detected faces using DBSCAN to identify unique individuals.

Based on: https://github.com/deepware/dface
"""

import os
import io
import base64
import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import DBSCAN

# dface library (copied into deepfake-backend/dface/)
from dface import MTCNN, FaceNet

# Resolve model paths relative to the project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
MTCNN_MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "mtcnn.pt")
FACENET_MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "facenet.pt")


class FaceAnalyzer:
    """Detects faces, generates embeddings, and clusters identities from media."""

    def __init__(self):
        import torch
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        print("🔵 Loading MTCNN face detection model...")
        self.mtcnn = MTCNN(self.device, MTCNN_MODEL_PATH)
        print("🔵 Loading FaceNet embedding model...")
        self.facenet = FaceNet(self.device, FACENET_MODEL_PATH)
        print(f"✅ Face analysis models loaded on {self.device}")

    # ------------------------------------------------------------------
    # Video Analysis (replicates the dface example.py pipeline)
    # ------------------------------------------------------------------
    def analyze_video(self, video_path: str) -> dict:
        """
        Full pipeline: extract frames → detect faces → embed → cluster.
        Returns structured results with face counts, identity clusters, and
        base64-encoded thumbnail samples.
        """
        try:
            frames = self._get_frames(video_path)
            if not frames:
                return self._empty_result("No readable frames in video.")

            # Detect faces across all sampled frames
            result = self.mtcnn.detect(frames)

            faces = []
            face_metadata = []  # track which frame/box each face came from
            for i, res in enumerate(result):
                if res is None:
                    continue
                boxes, probs, lands = res
                for j, box in enumerate(boxes):
                    if probs[j] > 0.98:
                        h, w = frames[i].shape[:2]
                        x1, y1, size = self._get_boundingbox(box, w, h)
                        face = frames[i][y1:y1+size, x1:x1+size]
                        if face.size == 0:
                            continue
                        faces.append(face)
                        face_metadata.append({
                            "frame_idx": i,
                            "bbox": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                            "confidence": round(float(probs[j]), 4),
                        })

            if len(faces) == 0:
                return self._empty_result("No faces detected with sufficient confidence.")

            # Generate face embeddings
            embeds = self.facenet.embedding(faces)

            # Cluster identities with DBSCAN
            clusters = {}
            unique_identities = 0
            if len(embeds) >= 5:
                dbscan = DBSCAN(eps=0.35, metric='cosine', min_samples=5)
                labels = dbscan.fit_predict(embeds)
                unique_identities = len(set(labels)) - (1 if -1 in labels else 0)

                for idx, label in enumerate(labels):
                    label = int(label)
                    if label < 0:
                        continue
                    key = f"identity_{label}"
                    if key not in clusters:
                        clusters[key] = {
                            "count": 0,
                            "sample_thumbnail": self._face_to_base64(faces[idx]),
                            "avg_confidence": 0.0,
                        }
                    clusters[key]["count"] += 1
                    clusters[key]["avg_confidence"] += face_metadata[idx]["confidence"]

                # Average out confidence per cluster
                for key in clusters:
                    clusters[key]["avg_confidence"] = round(
                        clusters[key]["avg_confidence"] / clusters[key]["count"], 4
                    )
            else:
                # Too few faces for DBSCAN — treat all as one identity
                unique_identities = 1
                clusters["identity_0"] = {
                    "count": len(faces),
                    "sample_thumbnail": self._face_to_base64(faces[0]),
                    "avg_confidence": round(
                        float(np.mean([m["confidence"] for m in face_metadata])), 4
                    ),
                }

            return {
                "faces_detected": len(faces),
                "unique_identities": unique_identities,
                "frames_sampled": len(frames),
                "clusters": clusters,
                "model": "dFace (MTCNN + FaceNet + DBSCAN)",
            }

        except Exception as e:
            print(f"❌ Face analysis error (video): {e}")
            return self._empty_result(str(e))

    # ------------------------------------------------------------------
    # Image Analysis
    # ------------------------------------------------------------------
    def analyze_image(self, image_path: str) -> dict:
        """Detect faces in a single image. Returns bounding boxes and confidence."""
        try:
            img = Image.open(image_path).convert("RGB")
            frame = np.array(img)

            result = self.mtcnn.detect([frame])

            if result[0] is None:
                return self._empty_result("No faces detected.")

            boxes, probs, lands = result[0]
            detected = []
            thumbnails = []
            for j, box in enumerate(boxes):
                if probs[j] > 0.90:
                    h, w = frame.shape[:2]
                    x1, y1, size = self._get_boundingbox(box, w, h)
                    face = frame[y1:y1+size, x1:x1+size]
                    detected.append({
                        "bbox": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                        "confidence": round(float(probs[j]), 4),
                    })
                    if face.size > 0:
                        thumbnails.append(self._face_to_base64(face))

            return {
                "faces_detected": len(detected),
                "unique_identities": len(detected),  # each face = 1 identity for images
                "faces": detected,
                "thumbnails": thumbnails[:5],  # cap thumbnails
                "model": "dFace (MTCNN)",
            }

        except Exception as e:
            print(f"❌ Face analysis error (image): {e}")
            return self._empty_result(str(e))

    # ------------------------------------------------------------------
    # Helpers (from the original example.py)
    # ------------------------------------------------------------------
    @staticmethod
    def _get_frames(video_path: str) -> list:
        """Sample 1 frame per 30 from a video, just like the demo."""
        frames = []
        vid = cv2.VideoCapture(video_path)
        total = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            vid.release()
            return frames
        nframe = max(total // 30, 1)
        idx = np.linspace(0, total, nframe, endpoint=False, dtype=int)
        for i in range(total):
            ok = vid.grab()
            if i not in idx:
                continue
            ok, frm = vid.retrieve()
            if not ok:
                continue
            frm = cv2.cvtColor(frm, cv2.COLOR_BGR2RGB)
            frames.append(frm)
        vid.release()
        return frames

    @staticmethod
    def _get_boundingbox(box, w, h, scale=1.2):
        """Scale and clip bounding box, from the demo."""
        x1, y1, x2, y2 = box
        size = int(max(x2 - x1, y2 - y1) * scale)
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        if size > w or size > h:
            size = int(max(x2 - x1, y2 - y1))
        x1 = max(int(center_x - size // 2), 0)
        y1 = max(int(center_y - size // 2), 0)
        size = min(w - x1, size)
        size = min(h - y1, size)
        return x1, y1, size

    @staticmethod
    def _face_to_base64(face_array, max_size=96) -> str:
        """Convert a face crop (numpy array) to a base64-encoded JPEG thumbnail."""
        img = Image.fromarray(face_array)
        img.thumbnail((max_size, max_size))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def _empty_result(error_msg: str = "") -> dict:
        return {
            "faces_detected": 0,
            "unique_identities": 0,
            "clusters": {},
            "model": "dFace (MTCNN + FaceNet)",
            "error": error_msg,
        }
