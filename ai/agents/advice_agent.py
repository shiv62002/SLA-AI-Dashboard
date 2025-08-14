# ai/agents/advice_agent.py
import os, time, json
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from pydantic import BaseModel
from chromadb import Client
from chromadb.config import Settings
from chromadb.utils import embedding_functions

KB_DIR = os.path.join(os.path.dirname(__file__), '..', 'kb')
CHROMA_DIR = os.path.join(os.path.dirname(__file__), '..', '.chroma')
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---- Chroma setup ----
def _client():
    return Client(Settings(persist_directory=CHROMA_DIR))

def _collection():
    cl = _client()
    name = "kb_store"  # >=3 chars; [a-zA-Z0-9._-], starts/ends alnum
    # Prefer get_or_create to avoid races and one-off failures
    try:
        return cl.get_or_create_collection(name=name)
    except AttributeError:
        # older Chroma clients may not have get_or_create_collection
        try:
            return cl.get_collection(name)
        except Exception:
            return cl.create_collection(name=name, metadata={"hnsw:space": "cosine"})


def _embedder():
    # OpenAI embedding function
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBED_MODEL
    )

def reindex_kb() -> Dict[str, Any]:
    cl = _client()
    name = "kb_store"

    # Drop & recreate (newer Chroma rejects delete(where={}))
    try:
        cl.delete_collection(name)
    except Exception:
        pass

    col = cl.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})

    kb_dir = Path(__file__).resolve().parents[1] / "kb"
    files = sorted(list(kb_dir.glob("*.md")))
    if not files:
        return {"ok": False, "indexed": 0, "detail": "No *.md files found in ai/kb"}

    docs, ids, metas = [], [], []
    for i, p in enumerate(files):
        text = p.read_text(encoding="utf-8", errors="ignore")
        chunks = _chunk_markdown(text, chunk_size=800, overlap=100)
        for j, ch in enumerate(chunks):
            ids.append(f"{p.stem}-{i}-{j}")
            docs.append(ch)
            metas.append({"source": p.name})

    col.add(
        ids=ids,
        documents=docs,
        metadatas=metas,
        embeddings=None  # let server-side embed via embedding_function
    )
    return {"ok": True, "indexed": len(ids), "files": [p.name for p in files]}


def retrieve(topic: str, top_k: int = 3) -> List[Dict[str, str]]:
    try:
        col = _collection()
        if hasattr(col, "count") and col.count() == 0:
            return []
        res = col.query(query_texts=[topic], n_results=top_k, embedding_function=_embedder())
    except Exception:
        return []
    out = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    for i in range(len(docs)):
        out.append({"chunk": docs[i], "source": metas[i].get("source", "kb")})
    return out

# ---- Advice generation ----
class Ticket(BaseModel):
    ticketId: str
    dcId: str
    docCategory: str
    owner: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    dueDate: Optional[str] = None
    daysToDue: Optional[int] = None
    RiskScore: Optional[int] = None
    RiskBucket: Optional[str] = None

class Suggestion(BaseModel):
    ticketId: str
    rationale: str
    nextActions: List[str]
    suggestedOwner: Optional[str] = None
    urgency: str  # e.g., "Escalate in 24h", "Do this week"

def _rules_hint(t: Ticket) -> List[str]:
    hints = []
    d = t.daysToDue if t.daysToDue is not None else 999
    p = (t.priority or "Medium").lower()
    if d < 0:
        hints.append("Overdue: escalate to DC manager and schedule daily check-ins.")
    elif d <= 7:
        hints.append("Due ≤7d: assign backup owner and block a repair window.")
    elif d <= 21:
        hints.append("Due ≤21d: confirm dependencies and order parts now.")
    if p == "high":
        hints.append("High priority: page on-call and notify stakeholders.")
    return hints

def _compose_with_llm(t: Ticket, kb_snips: List[Dict[str, str]]) -> Suggestion:
    client = OpenAI(api_key=OPENAI_API_KEY)
    kb_text = "\n\n".join([f"[{s['source']}]\n{s['chunk']}" for s in kb_snips[:3]]) or "No KB found."
    sys = (
        "You are a data center operations SRE assistant. "
        "Propose concrete, low-risk steps that move work forward today. "
        "Prefer checklists, owners, and timeboxes. Keep each action short."
    )
    user = f"""
Ticket:
- id: {t.ticketId}
- dataCenter: {t.dcId}
- category: {t.docCategory}
- priority: {t.priority}
- daysToDue: {t.daysToDue}
- risk: {t.RiskBucket} ({t.RiskScore})

Local rules/hints:
{chr(10).join('- ' + h for h in _rules_hint(t))}

Knowledge Base (top matches):
{kb_text}

Output JSON with keys: rationale, nextActions (array of 3-6 steps), suggestedOwner, urgency.
"""
    resp = client.chat.completions.create(
        model=os.getenv("AI_MODEL","gpt-4o"),
        temperature=float(os.getenv("AI_MODEL_TEMPERATURE","0.1")),
        messages=[{"role":"system","content":sys},{"role":"user","content":user}],
        response_format={"type":"json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    # Normalize nextActions to list[str] for Pydantic
    raw_actions = data.get("nextActions", [])
    norm_actions = []
    for a in raw_actions:
        if isinstance(a, dict):
            step = (a.get("step") or a.get("action") or "").strip()
            tb = (a.get("timebox") or a.get("eta") or "").strip()
            s = step + (f" — {tb}" if tb else "")
            if s:
                norm_actions.append(s)
        else:
            s = str(a).strip()
            if s:
                norm_actions.append(s)

    return Suggestion(
        ticketId=t.ticketId,
        rationale=data.get("rationale", "")[:1000],
        nextActions=norm_actions[:6],  # <-- strings only
        suggestedOwner=data.get("suggestedOwner") or t.owner,
        urgency=data.get("urgency", "")
    )

def advise(tickets: List[Dict[str, Any]]) -> Tuple[List[Suggestion], List[str]]:
    # group topics by category for KB retrieval
    per = []
    sources_used = set()
    for td in tickets:
        t = Ticket(**td)
        topic = f"{t.docCategory} remediation runbook"
        kb = retrieve(topic, top_k=3)
        for k in kb: sources_used.add(k["source"])
        per.append(_compose_with_llm(t, kb))
    return per, sorted(list(sources_used))
