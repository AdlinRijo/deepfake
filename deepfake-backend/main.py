import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mimetypes
import numpy as np
import httpx
import tempfile
import uuid
import asyncio

# Local Imports for AI Inference
from inference.visual_model import VisualArtifactDetector
from inference.audio_model import AudioArtifactDetector
from inference.c2pa_validator import C2PAValidator
from inference.face_analysis import FaceAnalyzer
from security import generate_api_key_for_company, verify_api_key

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
print("[STARTING] Initializing deepfake detection models...")
visual_detector = VisualArtifactDetector()
audio_detector = AudioArtifactDetector()
c2pa_validator = C2PAValidator()
face_analyzer = FaceAnalyzer()
print("[OK] All models ready!")


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


class GenerateKeyRequest(BaseModel):
    company_name: str

@app.post("/admin/generate-key")
def generate_key(request: GenerateKeyRequest):
    """
    Generate a new API Key for a social media company.
    This creates an access token to use the B2B API endpoints.
    """
    if not request.company_name or len(request.company_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Valid company name is required.")
    
    api_key = generate_api_key_for_company(request.company_name)
    return {
        "company": request.company_name,
        "api_key": api_key,
        "message": "Store this key centrally. It will only be shown once."
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


class VerificationResult(BaseModel):
    is_deepfake: bool
    is_target_user: bool
    targeted_attack_detected: bool
    authenticity_score: float
    message: str


@app.post("/verify-identity", response_model=VerificationResult)
async def verify_identity(
    reference_image: UploadFile = File(...),
    target_media: UploadFile = File(...),
    company: str = Depends(verify_api_key)
):
    if not reference_image or not target_media:
        raise HTTPException(status_code=400, detail="Both reference_image and target_media are required")

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    ref_path = os.path.join(upload_dir, f"ref_{reference_image.filename}")
    tgt_path = os.path.join(upload_dir, f"tgt_{target_media.filename}")

    with open(ref_path, "wb") as buffer:
        buffer.write(await reference_image.read())
    with open(tgt_path, "wb") as buffer:
        buffer.write(await target_media.read())

    try:
        # 1. Get embedding for the reference user
        ref_embeddings = face_analyzer.get_embeddings_from_image(ref_path)
        if not ref_embeddings:
            raise HTTPException(status_code=400, detail="No face detected in the reference image.")
        if len(ref_embeddings) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces in reference image. Please provide a clear picture of exactly one person.")
        
        anchor_embedding = np.array(ref_embeddings[0])

        # 2. Extract embeddings from the target media
        mime_type, _ = mimetypes.guess_type(target_media.filename)
        is_video = mime_type and mime_type.startswith('video')
        
        if is_video:
            target_embeddings = face_analyzer.get_embeddings_from_video(tgt_path)
        else:
            target_embeddings = face_analyzer.get_embeddings_from_image(tgt_path)
            
        # 3. Check if the target user is in the media
        is_target_user = False
        if target_embeddings:
            for emb in target_embeddings:
                emb_array = np.array(emb)
                # Cosine similarity for L2 normalized vectors is the dot product
                similarity = np.dot(anchor_embedding, emb_array)
                if similarity > 0.65:  # Same threshold as DBSCAN eps=0.35 (1 - 0.35)
                    is_target_user = True
                    break

        # 4. Check if the target media is a deepfake
        visual_result = {"visual_artifacts_score": 0.0}
        audio_result = {"audio_artifacts_score": 0.0}
        
        if is_video:
            visual_result = visual_detector.analyze_video(tgt_path)
            audio_result = audio_detector.analyze_audio(tgt_path)
            fake_prob = visual_result.get("visual_artifacts_score", 0.0) * 0.55 + audio_result.get("audio_artifacts_score", 0.0) * 0.45
        else:
            visual_result = visual_detector.analyze_image(tgt_path)
            fake_prob = visual_result.get("visual_artifacts_score", 0.0)
            
        authenticity_score = max(0.0, (1.0 - fake_prob) * 100.0)
        is_deepfake = authenticity_score < 60.0  # Suspicious or Fake

        targeted_attack_detected = is_deepfake and is_target_user

        if targeted_attack_detected:
            msg = "TARGETED DEEPFAKE DETECTED: The media is manipulated AND contains the reference user's face."
        elif is_deepfake and not is_target_user:
            msg = "DEEPFAKE DETECTED: The media is manipulated, but we did NOT find the reference user's face in it."
        elif not is_deepfake and is_target_user:
            msg = "AUTHENTIC MEDIA: The user is in the media, and no manipulation was detected."
        else:
            msg = "No manipulation detected, and the reference user was not found in the media."

        return VerificationResult(
            is_deepfake=is_deepfake,
            is_target_user=is_target_user,
            targeted_attack_detected=targeted_attack_detected,
            authenticity_score=round(authenticity_score, 2),
            message=msg
        )

    finally:
        # Cleanup
        for path in [ref_path, tgt_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass


# ------------------------------------------------------------------
# B2B Server-to-Server API: URL Verification
# ------------------------------------------------------------------
class MediaURLRequest(BaseModel):
    media_url: str
    media_type: str = "auto"  # "video", "image", "audio", or "auto"


@app.post("/analyze-media-url", response_model=AnalysisResult)
async def analyze_media_url(
    request: MediaURLRequest,
    company: str = Depends(verify_api_key)
):
    """
    B2B Endpoint for social media companies.
    Accepts a direct URL to a media file (CDN link), downloads it temporarily,
    analyzes it through the deepfake pipeline, and returns the result.
    """
    url = request.media_url
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL scheme. Must be http or https.")

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique temp filename
    file_ext = os.path.splitext(url)[1].split('?')[0] # handle query strings in URL
    if not file_ext:
        file_ext = ".tmp"
    
    temp_filename = f"b2b_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(upload_dir, temp_filename)

    try:
        # 1. Download the file from the URL using httpx (streaming to handle large files safely)
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    
                    # Optional: Check content-length to prevent downloading massive files
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > 100 * 1024 * 1024: # 100MB limit
                        raise HTTPException(status_code=413, detail="File too large (limit: 100MB)")
                    
                    with open(file_path, "wb") as buffer:
                        async for chunk in response.aiter_bytes():
                            buffer.write(chunk)
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"Failed to download media from URL: {str(e)}")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error {e.response.status_code} when downloading media")

        # 2. Determine MIME type
        mime_type = "unknown"
        if request.media_type != "auto":
             # Force provided type
             is_video = request.media_type == "video"
             is_audio = request.media_type == "audio"
             is_image = request.media_type == "image"
        else:
            # Guess from header first
            async with httpx.AsyncClient() as client: # need a new client block just for the head request if needed, but we can do it inside the main block. Actually let's just guess from python
                mime_type, _ = mimetypes.guess_type(file_path)
                # If still unknown, try checking the URL itself
                if not mime_type:
                    mime_type, _ = mimetypes.guess_type(url.split('?')[0])
            
            is_video = mime_type and mime_type.startswith('video')
            is_audio = mime_type and mime_type.startswith('audio')
            is_image = mime_type and mime_type.startswith('image')
            
            # Fallback if mimetypes fails
            if not is_video and not is_audio and not is_image:
                 if file_path.endswith((".mp4", ".mov", ".avi", ".webm")):
                     is_video = True
                 elif file_path.endswith((".jpg", ".jpeg", ".png", ".webp")):
                     is_image = True
                 elif file_path.endswith((".mp3", ".wav", ".m4a")):
                     is_audio = True

        if not is_video and not is_audio and not is_image:
            raise HTTPException(status_code=400, detail="Could not determine media type. Please specify media_type explicitly or ensure URL points to a valid media file.")

        # 3. Run Analysis Pipelines
        
        # C2PA Provenance Check
        c2pa_result = c2pa_validator.validate_manifest(file_path)

        # Visual Artifacts Check
        visual_result = {"visual_artifacts_score": 0.0, "visual_artifacts_detected": False}
        if is_video:
            visual_result = visual_detector.analyze_video(file_path)
        elif is_image:
            visual_result = visual_detector.analyze_image(file_path)

        # Audio Artifacts Check
        audio_result = {"audio_artifacts_score": 0.0, "audio_artifacts_detected": False}
        if is_video or is_audio:
            audio_result = audio_detector.analyze_audio(file_path)

        # Face Detection & Clustering
        face_result = {"faces_detected": 0, "unique_identities": 0}
        if is_video:
            face_result = face_analyzer.analyze_video(file_path)
        elif is_image:
            face_result = face_analyzer.analyze_image(file_path)

        # 4. Aggregate Authenticity Score
        if is_video:
            visual_weight, audio_weight = 0.55, 0.45
        elif is_audio:
            visual_weight, audio_weight = 0.0, 1.0
        else:  # image
            visual_weight, audio_weight = 1.0, 0.0

        fake_probability = (
            visual_result.get("visual_artifacts_score", 0.0) * visual_weight
            + audio_result.get("audio_artifacts_score", 0.0) * audio_weight
        )

        authenticity_score = max(0.0, (1.0 - fake_probability) * 100.0)

        if c2pa_result.get("c2pa_valid_signature") and c2pa_result.get("hardware_attested"):
            authenticity_score = min(100.0, authenticity_score + 15.0)

        # 5. Verdict
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
            "media_type": request.media_type if request.media_type != "auto" else ("video" if is_video else ("audio" if is_audio else "image")),
            "source_url": url
        }

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

    finally:
        # Clean up the downloaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
