import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mimetypes

# Local Imports for AI Inference
from inference.visual_model import VisualArtifactDetector
from inference.audio_model import AudioArtifactDetector
from inference.c2pa_validator import C2PAValidator
from inference.face_analysis import FaceAnalyzer

app = FastAPI(
    title="Deepfake Detection API",
    description="Multimodal deepfake detection using EfficientNet-B0 (visual) and Wav2Vec2 (audio) with C2PA provenance validation.",
    version="2.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Models (downloads happen on first run)
print("🚀 Initializing deepfake detection models...")
visual_detector = VisualArtifactDetector()
audio_detector = AudioArtifactDetector()
c2pa_validator = C2PAValidator()
face_analyzer = FaceAnalyzer()
print("🟢 All models ready!")


class AnalysisResult(BaseModel):
    authenticity_score: float
    c2pa_valid: bool
    visual_artifacts_detected: bool
    audio_artifacts_detected: bool
    face_detected: bool
    faces_count: int
    verdict: str
    details: dict


@app.get("/")
def read_root():
    return {
        "message": "Deepfake Detection API is running",
        "version": "2.0.0",
        "models": {
            "visual": "EfficientNet-B0 (FaceForensics++ C23)",
            "audio": "Wav2Vec2 (ASVspoof 2019)",
            "c2pa": "Binary JUMBF Parser",
        }
    }


@app.post("/upload", response_model=AnalysisResult)
async def upload_media(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    mime_type, _ = mimetypes.guess_type(file.filename)
    is_video = mime_type and mime_type.startswith('video')
    is_audio = mime_type and mime_type.startswith('audio')
    is_image = mime_type and mime_type.startswith('image')

    # 1. C2PA Provenance Check
    c2pa_result = c2pa_validator.validate_manifest(file_path)

    # 2. Visual Artifacts Check (images and videos)
    visual_result = {"visual_artifacts_score": 0.0, "visual_artifacts_detected": False}
    if is_video:
        visual_result = visual_detector.analyze_video(file_path)
    elif is_image:
        visual_result = visual_detector.analyze_image(file_path)

    # 3. Audio Artifacts Check (videos and audio files)
    audio_result = {"audio_artifacts_score": 0.0, "audio_artifacts_detected": False}
    if is_video or is_audio:
        audio_result = audio_detector.analyze_audio(file_path)

    # 4. Face Detection & Identity Clustering (dFace)
    face_result = {"faces_detected": 0, "unique_identities": 0}
    if is_video:
        face_result = face_analyzer.analyze_video(file_path)
    elif is_image:
        face_result = face_analyzer.analyze_image(file_path)

    # 5. Aggregate Authenticity Score
    # Weight visual more heavily for images, balance for video
    if is_video:
        visual_weight = 0.55
        audio_weight = 0.45
    elif is_audio:
        visual_weight = 0.0
        audio_weight = 1.0
    else:  # image
        visual_weight = 1.0
        audio_weight = 0.0

    # Compute weighted fake probability (0 = real, 1 = fake)
    fake_probability = (
        visual_result.get("visual_artifacts_score", 0.0) * visual_weight
        + audio_result.get("audio_artifacts_score", 0.0) * audio_weight
    )

    # Authenticity = inverse of fake probability (100 = fully authentic)
    authenticity_score = max(0.0, (1.0 - fake_probability) * 100.0)

    # C2PA bonus: boost score if provenance is cryptographically verified
    if c2pa_result.get("c2pa_valid_signature") and c2pa_result.get("hardware_attested"):
        authenticity_score = min(100.0, authenticity_score + 15.0)

    # Generate human-readable verdict
    if authenticity_score >= 85:
        verdict = "AUTHENTIC — High confidence this media is genuine."
    elif authenticity_score >= 60:
        verdict = "SUSPICIOUS — Some indicators of manipulation detected."
    elif authenticity_score >= 35:
        verdict = "LIKELY FAKE — Strong indicators of manipulation."
    else:
        verdict = "FAKE — Very high confidence this media has been manipulated."

    details = {
        "c2pa_manifest": c2pa_result,
        "visual_analysis": visual_result,
        "audio_analysis": audio_result,
        "face_analysis": face_result,
        "weights": {"visual": visual_weight, "audio": audio_weight},
        "media_type": "video" if is_video else ("audio" if is_audio else "image"),
    }

    # Clean up uploaded file
    try:
        os.remove(file_path)
    except OSError:
        pass

    return AnalysisResult(
        authenticity_score=round(authenticity_score, 2),
        c2pa_valid=bool(c2pa_result.get("c2pa_valid_signature", False)),
        visual_artifacts_detected=bool(visual_result.get("visual_artifacts_detected", False)),
        audio_artifacts_detected=bool(audio_result.get("audio_artifacts_detected", False)),
        face_detected=bool(face_result.get("faces_detected", 0) > 0),
        faces_count=int(face_result.get("faces_detected", 0)),
        verdict=verdict,
        details=details,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
