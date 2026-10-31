"""Durable actors for Haunted Earth (Terse durable-actors).

Haunt  - one actor per hazard event (actor id = event id). Holds the event's whole life story.
Globe  - one registry actor ("earth") that remembers every haunt id ever seen.

Each actor handles one call at a time, and persisted fields are saved after every call,
so agents can crash and restart without losing anything or racing each other.
"""
from durable_actors import Actor, persisted
from pydantic import BaseModel


class Reading(BaseModel):
    t: str
    severity: float
    status: str


class Article(BaseModel):
    id: str
    url: str
    title: str
    outlet: str
    published: str
    claims_json: str
    checked_by: list[str]


class HauntState(BaseModel):
    id: str
    kind: str
    title: str
    lat: float
    lon: float
    severity: float
    status: str
    first_seen: str
    last_seen: str
    sightings: int
    extra_json: str
    verdict: str
    analyzed_severity: float
    story: str
    history: list[Reading]
    consensus: str


class Haunt(Actor):
    kind: str = persisted("")
    title: str = persisted("")
    lat: float = persisted(0.0)
    lon: float = persisted(0.0)
    severity: float = persisted(0.0)
    status: str = persisted("")
    first_seen: str = persisted("")
    last_seen: str = persisted("")
    sightings: int = persisted(0)
    extra_json: str = persisted("{}")
    verdict: str = persisted("")
    analyzed_severity: float = persisted(-1.0)
    story: str = persisted("")
    story_verdict: str = persisted("")
    history: list[Reading] = persisted(default_factory=list)
    articles: list[Article] = persisted(default_factory=list)
    news_checked_at: str = persisted("")
    reports_json: str = persisted("{}")      # agency -> report (Corroborator)
    consensus: str = persisted("")
    alerts: list[str] = persisted(default_factory=list)   # county alerts already linked (Sentinel)

    def sight(self, kind: str, title: str, lat: float, lon: float, severity: float,
              status: str, seen_at: str, extra_json: str) -> str:
        """A scout reports this event. Returns 'new', 'changed' or 'same'."""
        is_new = self.sightings == 0
        changed = (not is_new) and (
            abs(severity - self.severity) > 0.02 or status != self.status
            or abs(lat - self.lat) > 0.05 or abs(lon - self.lon) > 0.05
        )
        if not is_new and not changed:
            return "same"            # read-only call: nothing is written, so it's fast
        if is_new:
            self.first_seen = seen_at
        self.kind, self.title, self.lat, self.lon = kind, title, lat, lon
        self.severity, self.status, self.extra_json = severity, status, extra_json
        self.last_seen = seen_at
        self.sightings += 1
        self.history.append(Reading(t=seen_at, severity=severity, status=status))
        return "new" if is_new else "changed"

    def needs_analysis(self) -> bool:
        return abs(self.severity - self.analyzed_severity) > 0.02 and self.status != "closed"

    def set_verdict(self, verdict: str) -> None:
        self.verdict = verdict
        self.analyzed_severity = self.severity

    def needs_story(self) -> bool:
        return bool(self.verdict) and self.story_verdict != self.verdict and self.status != "closed"

    def set_story(self, story: str, for_verdict: str) -> None:
        self.story = story
        self.story_verdict = for_verdict

    # ---- corroborator ----
    def add_report(self, agency: str, report_json: str) -> bool:
        """Store one agency's report of this quake. Returns True if it is new or changed."""
        import json
        reps = json.loads(self.reports_json)
        new = json.loads(report_json)
        if reps.get(agency) == new:
            return False
        reps[agency] = new
        self.reports_json = json.dumps(reps)
        return True

    def reports(self) -> str:
        return self.reports_json

    def set_consensus(self, text: str) -> None:
        self.consensus = text

    # ---- sentinel ----
    def add_alert(self, key: str) -> bool:
        """Link a county alert to this haunt once. Returns True the first time."""
        if key in self.alerts:
            return False
        self.alerts = self.alerts + [key]
        return True

    # ---- newsroom ----
    def last_news_check(self) -> str:
        return self.news_checked_at

    def add_articles(self, items_json: str, at: str) -> list[str]:
        """Herald files articles (JSON list). Returns ids of the ones that were new."""
        import json
        known = {a.id for a in self.articles}
        new = []
        for it in json.loads(items_json):
            if it["id"] in known:
                continue
            self.articles.append(Article(id=it["id"], url=it["url"], title=it["title"],
                                         outlet=it["outlet"], published=it.get("published", ""),
                                         claims_json=json.dumps(it.get("claims", [])), checked_by=[]))
            new.append(it["id"])
        self.articles = self.articles[-40:]
        self.news_checked_at = at
        return new

    def pending_articles(self, role: str) -> list[Article]:
        return [a for a in self.articles if role not in a.checked_by]

    def mark_checked(self, article_id: str, role: str) -> None:
        for a in self.articles:
            if a.id == article_id and role not in a.checked_by:
                a.checked_by.append(role)
        self.articles = list(self.articles)   # reassign so the change is persisted

    def list_articles(self) -> list[Article]:
        return self.articles

    def close(self, at: str) -> bool:
        """Scouts call this when an event disappears from its feed."""
        if self.status == "closed":
            return False
        self.status = "closed"
        self.history.append(Reading(t=at, severity=self.severity, status="closed"))
        return True

    def state(self) -> HauntState:
        return HauntState(
            id=self.id, kind=self.kind, title=self.title, lat=self.lat, lon=self.lon,
            severity=self.severity, status=self.status, first_seen=self.first_seen,
            last_seen=self.last_seen, sightings=self.sightings, extra_json=self.extra_json,
            verdict=self.verdict, analyzed_severity=self.analyzed_severity,
            story=self.story, history=self.history, consensus=self.consensus,
        )


