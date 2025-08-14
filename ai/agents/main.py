from typing import Optional
from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv
from agents.fetch_agent import get_open_tickets
from agents.risk_agent import score_tickets

# Load env (WEBAPP_BASE, etc.)
load_dotenv(find_dotenv(), override=False)

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/analyze")
def analyze(dcId: Optional[str] = None):
    """Return tickets (optionally filtered by dcId) scored with RiskScore/RiskBucket."""
    tickets = get_open_tickets()
    if dcId:
        tickets = [t for t in tickets if t.get("dcId") == dcId]
    scored = score_tickets(tickets)
    return {"count": len(scored), "tickets": scored}

@app.get("/summarize")
def summarize(dcId: Optional[str] = None):
    """
    Local fallback summary (no LLM). If dcId is provided, summarize only that DC.
    """
    tickets = get_open_tickets()
    if dcId:
        tickets = [t for t in tickets if t.get("dcId") == dcId]

    scored = score_tickets(tickets)
    top = sorted(scored, key=lambda t: t.get("RiskScore", 0), reverse=True)[:4]

    scope = f" for {dcId}" if dcId else ""
    lines = []
    lines.append(f"Executive Summary (local fallback{scope}):")
    lines.append(f"Top {len(top)} risky tickets:")
    for t in top:
        tid    = t.get("ticketId", "N/A")
        dc     = t.get("dcId", "N/A")
        cat    = t.get("docCategory", "N/A")
        due    = t.get("daysToDue", "N/A")  # field name from your data
        bucket = t.get("RiskBucket", "N/A")
        score  = t.get("RiskScore", "N/A")
        lines.append(f"- {tid} | {dc} | {cat} | due in {due} days | risk {bucket} ({score})")

    lines.append("")
    lines.append("Actions:")
    lines.append("- Escalate Critical within 24h")
    lines.append("- Reassign High risk to available owners")
    lines.append("- Add weekly check for categories trending to overdue")

    return {"summary": "\n".join(lines)}

