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
            story=self.story, history=self.history,
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
