import os, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

WEBAPP = os.getenv("WEBAPP_BASE", "http://localhost:5168")

_session = requests.Session()
retry = Retry(total=4, backoff_factor=0.5, status_forcelist=[429, 502, 503, 504])
_session.mount("http://", HTTPAdapter(max_retries=retry))
_session.mount("https://", HTTPAdapter(max_retries=retry))

def get_open_tickets(timeout=15):
    url = f"{WEBAPP}/api/tickets"
    try:
        r = _session.get(url, params={"status":"Open"}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Cannot reach web app at {url}. Is it running? ({e})")
