# ai/agents/main.py  (only the new/changed parts shown)
import os, time, sqlite3
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from agents.fetch_agent import get_open_tickets
from agents.risk_agent import score_tickets
from agents.advice_agent import advise, reindex_kb
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "ai_monitor.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app = FastAPI(title="SLA AI Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS ai_runs(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TEXT,
      endpoint TEXT,
      model TEXT,
      prompt_tokens INTEGER,
      latency_ms INTEGER,
      status TEXT
    )""")
    return conn

@app.get("/kb/reindex")
def kb_reindex():
    return reindex_kb()

@app.get("/health")
def health():
    return {"ok": True, "llm": "ready"}

@app.get("/summarize")
def summarize(dcId: str | None = Query(default=None)):
    t0 = time.time()
    model = os.getenv("AI_MODEL", "gpt-4o")

    # 1) fetch + risk
    rows = get_open_tickets(dc_id=dcId)
    scored = score_tickets(rows)

    # 2) executive bullets (existing logic can stay as-is) ...
    top = sorted(scored, key=lambda x: (x["RiskBucket"]!="Critical", x["RiskScore"]), reverse=True)[:4]
    lines = [f"- {t['ticketId']} | {t['dcId']} | {t['docCategory']} | due in {t['daysToDue']} days | risk {t['RiskBucket']} ({t['RiskScore']})" for t in top]
    summary = "Executive Summary" + (f" (DC {dcId})" if dcId else " (Global)") + ":\nTop risky tickets:\n" + "\n".join(lines)

    # 3) advice (per-ticket + list of KB sources used)
    per_ticket, kb_sources = advise(scored[:8])  # cap to keep latency low

    latency = int((time.time() - t0)*1000)
    with _db() as conn:
        conn.execute("INSERT INTO ai_runs(ts,endpoint,model,prompt_tokens,latency_ms,status) VALUES(datetime('now'),'summarize',?,?,?,?)",
                     (model, 0, latency, "OK"))

    return {
      "summary": summary,
      "actions": [
        "Escalate Critical within 24h",
        "Reassign High risk to available owners",
        "Add weekly check for categories trending to overdue"
      ],
      "suggestedFilter": {},
      "suggestions": {
        "kbSources": kb_sources,
        "perTicket": [s.model_dump() for s in per_ticket],
        "globalTop3": _bubble_up(per_ticket)  
      }
    }

def _bubble_up(per_ticket):
    # synthesize 3 cross-ticket moves (simple heuristic)
    buckets = {"Escalate overdues":"Overdue", "Staff high-priority items":"High", "Order parts & confirm windows":"Medium"}
    out = []
    seen = 0
    for title, _ in buckets.items():
        out.append({"title": title, "why": "Aggregated from ticket advice", "steps": [
            "Confirm owner coverage and backups",
            "Notify DC manager",
            "Set checkpoint in 48h"
        ]})
        seen += 1
        if seen >= 3: break
    return out
