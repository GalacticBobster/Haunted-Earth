"""Agent Relay: the agents' chat channels, via the `agent-relay` CLI (local Relaycast server).

Channels:  #sightings  scout -> analyst      #verdicts  analyst -> narrator
           #stories    narrator -> everyone (the dashboard reads this too, through Supabase)
           #news       herald -> seismologist / meteorologist / spaceweather
           #factcheck  checkers -> judge
           #consensus  corroborator (USGS vs EMSC vs JMA vs GDACS)
           #alerts     sentinel (NWS county alerts near haunts)
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

AGENTS = ("scout", "analyst", "narrator", "herald", "seismologist", "meteorologist",
          "spaceweather", "judge", "corroborator", "sentinel", "warden", "quartermaster")
CHANNELS = {
    "sightings": ("scout", "analyst", "herald"),
    "verdicts": ("analyst", "narrator"),
    "stories": ("narrator", "scout", "analyst"),
    "news": ("herald", "seismologist", "meteorologist", "spaceweather"),      # herald -> checkers
    "factcheck": ("seismologist", "meteorologist", "spaceweather", "judge"),  # checkers -> judge
    "consensus": ("corroborator", "analyst", "seismologist"),  # multi-agency magnitude consensus
    "alerts": ("sentinel", "analyst", "narrator"),             # county alerts linked to haunts
    "warnings": ("warden", "sentinel", "narrator", "quartermaster"),  # place-specific warning changes
    "relief": ("quartermaster", "warden", "narrator"),         # relief missions and their tasks
}
TAG_RE = re.compile(r"\[(\w+)=([^\]]+)\]")
ID_RE = re.compile(r"\[id=([^\]]+)\]")


def _bin() -> str:
    b = shutil.which("agent-relay") or shutil.which("relay")
    if not b:
        raise RuntimeError("agent-relay CLI not found. Install: npm install -g agent-relay")
    return b


def _run(*args: str, check: bool = True) -> str:
    r = subprocess.run([_bin(), *args], capture_output=True, text=True, timeout=30)
    if check and r.returncode != 0:
        raise RuntimeError(f"agent-relay {' '.join(args[:2])} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def setup() -> None:
    """Register agents, create channels, join members. Safe to run repeatedly."""
    for a in AGENTS:
        _run("agent", "register", a, "--strict", check=False)  # never rotate a live token
    for ch, (owner, *members) in CHANNELS.items():
        _run("channel", "create", ch, "--as", owner, check=False)
        for m in members:
            _run("channel", "join", ch, "--as", m, check=False)


def post(channel: str, text: str, as_agent: str) -> None:
    _run("message", "post", channel, text, "--as", as_agent)


def read(channel: str, as_agent: str, limit: int = 50) -> list[dict]:
    """Messages oldest-first: [{id, text, sender, created_at}]."""
    out = _run("message", "list", channel, "--limit", str(limit), "--as", as_agent)
    start = out.find("[")
    msgs = json.loads(out[start:]) if start >= 0 else []
    rows = [{"id": m.get("id") or m.get("messageId"), "text": m.get("text", ""),
             "sender": (m.get("from") or {}).get("name", "?"), "created_at": m.get("createdAt")}
            for m in msgs]
    rows.sort(key=lambda m: int(m["id"]) if str(m["id"]).isdigit() else 0)
    return rows


def haunt_id(text: str) -> str | None:
    m = ID_RE.search(text)
    return m.group(1) if m else None


def tags(text: str) -> dict:
    """'[id=eq-1] [art=ab12] ...' -> {'id': 'eq-1', 'art': 'ab12'}"""
    return dict(TAG_RE.findall(text))
