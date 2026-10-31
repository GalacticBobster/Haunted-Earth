"""Email alerts for shared places (SMTP; e.g. Gmail with an App Password).

.env:
  SMTP_HOST=smtp.gmail.com   SMTP_PORT=587   SMTP_USER=you@gmail.com   SMTP_PASS=<16-char app password>
  ALERT_FROM=you@gmail.com   APP_URL=https://your-app.streamlit.app   ALERT_MIN_LEVEL=1
"""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()
LEVEL_WORD = {1: "Advisory", 2: "Watch", 3: "Warning"}


def configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASS"))


def app_url() -> str:
    return os.getenv("APP_URL", "http://localhost:8501").rstrip("/")


def send(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = os.getenv("ALERT_FROM") or os.getenv("SMTP_USER")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    host, port = os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587"))
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=20) as s:
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
        return
    with smtplib.SMTP(host, port, timeout=20) as s:
        if os.getenv("SMTP_STARTTLS", "1") == "1":
            s.starttls(context=ssl.create_default_context())
        if os.getenv("SMTP_PASS") != "-":
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)


def _footer(pid: str) -> str:
    return (f"\n\nYour live page: {app_url()}/?me={pid}\n"
            f"Stop emails: {app_url()}/?unsub={pid}\n\n"
            "Haunted Earth is a hackathon demo. Estimates are not official warnings; always follow "
            "your local authorities and national warning centers.")


def welcome_email(place: dict) -> tuple[str, str]:
    return ("👻 Haunted Earth is watching your spot",
            f"Hi{(' ' + place['name']) if place.get('name') else ''},\n\n"
            f"Haunted Earth's Warden is now watching the area around "
            f"{place['lat']:.2f}, {place['lon']:.2f} for earthquakes, tsunamis, cyclones, humid heat, "
            f"wind, aurora and official alerts. You'll get an email when a warning is issued or upgraded."
            + _footer(place["id"]))


def change_email(place: dict, change) -> tuple[str, str]:
    word = LEVEL_WORD.get(change.level, "Update").upper()
    return (f"[{word}] {change.hazard}: {change.headline[:80]}",
            f"{word} {change.change} for {place.get('name') or 'your location'}:\n\n"
            f"{change.headline}\n" + _footer(place["id"]))
