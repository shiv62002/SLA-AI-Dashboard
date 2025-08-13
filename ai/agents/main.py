from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=False)
from agents.fetch_agent import get_open_tickets
from agents.risk_agent import score_tickets
from agents.comms_agent import exec_summary

load_dotenv()
app = FastAPI(title="SLA AI Service", version="0.1")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/analyze")
def analyze():
    tickets = get_open_tickets()
    scored = score_tickets(tickets)
    return {"count": len(scored), "tickets": scored}

@app.get("/summarize")
def summarize():
    tickets = get_open_tickets()
    scored = score_tickets(tickets)
    summary = exec_summary(scored)
    return {"summary": summary}
