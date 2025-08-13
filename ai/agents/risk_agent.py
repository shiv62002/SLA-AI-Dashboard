def score_tickets(tickets):
    """Add RiskScore and RiskBucket based on priority + days_to_due."""
    pri = {"Low":1,"Medium":2,"High":3}
    scored=[]
    for t in tickets:
        priority = pri.get(t.get("priority") or t.get("Priority") or "Medium", 2)
        days = t.get("daysToDue") or t.get("DaysToDue") or 999
        # days component: 0 (safe), 1 (near), 2 (urgent)
        days_component = 0 if days > 21 else (1 if days > 7 else 2 if days >= 0 else 3)
        score = priority*2 + days_component*3
        bucket = "Critical" if days_component==3 else ("High" if score>=7 else ("Medium" if score>=4 else "Low"))
        # normalize keys
        scored.append({
            "ticketId": t.get("ticketId"),
            "dcId": t.get("dcId"),
            "docCategory": t.get("docCategory"),
            "owner": t.get("owner"),
            "priority": t.get("priority"),
            "status": t.get("status"),
            "createdAt": t.get("createdAt"),
            "dueDate": t.get("dueDate"),
            "daysToDue": days,
            "RiskScore": score,
            "RiskBucket": bucket
        })
    return sorted(scored, key=lambda x: (x["RiskBucket"]!="Critical", x["RiskScore"]), reverse=True)
