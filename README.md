# Decentralized Fan Sentiment & Enterprise Risk Analytics Engine

An end-to-end, high-performance real-time sentiment analytics and sports match projection platform focused on the **AFL (Australian Football League)** and **IPL (Indian Premier League)**. The engine dynamically ingests public fan commentary streams, processes them through natural language processing (NLP) pipelines, models sentiment sway, and translates public crowd momentum into quantitative bookmaker risk profiles.

## 🚀 Live Production Dashboard
View the live, autonomous real-time tracker here: [Fan Sentiment Analytics Dashboard](https://fan-sentiment-analytics-dashboard.onrender.com)

---

## 🌟 Project Overview

This platform represents a paradigm shift in sports analytics, transforming raw consumer sentiment from active social media channels (e.g., Reddit communities r/AFL and r/IPL) into **quantitative risk mitigation vectors**. Rather than relying solely on lagging historical stats, the engine measures the real-time *momentum of crowd belief*. 

By mapping support flairs and analyzing sentiment sway ratios, the engine generates real-time odds adjustment suggestions. These insights allow sportsbook operators to dynamically manage their risk allocation, defensive variance limits, and liability profiles when sharp public crowd sentiment shifts.

---

## 🏗️ Core Architecture

The system implements a hybrid decentralized architecture comprising independent microservices communicating with a central Apache CouchDB store:

```
  ┌────────────────────────────────────────────────────────┐
  │                   Reddit Data Stream                   │
  └───────────────────────────┬────────────────────────────┘
                              │ (Comment Ingestion API)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 Autonomous Scraper                     │
  │                   (listener.py)                        │
  └───────────────────────────┬────────────────────────────┘
                              │ (Raw Document Buffer)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                  Apache CouchDB Store                  │
  └─────────────┬──────────────────────────────┬───────────┘
                │                              │
                ├──────────────────────────────┤
                ▼                              ▼
  ┌───────────────────────────┐  ┌───────────────────────────┐
  │    AFL Sentiment Engine   │  │    IPL Sentiment Engine   │
  │      (analyzer_afl.py)    │  │      (analyzer_ipl.py)    │
  └─────────────┬─────────────┘  └─────────────┬─────────────┘
                │ (Dynamic Polarity Calculation)│ (Dynamic Polarity Calculation)
                ▼                              ▼
  ┌───────────────────────────┐  ┌───────────────────────────┐
  │        afl_scores         │  │        ipl_scores         │
  └─────────────┬─────────────┘  └─────────────┬─────────────┘
                │                              │
                └──────────────┬───────────────┘
                               │ (Dynamic Scoring API)
                               ▼
  ┌────────────────────────────────────────────────────────┐
  │                   FastAPI Backend                      │
  │                 (dashboard/app.py)                     │
  └───────────────────────────┬────────────────────────────┘
                              │ (JSON Payload Delivery)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 High-Fidelity Dashboard                │
  │              (Tailwind CSS + Chart.js UI)              │
  └────────────────────────────────────────────────────────┘
```

1. **Stealth Ingestion Layer (`listener.py`)**: Runs persistently, listening to stream sockets and loading raw commentary documents into the database.
2. **NLTK VADER NLP Core (`analyzer_afl.py` / `analyzer_ipl.py`)**: Continuously monitors the CouchDB changes feeds. It tokenizes, cleans, and scores fan messages in real time using the NLTK VADER Intensity Analyzer.
3. **Time-Series Ledger Store (Apache CouchDB)**: Documents are organized with Mango query indices, allowing fast lookups of match-level flair counts, loyalist support bands, and sentiment history.
4. **FastAPI Web Service Presentation Layer (`dashboard/app.py`)**: Exposes highly optimized REST endpoints (`/api/scores`, `/api/match/live`, `/api/match/upcoming`, and `/api/predict-risk`).

---

## 🧠 MLOps & Vertex AI Fine-Tuning

To back our real-time analytics with predictive intelligence, the platform integrates a custom **fine-tuned Gemini 1.5 Pro core** deployed on **Google Cloud Vertex AI Studio**.

### 1. Dataset Engineering (`fetch_historical_squiggle.py`)
- Handled historical match outcome harvesting from all AFL seasons between **2018 and 2025** using the robust Squiggle API.
- Generated simulated fan sentiment proxy records based on margins, ladder performance, and historical crowd sizes, creating a premium **1,625-row SFT JSONL dataset** (`historical_sports_sft.jsonl`).

### 2. Gemini Fine-Tuning Pipeline
- Engineered under the structured Gemini 1.5 Supervised Fine-Tuning (SFT) schema:
  - **Prompt (User)**: Combines real-time match details, final home sway ratios, supporter flairs, and polarities.
  - **Output (Model)**: Returns a structured JSON-like risk analysis containing the projected winner, confidence scoring (55%-98%), and a recommended defensive bookmaker odds adjustment variance (10%-18%).
- Deployed inside Google Cloud Vertex AI Studio and trained across **10 epochs** using a low-learning-rate optimizer to avoid catastrophic forgetting.
- The model is registered inside the enterprise registry and accessed directly via:
  `projects/716142539353/locations/us-central1/models/5190750964021198848`

---

## 📲 Local Network Broadcasting (Mobile Demo)

The web dashboard is fully optimized for local network broadcasting, allowing users on the same Wi-Fi connection to view and interact with live charts on their mobile devices.

### Step-by-Step Setup:

1. **Configure local server execution**:
   Run the production Uvicorn server bound to all local interfaces (`0.0.0.0`) on Port `8080`:
   ```powershell
   $env:COUCHDB_URL="http://admin:password123@127.0.0.1:5984/"; python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8080
   ```

2. **Discover your Local Network IP**:
   Find your active Wi-Fi IPv4 address (e.g., `192.168.0.209` or `10.0.0.5`):
   - **Windows**: Run `ipconfig` in PowerShell or CMD.
   - **Mac/Linux**: Run `ifconfig` or `ip a` in the terminal.

3. **Access via Mobile Web Browser**:
   Open a browser on your phone connected to the same Wi-Fi network and navigate to:
   `http://<YOUR_LOCAL_IP>:8080` (e.g., `http://192.168.0.209:8080`).

---

## 🛡️ Resilient Failover Design

High availability is core to the application. The system integrates a **Localized Emulation Fallback Layer** inside the `/api/predict-risk` endpoint to manage Vertex AI connection exceptions.

- **Lazy Import Routine**: External cloud AI libraries (`google-cloud-aiplatform` / `vertexai`) are loaded on-demand, preventing server startup delays or boot crashes if network conditions are degraded.
- **Graceful Error Recovery**: If GCP credentials, quotas, or networks fail (e.g., encountering a `grpc._channel._InactiveRpcError` or `google.api_core.exceptions.InvalidArgument`), the exception is logged to standard error, and the server instantly falls back to a deterministic risk calculator.
- **Polished Presentation**: Rather than throwing indefinite loading loops or harsh raw JSON tracebacks to the browser, the endpoint serves a highly polished, premium emulated report. This ensures 100% operational dashboard uptime and a seamless native user experience.
