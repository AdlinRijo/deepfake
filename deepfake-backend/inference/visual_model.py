import os
import cv2
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
from torchvision import models, transforms

# EfficientNet-B0 fine-tuned on FaceForensics++ C23
# Model: https://huggingface.co/Xicor9/efficientnet-b0-ffpp-c23

MODEL_URL = "https://huggingface.co/Xicor9/efficientnet-b0-ffpp-c23/resolve/main/efficientnet_b0_ffpp_c23.pth"
MODEL_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

# Standard preprocessing for EfficientNet-B0
TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class VisualArtifactDetector:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model()
        print(f" Visual Deepfake Model loaded on {self.device}")

    def _load_model(self):
        """Downloads and loads the EfficientNet-B0 deepfake detection model."""
        os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
        model_path = os.path.join(MODEL_CACHE_DIR, "efficientnet_b0_ffpp_c23.pth")

        # Download if not cached
        if not os.path.exists(model_path):
            print("  Downloading EfficientNet-B0 deepfake model from HuggingFace...")
            state_dict = torch.hub.load_state_dict_from_url(
                MODEL_URL,
                model_dir=MODEL_CACHE_DIR,
                map_location=self.device,
                file_name="efficientnet_b0_ffpp_c23.pth"
            )
        else:
            print(" Loading cached EfficientNet-B0 deepfake model...")
            state_dict = torch.load(model_path, map_location=self.device, weights_only=True)

        # Rebuild architecture: EfficientNet-B0 with 2-class head (Real / Fake)
        model = models.efficientnet_b0(weights=None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        return model

    def _predict_frame(self, pil_image: Image.Image) -> float:
        """Run inference on a single PIL Image. Returns probability of being fake (0.0 - 1.0)."""
        tensor = TRANSFORM(pil_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)
            # Index 1 = Fake class
            prob_fake = probs[0][1].item()
        return prob_fake

    def analyze_image(self, image_path: str) -> dict:
        """
        Analyzes an image for deepfake visual artifacts using EfficientNet-B0.
        Returns a dictionary with the fake probability score and detection flag.
        """
        try:
            img = Image.open(image_path).convert("RGB")
            fake_score = self._predict_frame(img)
            is_fake = fake_score > 0.5

            return {
                "visual_artifacts_score": round(float(fake_score), 4),
                "visual_artifacts_detected": bool(is_fake),
                "model": "EfficientNet-B0 (FaceForensics++ C23)",
                "confidence": round(abs(fake_score - 0.5) * 2, 4),  # 0-1 confidence scale
            }
        except Exception as e:
            print(f" Error analyzing image: {e}")
            return {
                "visual_artifacts_score": 0.0,
                "visual_artifacts_detected": False,
                "model": "EfficientNet-B0 (FaceForensics++ C23)",
                "error": str(e),
            }

    def analyze_video(self, video_path: str, max_frames: int = 32) -> dict:
        """
        Extracts frames uniformly from a video and analyzes each for deepfake artifacts.
        Aggregates frame-level scores into a single video-level verdict.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                raise ValueError("Video has no readable frames.")

            # Sample frames uniformly across the video
            sample_indices = np.linspace(0, total_frames - 1, min(max_frames, total_frames), dtype=int)
            frame_scores = []

            for idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if not ret:
                    continue

                # Convert BGR (OpenCV)  RGB (PIL)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_frame = Image.fromarray(rgb_frame)
                score = self._predict_frame(pil_frame)
                frame_scores.append(score)

            cap.release()

            if not frame_scores:
                raise ValueError("Could not extract any valid frames from video.")

            # Aggregate: weighted mean with higher weight on max scores (catches localized fakes)
            avg_score = float(np.mean(frame_scores))
            max_score = float(np.max(frame_scores))
            # Blend: 60% average + 40% max to catch even short manipulated segments
            final_score = 0.6 * avg_score + 0.4 * max_score
            is_fake = final_score > 0.5

            return {
                "visual_artifacts_score": round(final_score, 4),
                "visual_artifacts_detected": bool(is_fake),
                "model": "EfficientNet-B0 (FaceForensics++ C23)",
                "frames_analyzed": len(frame_scores),
                "frame_avg_score": round(avg_score, 4),
                "frame_max_score": round(max_score, 4),
                "confidence": round(abs(final_score - 0.5) * 2, 4),
            }
        except Exception as e:
            print(f" Error analyzing video: {e}")
            return {
                "visual_artifacts_score": 0.0,
                "visual_artifacts_detected": False,
                "model": "EfficientNet-B0 (FaceForensics++ C23)",
                "error": str(e),
            }

