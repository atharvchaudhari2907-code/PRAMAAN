# BIS ONE (BIS AI Assistant) — Intelligent Pre-Certification & Cryptographic Conformity Platform
**Smart India Hackathon 2026 (SIH) | Problem Statement: SIH26107**

An enterprise-grade, manufacturer-focused full-stack pre-certification assistant and cryptographic trust ledger that bridges the gap between complex Bureau of Indian Standards (BIS) regulations, laboratory compliance, and market conformity.

---

## 🏛️ System Architecture

```
                                  ┌─────────────────────────────┐
                                  │      React + TypeScript     │
                                  │   (Manufacturer Dashboard) │
                                  └──────────────┬──────────────┘
                                                 │ REST API (JSON) + Bearer JWT
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FastAPI Backend Server                                │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────┤
│    Authentication & AuthZ     │      Document Intelligence    │    Compliance Engine    │
│  - Email/Password (PBKDF2)    │  - Multimodal PDF Extractor   │  - Deterministic Math   │
│  - JWT Bearer & Revocation    │  - Pydantic Structured Schema │  - Mathematical Scoring │
│  - Multi-Tenant Isolation     │  - Prompt Injection Defense   │  - Interactive Recheck  │
├───────────────────────────────┼───────────────────────────────┼─────────────────────────┤
│    BIS Application Workflow   │     Multimodal & IoT Layer    │  Cryptographic Ledger   │
│  - Dynamic Document Checklist │  - 12 Indian Languages Voice  │  - Canonical SHA-256    │
│  - Form I, II, IV & Dossier   │  - Computer Vision (YOLOv8)   │  - Content-Addressed IPFS│
│  - Versioned Document Hashes  │  - IoT Lab Sensor Telemetry   │  - Blockchain Anchor    │
│  - ZIP Export & Status Audit  │  - Citation-Backed RAG Chat   │  - Public QR Code Verify│
├───────────────────────────────┴───────────────────────────────┴─────────────────────────┤
│                                 Database Layer (SQLAlchemy ORM)                         │
│   Users | Sessions | Applications | Documents | Checklists | Certificates | Events      │
│                  SQLite (Default Zero-Config) / PostgreSQL (Production)                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Modules & Capabilities

1. **Enterprise Multi-Tenant Security & Authentication**:
   - OWASP-compliant PBKDF2-HMAC-SHA256 password hashing (600,000 iterations & cryptographic salt).
   - JWT access & refresh token management with token revocation on password reset.
   - Strict resource-level multi-tenant isolation ensuring manufacturers cannot access or tamper with competitor applications, documents, checklists, or private certificates (strictly returning 404).

2. **Multimodal Document Intelligence Pipeline**:
   - Direct PDF byte ingestion and cryptographic SHA-256 content hashing upon receipt.
   - Structured parameter extraction with unit tracking, confidence scoring, and source snippet attribution.
   - Prompt injection defense using isolated `<SYSTEM_INSTRUCTIONS>`, `<USER_DATA>`, and `<DOCUMENT_CONTENT>` tags.

3. **Deterministic Compliance Engine & Mathematical Readiness Gate**:
   - Zero hardcoded scores: Readiness score is calculated mathematically from clause evaluation weights, critical penalties (-40 points per critical failure), and missing evidence discounts.
   - Interactive parameter recheck updating the database and dynamically recalculating the score.

4. **Official BIS Forms & Application Dossier**:
   - Dynamic checklist tracking required statutory documents (Factory Layout, Test Report, Brand Registration, Machinery List).
   - Generates official BIS Form I, Form II, Form IV, and a 14-section Technical Dossier with field-level provenance tracking (`AI_EXTRACTED`, `MANUFACTURER_INPUT`, `BIS_STANDARD_CATALOG`).
   - Generates versioned immutable documents with SHA-256 hashes and exports full ZIP dossier packages.

5. **Cryptographic Trust Ledger & Public QR Verification**:
   - Deterministic canonical certificate representation hashed with SHA-256.
   - Decentralized IPFS CID generation and pinning.
   - Blockchain anchoring storing transaction hashes, block numbers, and contract addresses.
   - Unauthenticated public verification endpoint (`GET /api/public/verify/{certificate_id}`) allowing consumers and field inspectors to verify authenticity instantly by scanning the SVG QR code.
   - Real-time cryptographic tamper detection flag (`is_verified` and `integrity_status`).

6. **Multilingual Voice & Computer Vision**:
   - 12 scheduled Indian languages supported for voice interaction (Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Odia, Assamese, English).
   - Computer vision conformity adapter analyzing rating plates and ISI mark geometry with audit disclaimers.
   - IoT test bench telemetry ingestion for automated laboratory test recording.

---

## ⚡ Quick Start & Local Execution

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+ (Python 3.14 compatible)

### Step 1: Backend Setup & Launch
```powershell
# Navigate to backend directory
cd backend

