import os
from typing import List, Dict

def _fallback_summary(scored: List[Dict]) -> str:
    top = scored[:5]
    lines = [f"- {t['ticketId']} | {t['dcId']} | {t['docCategory']} | due in {t['daysToDue']} days | risk {t['RiskBucket']} ({t['RiskScore']})"
             for t in top]
    return (
        "Executive Summary (fallback: no OPENAI_API_KEY):\n"
        f"Top {len(top)} risky tickets:\n" + "\n".join(lines) +
        "\n\nActions:\n- Escalate Critical within 24h\n- Reassign High risk to available owners\n- Add weekly check for categories trending to overdue"
    )

def exec_summary(scored: List[Dict]) -> str:
    """Returns an exec summary using OpenAI if key present; otherwise fallback."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_summary(scored)

    try:
        from langchain_openai import ChatOpenAI
        model = os.getenv("AI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model, temperature=0.2, api_key=api_key)

        bullets = "\n".join([
            f"- {t['ticketId']} | {t['dcId']} | {t['docCategory']} | due in {t['daysToDue']} days | risk {t['RiskBucket']} ({t['RiskScore']})"
            for t in scored[:8]
        ])

        prompt = (
            "You are an SRE/operations assistant. Produce a concise, executive summary of SLA risk for data centers. "
            "Include a 1-paragraph overview, a short prioritized list of the top risks, and 3 concrete next actions. "
            "Use neutral, professional language. Input tickets:\n"
            f"{bullets}"
        )
        return llm.invoke(prompt).content
    except Exception as e:
        return _fallback_summary(scored) + f"\n\n(Note: LLM call failed: {e})"
