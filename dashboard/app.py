from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import couchdb
import os
try:
    import config
except ModuleNotFoundError:
    config = None
import requests
from datetime import datetime, timedelta

# Import analyzer logic to calculate live sentiment
try:
    from match_controller import get_mapped_team_general, get_team_doc_id
    from analyzer_afl import clean_text
except ModuleNotFoundError:
    pass
# from nltk.sentiment.vader import SentimentIntensityAnalyzer

CLOUD_CACHE = {"live": None, "upcoming": [], "history": []}

if config and hasattr(config, "COUCHDB_URL"):
    COUCHDB_URL = config.COUCHDB_URL
else:
    user = os.getenv("COUCHDB_USER", "admin")
    password = os.getenv("COUCHDB_PASSWORD", "password123")
    COUCHDB_URL = os.getenv("COUCHDB_URL", f"http://{user}:{password}@couchdb-db:5984/")

app = FastAPI(title="AFL/IPL Real-Time Sentiment Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine the absolute path to the static directory
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# sia = SentimentIntensityAnalyzer()

@app.on_event("startup")
def startup_event():
    # Wrap the index creation logic with a strict 2-second timeout connection check using 'couch.version()'
    try:
        session = couchdb.Session(timeout=2)
        couch = couchdb.Server(COUCHDB_URL, session=session)
        couch.version()
    except Exception:
        print("[STARTUP] CouchDB offline. Skipping index allocation, operating in Cache Mode.")
        return

    # Ensure Mango Index for link_id in databases
    index_payload = {
        "index": {"fields": ["link_id"]},
        "name": "link_id-index",
        "type": "json"
    }
    
    afl_db_name = config.COUCHDB_DB_NAME if (config and hasattr(config, "COUCHDB_DB_NAME")) else "reddit_afl"
    databases = [
        afl_db_name,
        "reddit_ipl"
    ]
    
    for db_name in databases:
        raw_db_url = COUCHDB_URL.rstrip('/') + '/' + db_name
        try:
            requests.post(f"{raw_db_url}/_index", json=index_payload, timeout=2)
            print(f"Confirmed Mango index on 'link_id' for {db_name}.")
        except Exception as e:
            print(f"Warning: Failed to create index on link_id for {db_name} in app startup: {e}")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.post("/api/update-cloud-cache")
async def update_cloud_cache(payload: dict):
    global CLOUD_CACHE
    CLOUD_CACHE = payload
    return {"status": "Data synced successfully"}

@app.get("/api/scores")
def get_scores():
    try:
        couch = couchdb.Server(COUCHDB_URL)
        couch.version() # Force connection check
        payload = {
            "AFL": [],
            "IPL": []
        }

        # Fetch AFL scores
        if "afl_scores" in couch:
            db_afl = couch["afl_scores"]
            for doc_id in db_afl:
                if not doc_id.startswith('_design/'):
                    doc = db_afl[doc_id]
                    payload["AFL"].append({
                        "team_name": doc.get("team_name", "Unknown"),
                        "average_sentiment": doc.get("average_sentiment", 0.0),
                        "comment_count": doc.get("comment_count", 0)
                    })
                    
        # Fetch IPL scores gracefully
        if "ipl_scores" in couch:
            db_ipl = couch["ipl_scores"]
            for doc_id in db_ipl:
                if not doc_id.startswith('_design/'):
                    doc = db_ipl[doc_id]
                    payload["IPL"].append({
                        "team_name": doc.get("team_name", "Unknown"),
                        "average_sentiment": doc.get("average_sentiment", 0.0),
                        "comment_count": doc.get("comment_count", 0)
                    })

        return payload
    except Exception as e:
        return CLOUD_CACHE.get("scores", {"AFL": [], "IPL": []})

def fetch_basic_live_match(couch, fix, league, is_preview=False):
    home_id = fix.get("home_team")
    away_id = fix.get("away_team")
    
    # Global Sway
    global_home, global_away = 0.0, 0.0
    scores_db_name = "afl_scores" if league == "AFL" else "ipl_scores"
    if scores_db_name in couch:
        db_scores = couch[scores_db_name]
        if home_id in db_scores:
            global_home = db_scores[home_id].get("average_sentiment", 0.0)
        if away_id in db_scores:
            global_away = db_scores[away_id].get("average_sentiment", 0.0)
            
    res = {
        "status": "active",
        "fixture_id": fix.get("_id"),
        "match_time": fix.get("match_time"),
        "home_team": home_id,
        "away_team": away_id,
        "global_sway": {"home": global_home, "away": global_away},
        "is_preview": is_preview
    }
    if "prediction_snapshot" in fix:
        res["prediction_snapshot"] = fix["prediction_snapshot"]
    if "sway_history" in fix:
        res["sway_history"] = fix["sway_history"]
    return res



@app.get("/api/match/live")
def get_live_match():
    try:
        couch = couchdb.Server(COUCHDB_URL)
        couch.version() # Force connection check
        payload = {"AFL": None, "IPL": None}
        
        if "match_fixtures" not in couch:
            return payload
            
        db_fixtures = couch["match_fixtures"]
        
        afl_active = []
        ipl_active = []
        
        for doc_id in db_fixtures:
            if not doc_id.startswith('_design/'):
                doc = db_fixtures[doc_id]
                if doc.get('status') == 'active':
                    if doc.get('league') == 'AFL':
                        afl_active.append(doc)
                    elif doc.get('league') == 'IPL':
                        ipl_active.append(doc)
                        
        # Sort active matches by match_time ascending
        afl_active.sort(key=lambda x: x.get('match_time', ''))
        ipl_active.sort(key=lambda x: x.get('match_time', ''))
        
        now = datetime.now()
        two_hours_limit = timedelta(hours=2)
        
        active_afl = None
        is_afl_preview = False
        for doc in afl_active:
            mtime_str = doc.get('match_time')
            if mtime_str:
                try:
                    mtime = datetime.fromisoformat(mtime_str)
                    if now >= mtime or (mtime - now) <= two_hours_limit:
                        active_afl = doc
                        break
                except Exception:
                    continue
                    
        if not active_afl and afl_active:
            active_afl = afl_active[0]
            is_afl_preview = True

        active_ipl = None
        is_ipl_preview = False
        for doc in ipl_active:
            mtime_str = doc.get('match_time')
            if mtime_str:
                try:
                    mtime = datetime.fromisoformat(mtime_str)
                    if now >= mtime or (mtime - now) <= two_hours_limit:
                        active_ipl = doc
                        break
                except Exception:
                    continue

        if not active_ipl and ipl_active:
            active_ipl = ipl_active[0]
            is_ipl_preview = True
                    
        if active_afl:
            payload["AFL"] = fetch_basic_live_match(couch, active_afl, "AFL", is_preview=is_afl_preview)
        if active_ipl:
            payload["IPL"] = fetch_basic_live_match(couch, active_ipl, "IPL", is_preview=is_ipl_preview)
            
        return payload
    except Exception as e:
        return CLOUD_CACHE.get("live", {"AFL": None, "IPL": None})

@app.get("/api/match/upcoming")
def get_match_upcoming():
    try:
        couch = couchdb.Server(COUCHDB_URL)
        couch.version() # Force connection check
        if "match_fixtures" not in couch:
            return []
            
        db_fixtures = couch["match_fixtures"]
        
        upcoming = []
        for doc_id in db_fixtures:
            if not doc_id.startswith('_design/'):
                doc = db_fixtures[doc_id]
                if doc.get('status') == 'active':
                    upcoming.append(doc)
                    
        # Sort by match_time ascending
        upcoming.sort(key=lambda x: x.get('match_time', ''))
        return upcoming
    except Exception as e:
        return CLOUD_CACHE.get("upcoming", [])

@app.get("/api/match/history")
def get_match_history():
    try:
        couch = couchdb.Server(COUCHDB_URL)
        couch.version() # Force connection check
        if "match_fixtures" not in couch:
            return []
            
        db_fixtures = couch["match_fixtures"]
        
        history = []
        for doc_id in db_fixtures:
            if not doc_id.startswith('_design/'):
                doc = db_fixtures[doc_id]
                if doc.get('status') == 'completed':
                    history.append(doc)
                    
        # Sort by match_time descending
        history.sort(key=lambda x: x.get('match_time', ''), reverse=True)
        return history
    except Exception as e:
        return CLOUD_CACHE.get("history", [])

TUNED_MODEL_ID = "projects/716142539353/locations/us-central1/models/5190750964021198848"

@app.post("/api/predict-risk")
async def predict_risk(payload: dict):
    home_team = payload.get("home_team", "Unknown")
    away_team = payload.get("away_team", "Unknown")
    home_sway = float(payload.get("home_sway", 0.0))
    away_sway = float(payload.get("away_sway", 0.0))
    sway_ratio = float(payload.get("sway_ratio", 50.0))
    
    home_fans = float(payload.get("home_fans", 45.0))
    away_fans = float(payload.get("away_fans", 40.0))
    neutral_fans = float(payload.get("neutral_fans", 15.0))
    
    # Safe team format
    home_name = home_team.replace("_", " ").title()
    away_name = away_team.replace("_", " ").title()
        
    prompt = (
        f"Analyze the following real-time fan sentiment metrics and demographic distributions to project the match winner and optimize betting odds risk allocation.\n\n"
        f"Match: {home_name} vs {away_name}\n"
        f"Sway Ratio: {sway_ratio:.1f}% Home\n"
        f"Demographics: Home Fans ({home_fans:.1f}%), Away Fans ({away_fans:.1f}%), Neutrals ({neutral_fans:.1f}%)\n"
        f"Final Pre-Game Sentiment: Home ({home_sway:.3f}), Away ({away_sway:.3f})"
    )
    
    try:
        from google.cloud import aiplatform
        import vertexai
        from vertexai.generative_models import GenerativeModel, Content, Part
        
        # Explicitly initialize Vertex AI SDK with the project and region
        vertexai.init(project="716142539353", location="us-central1")
        
        # Instantiate GenerativeModel using the exact fine-tuned tuned resource path
        model = GenerativeModel(TUNED_MODEL_ID)
        contents = [Content(role="user", parts=[Part.from_text(prompt)])]
        response = model.generate_content(contents)
        prediction_text = response.text
        return {"risk_analysis": prediction_text, "mode": "Vertex Live"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Determine fallback predictor details
        predicted_winner = home_name if home_sway > away_sway else away_name
        sentiment_diff = abs(home_sway - away_sway)
        defensive_variance = max(10, min(18, int(sentiment_diff * 40 + 10)))
        confidence = max(55.0, min(98.0, 50.0 + sentiment_diff * 120.0))
        
        fallback_text = (
            f"**Predicted Winner**: {predicted_winner}\n\n"
            f"**Analysis**: The community supporter sentiment intensity for {predicted_winner} demonstrated a positive average polarity "
            f"differential of `{sentiment_diff:.3f}` relative to their opponent, indicating robust pre-match network momentum. "
            f"Additionally, active supporter cohort counts and flair allegiances strongly back {predicted_winner} with "
            f"{home_fans if predicted_winner == home_name else away_fans:.1f}% of total active participants, locking in "
            f"quantifiable pre-game optimism.\n\n"
            f"**Risk Management Recommendation**: Adjust match opening odds to favor {predicted_winner} by a defensive variance "
            f"of `{defensive_variance}%` to mitigate late-stage sharp crowd momentum liability. "
            f"Confidence rating is evaluated at `{confidence:.1f}%`."
        )
        return {"risk_analysis": fallback_text, "mode": "Local Emulation Fallback"}


if __name__ == "__main__":
    import uvicorn
    import os
    # Read Render's dynamic port environment variable, default to 8000 for local PC use
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
