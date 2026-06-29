# AI Piracy Guard: Enterprise-Grade AI Media Forensics Platform

AI Piracy Guard is a production-grade, high-performance media forensics platform designed to detect video piracy, facial deepfakes, watermark tampering, container-level modifications, copyright violations, and duplicate media distribution. 

Constructed with modular, clean-code architecture adhering to SOLID principles, it replaces fragile heuristics with advanced spatial hashing (aHash, pHash, dHash), Discrete Cosine Transform (DCT) block variances, Fast Fourier Transform (FFT) grids, face extraction neural networks, and container metadata anomaly parsers.

---

## 🏗️ Architecture & Component Overview

```
                           +--------------------------------------+
                           |             REST API / CLI           |
                           +------------------+-------------------+
                                              |
                                              v
                           +--------------------------------------+
                           |          Forensic Pipeline           |
                           +------------------+-------------------+
                                              |
     +-------------------+--------------------+-------------------+--------------------+
     |                   |                    |                   |                    |
     v                   v                    v                   v                    v
+----+----+        +-----+----+          +----+----+        +-----+----+          +----+----+
| Spatial |        | Deepfake |          |Watermark |        | Metadata |          | Overlay |
| Hashing |        |   CNN    |          | FFT/DCT  |        | Forensics|          | OCR/Logo|
+----+----+        +-----+----+          +----+----+        +-----+----+          +----+----+
     |                   |                    |                   |                    |
     +-------------------+--------------------+-------------------+--------------------+
                                              |
                                              v
                           +--------------------------------------+
                           |       Multi-Signal Risk Engine       |
                           +------------------+-------------------+
                                              |
                                              v
                           +------------------+-------------------+
                           |        SQLAlchemy Storage / PDF      |
                           +--------------------------------------+
```

### Forensic Signals Evaluated:
1. **Spatial Hashing**: Generates combined Average Hash (aHash), Difference Hash (dHash), and Perceptual Hash (pHash) signatures for sampled frames.
2. **Temporal Alignment**: Computes Levenshtein-based string edit distances on frame-to-frame change sequences to identify copy modifications over time.
3. **Deepfake Face Classification**: Detects faces using Haar cascades and runs PyTorch batch inference using pre-trained **EfficientNet-B4**, **XceptionNet**, or **ResNet18** classifiers (with a deterministic Laplacian variance fallback).
4. **Watermark & Steganography**: Analyzes border region edge densities, Least Significant Bit (LSB) entropy, Discrete Wavelet Transform (DWT) subband coefficient kurtosis, 2D FFT periodic noise grid spikes, and 8x8 block-level DCT coefficient variances.
5. **Container & Metadata**: Checks codec parameters, FPS consistency, container marcas, and strips editing software tags (Adobe, Handbrake, DaVinci, etc.) via ffprobe/OpenCV.
6. **Overlay OCR & Logos**: Extracts overlay texts in border regions to verify copyright strings, and segments corner regions to flag unauthorized broadcaster logo watermarks.

---

## 🛠️ Tech Stack & Dependencies

- **Core**: Python 3.10+, Flask
- **Forensics & Vision**: OpenCV (`opencv-python`), NumPy, Pillow, PyTorch, Torchvision
- **Database**: SQLAlchemy ORM (SQLite / PostgreSQL)
- **Security & Performance**: PyJWT (HS256 tokens), ThreadPoolExecutor background workers, Sliding-window Rate Limiting
- **Reporting**: ReportLab (Professional PDF reports)

---

## 📂 Repository Layout

```
AI-PiracyGuard/
├── piracyguard/                    # Primary application package
│   ├── __init__.py                 # Package metadata
│   ├── app.py                      # Flask Application Factory
│   ├── config.py                   # Central Settings (frozen dataclass)
│   ├── exceptions.py               # Custom Exception hierarchy
│   ├── logging_config.py           # Structured JSON/Colored Logging
│   │
│   ├── api/                        # REST API Controllers
│   │   ├── middleware/             # Rate limiters, RBAC, JWT Auth
│   │   └── routes/                 # Blueprint routers (auth, scans, reports)
│   │
│   ├── core/                       # Computer Vision & Forensics Engines
│   │   ├── fingerprint/            # spatial (a/p/dHash) & temporal hashes
│   │   ├── deepfake/               # PyTorch CNN backbones & GradCAM
│   │   ├── watermark/              # FFT, DCT block, DWT & LSB checkers
│   │   ├── metadata/               # Codec & tag analyzers
│   │   ├── ocr/ / logo/            # Text & icon overlay recognizers
│   │   ├── risk_engine.py          # Composite risk scoring
│   │   └── detection_engine.py     # Orchestrator
│   │
│   ├── database/                   # Schema Models & Session Pools
│   └── services/                   # Business logics (scan, job, reports)
│
├── tests/                          # Automated pytest suite
├── main.py                         # Command Line Interface (CLI)
├── requirements.txt                # Production library requirements
└── .env.example                    # Environment settings blueprint
```

---

## 🚀 Quick Start Guide

### 1. Installation & Environment Set Up
Ensure Python 3.10+ is installed on your machine. Clone this repository, create a virtual environment, and install dependencies:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the template `.env.example` file and modify variables as needed:

```bash
cp .env.example .env
```

Default credentials:
```ini
SECRET_KEY=change-me-to-a-strong-random-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me-to-a-strong-password
```

### 3. Run Commands via the CLI

Use the built-in command line interface to register originals and execute scans directly from your terminal:

```bash
# View usage instructions
python3 main.py

# Register a known reference original video
python3 main.py --register path/to/original.mp4

# Run a forensic scan on the uploads folder
python3 main.py --run

# View database aggregated statistics
python3 main.py --stats
```

---

## 🌐 API Endpoint Documentation

All REST API endpoints are versioned and prefix with `/api/v1`.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **POST** | `/api/v1/auth/login` | Authenticate username/password, returns JWT | None |
| **POST** | `/api/v1/scans/run` | Enqueue background scan job for uploads directory | User |
| **GET** | `/api/v1/scans/job/<uuid>` | Check progress, status, and results of a scan job | User |
| **POST** | `/api/v1/scans/register` | Fingerprint and save a reference video file | Admin/Analyst |
| **POST** | `/api/v1/reports/job/<uuid>` | Compile professional PDF report for completed job | User |
| **GET** | `/api/v1/reports/download/<uuid>` | Serve generated PDF document download | None |
| **GET** | `/api/v1/analytics/stats` | Retrieve aggregated dashboard counts | User |
| **GET** | `/api/v1/analytics/history` | Retrieve full historical scan metrics list | User |

---

## 🧪 Testing Suite
AI Piracy Guard includes a comprehensive test suite covering core computer vision functions, database ORM scopes, authentication logic, and API endpoints, maintaining a **70%+ code coverage**.

To execute tests and view coverage statistics:

```bash
# Run pytest with code coverage
pytest --cov=piracyguard tests/
```

---

## 📄 License
This project is licensed under the MIT License.

Author: **Kunal Kumar**
