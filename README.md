# Decentralized Fan Sentiment Analytics Engine

An end-to-end, high-performance real-time sentiment analytics and sports match projection platform focused on the **AFL (Australian Football League)** and **IPL (Indian Premier League)**.

The engine dynamically ingests public fan commentary streams from active social media channels (e.g., Reddit communities r/AFL and r/IPL), processes the text streams through resilient natural language processing (NLP) pipelines, models dynamic sentiment sway, and automatically computes pre-game predictive projections as well as support cohort profiles in real time.

---

## 🏗️ Architecture Design

The system implements a hybrid decentralized architecture comprising independent microservices communicating with a central Apache CouchDB store:

```
  ┌────────────────────────────────────────────────────────┐
  │                   Reddit Data Stream                   │
  └───────────────────────────┬────────────────────────────┘
                              │ (Comment Ingestion API)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 Autonomous Scraper                     │
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
  │      (NLTK VADER NLP)     │  │      (NLTK VADER NLP)     │
  └─────────────┬─────────────┘  └─────────────┬─────────────┘
                │ (Dynamic Sway Metrics)       │ (Dynamic Sway Metrics)
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
  │                 (Presentation Layer)                   │
  └───────────────────────────┬────────────────────────────┘
                              │ (JSON Payload Delivery)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 High-Fidelity Dashboard                │
  │               (Spotlight & Ledger UI)                  │
  └────────────────────────────────────────────────────────┘
```

### 1. Presentation & Delivery (`dashboard/`)
- **FastAPI Backend (`app.py`)**: Delivers highly optimized endpoints for scores, active live matches, pre-game previews, upcoming schedules, and historical records. Features secure runtime environment fallback setups.
- **Glassmorphic Frontend (`static/index.html`)**: A sleek, dark-mode visual interface styled using Tailwind CSS and interactive Chart.js widgets. It showcases real-time sentiment sways, support flairs, loyalist cohort support levels, and sports forecasts.

### 2. Autonomous Processing & Ingestion (Local Daemon Services)
- **Continuous Scraper Daemon (`listener.py`)**: Runs persistently, listening to stream sockets and loading raw commentary documents into the database.
- **Real-Time Sentiment Analyzers (`analyzer_afl.py` / `analyzer_ipl.py`)**: Continuously monitor changes feeds in the database. Equipped with `while True:` reconnect error catchers and backoff logic for total network resilience.
- **State Orchestrator (`match_controller.py` & `sync_schedule.py`)**: Auto-updates schedule ledgers, creates Mango indexes, manages active pre-game timelines, and evaluates post-match correctness.

---

## 🛠️ Technological Stack

- **Server Core**: Python 3.10+, FastAPI, Uvicorn
- **NLP Sentiment Analysis**: Natural Language Toolkit (NLTK VADER Intensity Analyzer)
- **Database Engine**: Apache CouchDB 3.x (Mango query indices)
- **Interface Layer**: HTML5, Modern ES6 JavaScript, Tailwind CSS, Chart.js

---

## ⚡ Deployment & Quick Start

### 1. Installation
Install the necessary requirements for the presentation backend:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variable
Securely configure your database credentials using a local environment variable:
```env
COUCHDB_URL=http://your_username:your_password@127.0.0.1:5984/
```
*If not set, the app defaults to a standard development connection (`http://admin:password123@127.0.0.1:5984/`).*

### 3. Start Presentation Server
Run the FastAPI application locally:
```bash
python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8000
```
Visit `http://127.0.0.1:8000` to interact with the real-time analytics UI.
