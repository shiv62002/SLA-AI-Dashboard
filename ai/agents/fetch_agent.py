# agents/fetch_agent.py
import os
import requests
from typing import List, Dict, Any, Optional

WEBAPP_BASE = os.getenv("WEBAPP_BASE", "http://localhost:5168")

def get_open_tickets(dc_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Pulls open tickets from the webapp API. Optionally filters by datacenter.
    Normalizes key names to lowerCamelCase used by the AI layer.
    """
    params = {"status": "Open"}
    if dc_id:
        params["dc"] = dc_id  # maps to Program.cs /api/tickets?dc=...

    url = f"{WEBAPP_BASE}/api/tickets"
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    items = r.json()

    norm = []
    for t in items:
        # Normalize possible PascalCase from C# to lowerCamelCase
        norm.append({
            "ticketId":   t.get("ticketId")   or t.get("TicketId"),
            "dcId":       t.get("dcId")       or t.get("DcId"),
            "docCategory":t.get("docCategory")or t.get("DocCategory"),
            "owner":      t.get("owner")      or t.get("Owner"),
            "status":     t.get("status")     or t.get("Status"),
            "priority":   t.get("priority")   or t.get("Priority"),
            "createdAt":  t.get("createdAt")  or t.get("CreatedAt"),
            "dueDate":    t.get("dueDate")    or t.get("DueDate"),
            "daysToDue":  t.get("daysToDue")  or t.get("DaysToDue"),
        })
    return norm