class Globe(Actor):
    ids: list[str] = persisted(default_factory=list)
    scout_runs: int = persisted(0)

    def register(self, haunt_id: str) -> bool:
        if haunt_id in self.ids:
            return False
        self.ids.append(haunt_id)
        return True

    def all_ids(self) -> list[str]:
        return self.ids

    def scout_started(self) -> int:
        self.scout_runs += 1
        return self.scout_runs


class OutletLedger(BaseModel):
    outlet: str
    confirmed: int
    plausible: int
    mismatched: int
    implausible: int
    unverifiable: int


class Outlet(Actor):
    """One per news outlet (actor id = domain): a durable credibility ledger built from physics checks."""
    confirmed: int = persisted(0)
    plausible: int = persisted(0)
    mismatched: int = persisted(0)
    implausible: int = persisted(0)
    unverifiable: int = persisted(0)
    keys: list[str] = persisted(default_factory=list)

    def record(self, key: str, verdict: str) -> bool:
        """Count one checked claim once (idempotent on key). Returns True if it was new."""
        if key in self.keys:
            return False
        self.keys.append(key)
        field = {"CONFIRMED": "confirmed", "PLAUSIBLE": "plausible", "MISMATCH": "mismatched",
                 "IMPLAUSIBLE": "implausible"}.get(verdict, "unverifiable")
        setattr(self, field, getattr(self, field) + 1)
        return True

    def ledger(self) -> OutletLedger:
        return OutletLedger(outlet=self.id, confirmed=self.confirmed, plausible=self.plausible,
                            mismatched=self.mismatched, implausible=self.implausible,
                            unverifiable=self.unverifiable)


class WarningItem(BaseModel):
    key: str
    hazard: str
    level: int
    headline: str
    detail: str
    issued: str
    updated: str


class Change(BaseModel):
    key: str
    hazard: str
    change: str          # issued | upgraded | downgraded | expired
    level: int
    headline: str


class Place(Actor):
    """One per watched place. Remembers active warnings so it only alerts on real changes."""
    name: str = persisted("")
    lat: float = persisted(0.0)
    lon: float = persisted(0.0)
    active: list[WarningItem] = persisted(default_factory=list)
    log: list[Change] = persisted(default_factory=list)
    welcomed: str = persisted("")          # email address we already sent a welcome to

    def update(self, name: str, lat: float, lon: float, items_json: str, at: str) -> list[Change]:
        """Reconcile freshly computed threats with active warnings. Returns only the changes."""
        import json
        self.name, self.lat, self.lon = name, lat, lon
        new = {i["key"]: i for i in json.loads(items_json)}
        old = {w.key: w for w in self.active}
        changes: list[Change] = []
        kept: list[WarningItem] = []
        for k, i in new.items():
            o = old.get(k)
            if o is None:
                kind = "issued"
            elif i["level"] > o.level:
                kind = "upgraded"
            elif i["level"] < o.level:
                kind = "downgraded"
            else:
                kind = ""
            kept.append(WarningItem(key=k, hazard=i["hazard"], level=i["level"], headline=i["headline"],
                                    detail=i["detail"], issued=o.issued if o else at, updated=at))
            if kind:
                changes.append(Change(key=k, hazard=i["hazard"], change=kind, level=i["level"],
                                      headline=i["headline"]))
        for k, o in old.items():
            if k not in new:
                changes.append(Change(key=k, hazard=o.hazard, change="expired", level=0, headline=o.headline))
        self.active = kept
        if changes:
            self.log = (self.log + changes)[-60:]
        return changes

    def welcome(self, email: str) -> bool:
        """True the first time we see this email for this place (send a welcome once)."""
        if not email or self.welcomed == email:
            return False
        self.welcomed = email
        return True

    def warnings(self) -> list[WarningItem]:
        return self.active

    def history(self) -> list[Change]:
        return self.log