# Start FastAPI server using the virtual environment's python:
.\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
# (Alternatively, activate the venv first: .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8000)
```
*Backend API Documentation (Swagger) is available at: `http://localhost:8000/docs`*

### Step 2: Frontend Setup & Launch
```powershell
# Open a new terminal in the project root
npm install

# Start Vite development server
npm run dev
```
*Frontend UI will launch at: `http://localhost:5173`*

### Step 3: Run the Full Test Suite
```powershell
# Run the complete automated test suite (25 test modules covering all 5 phases)
.\backend\venv\Scripts\pytest backend\tests -v
```

---

## ⏱️ 5 to 7 Minute SIH Judge Demonstration Script

| Time | Stage | Action / Navigation | What to Highlight to Judges |
| :--- | :--- | :--- | :--- |
| **0:00 - 1:00** | **Authentication & Isolation** | Log in as manufacturer (`demo.manufacturer@havells-india.com`) | Point out OWASP PBKDF2 hashing, JWT bearer auth, and multi-tenant tenant isolation protecting competitor proprietary data. |
| **1:00 - 2:00** | **Document Upload & AI Extraction** | Navigate to Applications -> Create "Havells LED Bulb" -> Upload Test Report PDF | Show instant SHA-256 document hashing, multimodal parameter extraction, unit parsing, and source snippet tracing with confidence score. |
| **2:00 - 3:15** | **Standards Retrieval & Compliance Engine** | View matched standard `IS 16102 (Part 1) : 2012` -> Run Compliance Assessment | Highlight deterministic mathematical verification (no fake scores), critical clause penalties, and clause citation breakdown. |
| **3:15 - 4:15** | **Interactive Remediation & Checklist** | Remediate parameter (e.g., luminous efficacy to 85 lm/W) -> Click Recheck | Show dynamic score recalculation (jumps to 90%+), dynamic document checklist, and auditor verification workflow. |
| **4:15 - 5:15** | **Official BIS Forms & Dossier Export** | Click Generate Documents -> Export Complete Dossier | Show generated official BIS Form I, Form II, Form IV, and 14-section Technical Dossier with field provenance and downloadable ZIP bundle. |
| **5:15 - 6:30** | **Trust Ledger & Blockchain QR Verify** | Issue Certificate -> View Trust Ledger | Show canonical SHA-256 certificate hash, IPFS CIDv1 multihash, and blockchain transaction hash. Scan SVG QR code to open unauthenticated public verification page. |
| **6:30 - 7:00** | **Multilingual Voice & Tamper Detection** | Switch voice language to Hindi (`नमस्ते`) -> Run Tamper Verification | Demonstrate regulatory AI voice query in Indian languages and show cryptographic tamper alarm when a byte is altered. |

---

## 📊 PPT Feature Mapping Matrix

