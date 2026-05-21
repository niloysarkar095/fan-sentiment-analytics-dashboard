# 🌟 Live Fan Sentiment Analysis & Match Predictor Dashboard

A real-time, high-fidelity sports sentiment analytics and projection engine for **AFL (Australian Football League)** and **IPL (Indian Premier League)**. By dynamically listening to high-velocity fan commentary on Reddit, this system applies advanced natural language processing (NLP) to model dynamic public sway, project upcoming match winners, and evaluate demographic support cohorts in real time.

---

## 🏗️ Hybrid Architecture Summary

The platform is designed around a decoupled, highly resilient multi-service architecture:

```
                  ┌──────────────────────────────────────────────┐
                  │                 Reddit API                   │
                  └──────────────────────┬───────────────────────┘
                                         │ (Comment Stream)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          Headless Scraper Daemon             │
                  └──────────────────────┬───────────────────────┘
                                         │ (Buffer Ingestion)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │           Apache CouchDB Store               │
                  └──────────┬───────────┬────────────┬──────────┘
                             │           │            │
         (AFL Change Stream) │           │            │ (IPL Change Stream)
                             ▼           │            ▼
   ┌───────────────────────────┐         │   ┌───────────────────────────┐
   │    AFL Analyzer Engine    │         │   │    IPL Analyzer Engine    │
   │      (NLTK VADER NLP)     │         │   │      (NLTK VADER NLP)     │
   └─────────────┬─────────────┘         │   └────────────┬──────────────┘
                 │ (Sway Scores)         │                │ (Sway Scores)
                 ▼                       │                ▼
   ┌───────────────────────────┐         │   ┌───────────────────────────┐
   │    afl_scores Database    │         │   │    ipl_scores Database    │
   └─────────────┬─────────────┘         │   └────────────┬──────────────┘
                 │                       │                │
                 └──────────────┐        │        ┌───────┘
                                │        │        │
                                ▼        ▼        ▼
                  ┌──────────────────────────────────────────────┐
                  │             FastAPI Backend API              │
                  │             (Presentation Layer)             │
                  └──────────────────────┬───────────────────────┘
                                         │ (JSON Endpoints)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             Tailwind Frontend UI             │
                  │          (Real-Time Spotlight/Sway)          │
                  └──────────────────────────────────────────────┘
```

### 1. Presentation Layer (`dashboard/`)
- **FastAPI Presentation API**: A lightweight, high-performance API serving structured JSON endpoints for live, upcoming, and historical match data. Securely connects to CouchDB using environment variable configuration.
- **Dynamic Spotlight Engine**: Overhauled to provide intelligent pre-game previews when no match is active. Compares live, rolling fan sentiments to project the `Predicted Winner` ahead of start times.
- **Twin-Track Ledger**: A sleek, dark glassmorphic match listing that tracks AFL and IPL fixtures independently, showing micro-predictions for the absolute next game of each league.

### 2. Autonomous Ingestion & Process Pipelines (Excluded from Public Repo)
- **Headless Comment Scraper**: Connects to the Reddit API and streams live comments, maintaining constant throughput.
- **NLTK VADER Sentiment Analyzers**: Parallel continuous change listeners that process CouchDB raw queues. Equipped with custom `while True:` reconnect loops for 100% database stream resilience.
- **Match State Controller**: Manages database initialization, chronologically sorts fixtures, and settles predictions once matches conclude.

---

## 🛠️ Technology Stack

- **Backend API**: Python 3.10+, FastAPI, Uvicorn
- **Sentiment & NLP**: NLTK (VADER Sentiment Analysis)
- **Database Layer**: Apache CouchDB 3.x (Leveraging Mango JSON Indexing)
- **Frontend Presentation**: HTML5, Vanilla JavaScript (ES6), Tailwind CSS (CDN), Chart.js

---

## ⚡ Quick Start & Deployment

### 1. Prerequisites
- **Python**: Ensure Python 3.10+ is installed.
- **Database**: A running instance of Apache CouchDB 3.x with admin privileges.

### 2. Installation
Clone the repository and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root folder or set your environment variables directly to securely specify your CouchDB credentials:
```env
COUCHDB_URL=http://your_db_username:your_db_password@127.0.0.1:5984/
```
*Note: If no environment variable is provided, the API gracefully falls back to a secure local default (`http://admin:password123@127.0.0.1:5984/`).*

### 4. Running the Dashboard
To start the presentation server locally on port 8000:
```bash
python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8000
```
Open your browser and navigate to `http://127.0.0.1:8000` to view the live dashboard.

---

## 📁 Repository Structure

```
├── .gitignore             # Strict sanitization rules
├── README.md              # Technical presentation & overview
├── requirements.txt       # Production dependencies
└── dashboard/             # Presentation layer
    ├── app.py             # FastAPI backend implementation
    └── static/            
        └── index.html     # High-fidelity glassmorphic HTML/JS/CSS UI
```
