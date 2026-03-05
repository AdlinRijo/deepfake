# 🛡️ Deepfake Detector

A multimodal AI-powered deepfake detection platform that analyzes images, videos, and audio for signs of synthetic manipulation. Built with a **FastAPI** backend running real AI models and a **React** frontend with a modern dark-mode UI.

---

## 🎯 Features

| Feature | Model / Tech | Description |
|---------|-------------|-------------|
| **Visual Deepfake Detection** | EfficientNet-B0 (FaceForensics++ C23) | Frame-level analysis of images and videos for visual manipulation artifacts |
| **Audio Deepfake Detection** | Wav2Vec2 (ASVspoof 2019) | Detects synthetic/cloned speech in audio tracks |
| **C2PA Provenance Validation** | Binary JUMBF Parser | Verifies cryptographic content provenance signatures (JPEG, PNG, video) |
| **Face Detection & Recognition** | dFace (MTCNN + FaceNet) | Detects faces, generates embeddings, clusters unique identities via DBSCAN |
| **Live Camera Capture** | Webcam API | Capture photos directly from your camera for instant AI analysis |

---

## 🏗️ Architecture

```
deepfake-detector/
├── deepfake-backend/          # FastAPI Python backend
│   ├── main.py                # API server & endpoints
│   ├── inference/
│   │   ├── visual_model.py    # EfficientNet-B0 deepfake detector
│   │   ├── audio_model.py     # Wav2Vec2 audio deepfake detector
│   │   ├── c2pa_validator.py  # C2PA binary manifest parser
│   │   └── face_analysis.py   # dFace face detection & clustering
│   ├── dface/                 # dFace library (MTCNN + FaceNet)
│   │   ├── __init__.py
│   │   ├── mtcnn.py           # Multi-task CNN face detection
│   │   └── facenet.py         # FaceNet face embedding (512-dim)
│   ├── models/                # Pre-trained model weights
│   │   ├── efficientnet_b0_ffpp_c23.pth
│   │   ├── wav2vec2-deepfake/
│   │   ├── mtcnn.pt
│   │   └── facenet.pt
│   ├── requirements.txt
│   └── venv/
│
└── deepfake-web-app/          # React + Vite frontend
    ├── src/
    │   ├── App.tsx             # Router & navigation
    │   ├── pages/
    │   │   ├── UploadPage.tsx  # Drag & drop media upload
    │   │   ├── CameraPage.tsx  # Live webcam capture
    │   │   └── ResultsPage.tsx # AI analysis results dashboard
    │   ├── index.css
    │   └── main.tsx
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.js
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **GPU (optional)**: CUDA-capable GPU significantly speeds up inference. Runs on CPU by default.

### 1. Clone the Repository

```bash
git clone https://github.com/AdlinRijo/deepfake.git
cd deepfake
```

### 2. Backend Setup

```bash
cd deepfake-backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Note:** First run will download model weights from HuggingFace (~360MB for Wav2Vec2). MTCNN and FaceNet models are included in the `models/` directory.

### 3. Start the Backend

```bash
python main.py
```

The API will start at **http://localhost:8000**. You should see:

```
🚀 Initializing deepfake detection models...
✅ Visual Deepfake Model loaded on cpu
✅ Audio Deepfake Model loaded on cpu
✅ C2PA Validator initialized (binary parser)
🔵 Loading MTCNN face detection model...
🔵 Loading FaceNet embedding model...
✅ Face analysis models loaded on cpu
🟢 All models ready!
INFO:     Application startup complete.
```

### 4. Frontend Setup

