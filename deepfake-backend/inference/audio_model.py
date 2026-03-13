import os
import numpy as np
import torch
import librosa
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

# Wav2Vec2 fine-tuned on ASVspoof 2019 for audio deepfake detection
# Model: https://huggingface.co/HyperMoon/wav2vec2-base-finetuned-deepfake-0919

MODEL_ID = "HyperMoon/wav2vec2-base-finetuned-deepfake-0919"
MODEL_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "wav2vec2-deepfake")
SAMPLE_RATE = 16000  # Wav2Vec2 expects 16kHz audio


class AudioArtifactDetector:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.feature_extractor = None
        self.model = None
        self._load_model()
        print(f" Audio Deepfake Model loaded on {self.device}")

    def _load_model(self):
        """Downloads and loads the Wav2Vec2 audio deepfake detection model."""
        print("  Loading Wav2Vec2 audio deepfake model from HuggingFace (first run will download ~360MB)...")
        os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

        self.feature_extractor = AutoFeatureExtractor.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_CACHE_DIR,
        )
        self.model = AutoModelForAudioClassification.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_CACHE_DIR,
        )
        self.model.to(self.device)
        self.model.eval()

    def _extract_audio(self, file_path: str) -> np.ndarray:
        """
        Extract audio waveform from any media file (audio or video).
        Uses librosa which supports various formats.
        Returns mono waveform at 16kHz.
        """
        waveform, sr = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
        return waveform

    def _predict_segment(self, waveform: np.ndarray) -> float:
        """Run inference on an audio segment. Returns probability of being fake."""
        inputs = self.feature_extractor(
            waveform,
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
            padding=True,
        )
        input_values = inputs.input_values.to(self.device)

        with torch.no_grad():
            logits = self.model(input_values).logits
            probs = torch.softmax(logits, dim=-1)

        # Check label mapping  models may use different label orders
        label_names = self.model.config.id2label
        fake_idx = None
        for idx, label in label_names.items():
            if "fake" in label.lower() or "spoof" in label.lower():
                fake_idx = int(idx)
                break

        if fake_idx is not None:
            prob_fake = probs[0][fake_idx].item()
        else:
            # Default: assume index 1 = Fake
            prob_fake = probs[0][1].item() if probs.shape[1] > 1 else probs[0][0].item()

        return prob_fake

    def analyze_audio(self, file_path: str, max_duration_secs: float = 30.0) -> dict:
        """
        Analyzes audio from a file (audio or video) for synthetic speech artifacts.
        Splits long audio into segments and aggregates predictions.
        """
        try:
            waveform = self._extract_audio(file_path)

            if len(waveform) == 0:
                return {
                    "audio_artifacts_score": 0.0,
                    "audio_artifacts_detected": False,
                    "model": "Wav2Vec2 (ASVspoof 2019)",
                    "error": "No audio track found or audio is empty.",
                }

            # Truncate very long audio to max_duration
            max_samples = int(max_duration_secs * SAMPLE_RATE)
            total_duration = len(waveform) / SAMPLE_RATE

            # Split into ~5 second segments for more robust detection
            segment_len = 5 * SAMPLE_RATE
            segments = []
            for start in range(0, min(len(waveform), max_samples), segment_len):
                end = min(start + segment_len, len(waveform))
                seg = waveform[start:end]
                if len(seg) > SAMPLE_RATE:  # Skip segments < 1 second
                    segments.append(seg)

            if not segments:
                # Audio too short, analyze whole thing
                segments = [waveform]

            # Predict each segment
            segment_scores = []
            for seg in segments:
                score = self._predict_segment(seg)
                segment_scores.append(score)

            avg_score = float(np.mean(segment_scores))
            max_score = float(np.max(segment_scores))
            # Blend: 60% average + 40% max
            final_score = 0.6 * avg_score + 0.4 * max_score
            is_fake = final_score > 0.5

            return {
                "audio_artifacts_score": round(final_score, 4),
                "audio_artifacts_detected": bool(is_fake),
                "model": "Wav2Vec2 (ASVspoof 2019)",
                "segments_analyzed": len(segment_scores),
                "audio_duration_secs": round(total_duration, 2),
                "segment_avg_score": round(avg_score, 4),
                "segment_max_score": round(max_score, 4),
                "confidence": round(abs(final_score - 0.5) * 2, 4),
            }

        except Exception as e:
            print(f" Error analyzing audio: {e}")
            return {
                "audio_artifacts_score": 0.0,
                "audio_artifacts_detected": False,
                "model": "Wav2Vec2 (ASVspoof 2019)",
                "error": str(e),
            }