MISSION_MAX_DEPTH = 3   # follow-up tasks can nest at most this deep


class Task(BaseModel):
    id: str
    title: str
    role: str             # logistics | medic | comms | scout
    status: str           # pending | done
    depth: int
    parent: str
    result: str


class MissionState(BaseModel):
    id: str
    place_id: str
    place_name: str
    hazard: str
    level: int
    status: str           # active | stood down
    opened: str
    tasks: list[Task]


class Mission(Actor):
    """One relief mission per (place, hazard). Tasks can spawn follow-up tasks (bounded depth),
    so a warning grows its own plan; one call at a time keeps two workers off the same task."""
    place_id: str = persisted("")
    place_name: str = persisted("")
    hazard: str = persisted("")
    level: int = persisted(0)
    status: str = persisted("")
    opened: str = persisted("")
    tasks: list[Task] = persisted(default_factory=list)

    def open(self, place_id: str, place_name: str, hazard: str, level: int, at: str, seeds_json: str) -> bool:
        """Open (or re-open / escalate) the mission. Returns True if it was newly opened."""
        import json
        fresh = self.status != "active"
        self.place_id, self.place_name, self.hazard = place_id, place_name, hazard
        self.level = max(self.level, level) if not fresh else level
        if fresh:
            self.status, self.opened = "active", at
            if not self.tasks:
                for i, (title, role) in enumerate(json.loads(seeds_json)):
                    self.tasks = self.tasks + [Task(id=f"t{i + 1}", title=title, role=role, status="pending",
                                                    depth=0, parent="", result="")]
        return fresh

    def pending(self) -> list[Task]:
        return [t for t in self.tasks if t.status == "pending"] if self.status == "active" else []

    def complete(self, task_id: str, result: str, spawn_json: str) -> list[str]:
        """Finish a task and add its follow-ups (deduplicated, depth-limited). Returns new task ids."""
        import json
        tasks = list(self.tasks)
        parent = next((t for t in tasks if t.id == task_id), None)
        if parent is None or parent.status == "done":
            return []
        parent.status, parent.result = "done", result
        titles = {t.title for t in tasks}
        new_ids = []
        if parent.depth + 1 <= MISSION_MAX_DEPTH:
            for title, role in json.loads(spawn_json):
                if title in titles:
                    continue
                tid = f"{task_id}.{len([t for t in tasks if t.parent == task_id]) + 1}"
                tasks.append(Task(id=tid, title=title, role=role, status="pending",
                                  depth=parent.depth + 1, parent=task_id, result=""))
                titles.add(title)
                new_ids.append(tid)
        self.tasks = tasks
        return new_ids

    def stand_down(self) -> bool:
        if self.status != "active":
            return False
        self.status = "stood down"
        return True

    def state(self) -> MissionState:
        return MissionState(id=self.id, place_id=self.place_id, place_name=self.place_name,
                            hazard=self.hazard, level=self.level, status=self.status,
                            opened=self.opened, tasks=self.tasks)


class CrewState(BaseModel):
    name: str
    runs: int
    cycles: int
    last_action: str
    last_seen: str
    started: str


class Crew(Actor):
    """One per agent (actor id = agent name). Restarts and work done survive crashes."""
    runs: int = persisted(0)
    cycles: int = persisted(0)
    last_action: str = persisted("")
    last_seen: str = persisted("")
    started: str = persisted("")

    def start(self, at: str) -> int:
        self.runs += 1
        self.started = at
        self.last_seen = at
        return self.runs

    def beat(self, action: str, at: str) -> int:
        self.cycles += 1
        if action:
            self.last_action = action
        self.last_seen = at
        return self.cycles

    def state(self) -> CrewState:
        return CrewState(name=self.id, runs=self.runs, cycles=self.cycles, last_action=self.last_action,
                         last_seen=self.last_seen, started=self.started)