| # | SIH PPT Promised Feature | Backend Service / Route | Frontend Component / View | Status |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Manufacturer User Registration | `POST /api/auth/register` | `RegisterModal.tsx` | ✅ Verified |
| 2 | PBKDF2 Enterprise Password Hashing | `app.core.security.hash_password` | Form validation & login | ✅ Verified |
| 3 | Multi-Tenant Data Isolation | `get_application(id, user_id)` | Scoped dashboard views | ✅ Verified |
| 4 | Technical Document PDF Upload | `POST /api/applications/{id}/documents` | `FileUploadZone.tsx` | ✅ Verified |
| 5 | SHA-256 Document Hashing | `compute_sha256` in `DocumentService` | Document list badge | ✅ Verified |
| 6 | Multimodal Parameter Extraction | `POST /api/applications/{id}/extract` | `ParameterReviewTable.tsx` | ✅ Verified |
| 7 | Confidence Scoring & Source Tracking | `DocumentExtractor.extract_parameters` | Confidence indicator chips | ✅ Verified |
| 8 | Prompt Injection Guardrails | Structured XML delimiter tags | Sanitized prompt builder | ✅ Verified |
| 9 | BIS Standards Catalog Retrieval | `GET /api/standards` | `StandardSelector.tsx` | ✅ Verified |
| 10 | Clause-Level Requirements Extraction | `GET /api/standards/{id}` | Clause accordion view | ✅ Verified |
| 11 | Deterministic Physical Math Checking | `AssessmentEngine.run_compliance_analysis` | Compliance checklist table | ✅ Verified |
| 12 | Mathematical Readiness Scoring | Dynamic penalty/bonus weighting | `ReadinessScoreGauge.tsx` | ✅ Verified |
| 13 | Interactive Parameter Remediation | `POST /api/applications/{id}/recheck` | Interactive parameter slider | ✅ Verified |
| 14 | Citation-Backed RAG Chatbot | `POST /api/applications/{id}/chat` | `ContextualChatDrawer.tsx` | ✅ Verified |
| 15 | Dynamic Document Checklist | `GET /api/applications/{id}/checklist` | `DocumentChecklistCard.tsx` | ✅ Verified |
| 16 | Checklist Item Auditor Verification | `POST /api/applications/{id}/checklist/{item}/verify` | Verify/Reject buttons | ✅ Verified |
| 17 | Application Readiness Gate | `GET /api/applications/{id}/readiness` | Readiness status banner | ✅ Verified |
| 18 | Official BIS Form I Compilation | `FormGenerator.build_forms` | Forms preview tab | ✅ Verified |
| 19 | Official BIS Form II & IV Generation | `FormGenerator.build_forms` | Forms preview tab | ✅ Verified |
| 20 | 14-Section Technical Dossier | `FormGenerator._build_technical_dossier` | Technical Dossier view | ✅ Verified |
| 21 | Field-Level Provenance Tracking | `FormFieldProvenance` metadata | Provenance badge tags | ✅ Verified |
| 22 | Versioned Document Generation | `POST /api/applications/{id}/documents/generate` | Generated docs table | ✅ Verified |
| 23 | Application Dossier ZIP Export | `GET /api/applications/{id}/export-dossier` | "Export Full Dossier" button | ✅ Verified |
| 24 | Application Lifecycle State Machine | `PATCH /api/applications/{id}` | Status progression stepper | ✅ Verified |
| 25 | Canonical Certificate Representation | `compute_canonical_hash` | Canonical JSON view | ✅ Verified |
| 26 | Decentralized IPFS Pinning | `IPFSProvider` (`ipfs_provider.py`) | IPFS CID hash link | ✅ Verified |
| 27 | Blockchain Anchor (Block & Tx Hash) | `BlockchainProvider` (`blockchain_provider.py`) | Trust Ledger block badge | ✅ Verified |
| 28 | Unauthenticated Public QR Verification | `GET /api/public/verify/{cert_id}` | `TrustLedgerVerifyPage.tsx` | ✅ Verified |
| 29 | 12 Indian Languages Voice Support | `POST /api/applications/{id}/voice/query` | `VoiceAssistantModal.tsx` | ✅ Verified |
| 30 | Computer Vision Plate Verification | `POST /api/applications/{id}/vision/analyze` | `VisionAnalysisDrawer.tsx` | ✅ Verified |

---

## 🔒 Zero-Mock Guarantee
- Every single score, hash, CID, and verification result is computed dynamically.
- Zero mock/simulated data in production application paths.
- Cryptographic calculations use industry-standard SHA-256 and multihash CIDv1.
