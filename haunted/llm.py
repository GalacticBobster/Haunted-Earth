"""Narrator's voice. OpenAI cloud if OPENAI_API_KEY is set, else local Ollama, else a template.

The physics numbers never come from the LLM: it only rewrites the Analyst's verdict as a line.
"""
from __future__ import annotations

import os
import random

from dotenv import load_dotenv

load_dotenv()

SYSTEM = (
    "You are the Narrator of Haunted Earth, a Halloween globe of live natural hazards. "
    "Write ONE spooky, vivid sentence (max 35 words) about the event. "
    "Use ONLY the numbers given in the verdict, never invent new facts or numbers. "
    "Be respectful: real people may be affected, so be eerie, never mocking."
)


def _client():
    from openai import OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return OpenAI(timeout=30), os.getenv("LLM_MODEL", "gpt-5-mini")
    base = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    return OpenAI(base_url=base, api_key="ollama", timeout=60), os.getenv("LLM_MODEL", "gpt-oss:20b")


def _template(title: str, kind: str, verdict: str) -> str:
    """Offline narrator: still uses only the Analyst's numbers."""
    parts = [p.strip() for p in verdict.split(";") if p.strip()]
    place = title.split(" of ")[-1] if " of " in title else title
    pick = lambda key: next((p for p in parts if key in p), "")  # noqa: E731
    if kind == "earthquake":
        energy, echo = pick("energy"), pick("aftershock ~")
        return (f"The ground beneath {place} groans, {energy}"
                + (f"; a smaller echo, {echo.replace('largest aftershock ', '')}, may follow." if echo else "."))
    if kind == "volcano":
        return f"Fire stirs beneath {place}; the mountain's eye has opened and it is watching."
    if kind == "wildfire":
        return f"Smoke-ghosts rise over {place}, drifting wherever the wind commands."
    if kind == "storm":
        return f"A howling spirit circles {place}" + (f", {parts[0]}." if parts and "kts" in parts[0] else ".")
    if kind == "aurora":
        return f"Green ghosts dance across the northern sky: {parts[0] if parts else verdict}."
    opener = random.choice(["Something stirs", "An eye opens", "The planet shivers", "A restless spirit wakes"])
    return f"{opener} over {place}" + (f": {parts[0]}." if parts else ".")


def narrate(title: str, kind: str, verdict: str) -> tuple[str, str]:
    """Return (story, source) where source is the model name or 'template'."""
    if not os.getenv("OPENAI_API_KEY") and os.getenv("LLM_LOCAL") != "1":
        return _template(title, kind, verdict), "template"   # fast path: no local 20B model
    try:
        client, model = _client()
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": f"Event: {title} ({kind})\nVerdict: {verdict}"}],
        )
        text = (r.choices[0].message.content or "").strip().strip('"')
        if text:
            return text, model
    except Exception:
        pass
    return _template(title, kind, verdict), "template"