```bash
cd deepfake-web-app

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will start at **http://localhost:5173**.

### 5. Use It

1. Open **http://localhost:5173** in your browser
2. Upload any image or video (supports MP4, MOV, JPEG, PNG, WAV, MP3)
3. Wait for the AI models to analyze the media
4. View the results dashboard with authenticity scores, visual/audio analysis, face detection, and C2PA status

---

## 📡 API Reference

### `GET /`

Health check. Returns API status and loaded models.

**Response:**
```json
{
  "message": "Deepfake Detection API is running",
  "version": "2.0.0",
  "models": {
    "visual": "EfficientNet-B0 (FaceForensics++ C23)",
    "audio": "Wav2Vec2 (ASVspoof 2019)",
    "c2pa": "Binary JUMBF Parser"
  }
}
```

### `POST /upload`

Upload a media file for full AI analysis. Runs all detectors in sequence.

**Request:** `multipart/form-data` with a `file` field.

**Response:**
```json
{
  "authenticity_score": 87.5,
  "c2pa_valid": false,
  "visual_artifacts_detected": false,
  "audio_artifacts_detected": false,
  "face_detected": true,
  "faces_count": 3,
  "verdict": "AUTHENTIC — High confidence this media is genuine.",
  "details": {
    "c2pa_manifest": { ... },
    "visual_analysis": {
      "visual_artifacts_score": 0.12,
      "visual_artifacts_detected": false,
      "model": "EfficientNet-B0 (FaceForensics++ C23)",
      "confidence": 0.76
    },
    "audio_analysis": {
      "audio_artifacts_score": 0.08,
      "audio_artifacts_detected": false,
      "model": "Wav2Vec2 (ASVspoof 2019)"
    },
    "face_analysis": {
      "faces_detected": 3,
      "unique_identities": 2,
      "clusters": {
        "identity_0": {
          "count": 5,
          "sample_thumbnail": "<base64>",
          "avg_confidence": 0.9965
        },
        "identity_1": {
          "count": 2,
          "sample_thumbnail": "<base64>",
          "avg_confidence": 0.9912
        }
      },
      "model": "dFace (MTCNN + FaceNet + DBSCAN)"
    },
    "weights": { "visual": 0.55, "audio": 0.45 },
    "media_type": "video"
  }
}
```

Interactive API docs available at **http://localhost:8000/docs** (Swagger UI).

---

## 🧠 AI Models

### Visual — EfficientNet-B0
- **Source:** [HuggingFace](https://huggingface.co/Xicor9/efficientnet-b0-ffpp-c23)
- **Training:** FaceForensics++ dataset (C23 compression)
- **Input:** 224×224 RGB images
- **Output:** Binary classification (Real / Fake) with probability score

### Audio — Wav2Vec2
- **Source:** [HuggingFace](https://huggingface.co/HyperMoon/wav2vec2-base-finetuned-deepfake-0919)
- **Training:** ASVspoof 2019 dataset
- **Input:** 16kHz mono audio, split into 5-second segments
- **Output:** Binary classification (Real / Fake) with segment-level scores

### Face Detection — MTCNN
- **Source:** [dFace / deepware](https://github.com/deepware/dface)
- **Paper:** [Joint Face Detection and Alignment using MTCNN](https://arxiv.org/abs/1604.02878)
- **Architecture:** 3-stage cascade (PNet → RNet → ONet)
- **Output:** Bounding boxes, confidence scores, facial landmarks

### Face Recognition — FaceNet
- **Source:** [dFace / deepware](https://github.com/deepware/dface)
- **Paper:** [FaceNet: A Unified Embedding for Face Recognition](https://arxiv.org/abs/1503.03832)
- **Architecture:** InceptionResNetV1
- **Output:** 512-dimensional face embeddings, clustered via DBSCAN

### C2PA — Content Provenance
- **Standard:** [C2PA](https://c2pa.org/) (Coalition for Content Provenance and Authenticity)
- **Implementation:** Binary JUMBF parser for JPEG APP11 segments, PNG caBX chunks, and generic file scanning

---

## 🔧 Scoring System

The overall **authenticity score** (0–100%) is computed as:

```
fake_probability = visual_score × visual_weight + audio_score × audio_weight

authenticity_score = (1 - fake_probability) × 100
```

| Media Type | Visual Weight | Audio Weight |
|-----------|--------------|-------------|
| Video     | 0.55         | 0.45        |
| Image     | 1.00         | 0.00        |
| Audio     | 0.00         | 1.00        |

- **C2PA Bonus:** +15 points if a valid cryptographic signature and hardware attestation are found.

| Score Range | Verdict |
|------------|---------|
| 85–100     | ✅ AUTHENTIC |
| 60–84      | ⚠️ SUSPICIOUS |
| 35–59      | 🔴 LIKELY FAKE |
| 0–34       | ❌ FAKE |

---

## 📦 Dependencies

### Backend (Python)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.110.0 | Web framework |
| uvicorn | 0.29.0 | ASGI server |
| torch | 2.2.1 | Deep learning framework |
| torchvision | 0.17.1 | Vision transforms & models |
| torchaudio | 2.2.1 | Audio processing |
| transformers | ≥4.38.0 | HuggingFace model loading |
| opencv-python-headless | 4.9.0.80 | Video frame extraction |
| Pillow | 10.2.0 | Image processing |
| librosa | 0.10.1 | Audio loading & resampling |
| scikit-learn | ≥1.4.0 | DBSCAN face clustering |
| numpy | 1.26.4 | Numerical computing |

### Frontend (Node.js)

| Package | Purpose |
|---------|---------|
| react / react-dom | UI framework |
| react-router-dom | Client-side routing |
| axios | HTTP client for API calls |
| lucide-react | Icon library |
| tailwindcss | Utility-first CSS |
| vite | Build tool & dev server |

---

## 🖥️ Supported Media Formats

| Type | Formats |
|------|---------|
| Image | JPEG, PNG |
| Video | MP4, MOV |
| Audio | WAV, MP3 |

---

## 📝 License

See [LICENSE](LICENSE) for details.
