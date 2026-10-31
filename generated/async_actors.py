"""Typed async actor handles sharing the synchronous namespace models."""
from __future__ import annotations
import builtins as _builtins
from typing import TypeAlias as _TypeAlias, Literal as _Literal
from durable_actors.async_client import AsyncActorTransport as _ActorTransport
from durable_actors.generated import Unset as _Unset
from durable_actors.proxy import prepare_async_authorization as _prepare_authorization
from durable_actors.client import SocketGrant as _SocketGrant
from pydantic import TypeAdapter as _TypeAdapter
from . import actors as _sync_actors
from . import _crew as _client_0
from . import _crew_models as _models_0

class Crew:
    """One per agent (actor id = agent name). Restarts and work done survive crashes."""
    Stub: _TypeAlias = _client_0.AsyncStub
    Metadata: _TypeAlias = _models_0.SocketMetadata
    Incoming: _TypeAlias = _models_0.SocketIncoming
    Outgoing: _TypeAlias = _models_0.SocketOutgoing
    State: _TypeAlias = _models_0.SocketState
    EmittedState: _TypeAlias = _models_0.SocketEmittedState
    StatePatch: _TypeAlias = _models_0.SocketStatePatch
    CrewState: _TypeAlias = _models_0.CrewState

    @_builtins.staticmethod
    def get(actor_id: _builtins.str, transport: _ActorTransport | None = None) -> _client_0.AsyncStub:
        """Return a async actor handle without sending a request.
        
        Args:
            actor_id: Identity of the actor to call.
            transport: Optional caller-owned transport. Uses the SDK-managed
                transport when omitted.
        
        The returned Stub provides the actor's typed RPC methods.
        """
        return _client_0.AsyncStub(actor_id, transport)

    Authorization: _TypeAlias = _sync_actors.Crew.Authorization

    @_builtins.staticmethod
    async def prepare_websocket(authorization: Crew.Authorization, transport: _ActorTransport | None = None) -> _SocketGrant:
        """Issue browser access after authenticating the user and authorizing this actor."""
        return await _prepare_authorization(_TypeAdapter(Crew.Authorization).validate_python(authorization), transport)

    class Methods:
        """Argument tuples and return types for each actor RPC."""
        class beat:
            """Types for Crew.beat."""
            Args: _TypeAlias = _builtins.tuple[_models_0.RpcMethodBeatParameter0, _models_0.RpcMethodBeatParameter1]
            Result: _TypeAlias = _models_0.RpcMethodBeatResult

        class start:
            """Types for Crew.start."""
            Args: _TypeAlias = _builtins.tuple[_models_0.RpcMethodStartParameter0]
            Result: _TypeAlias = _models_0.RpcMethodStartResult

        class state:
            """Types for Crew.state."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_0.RpcMethodStateResult

from . import _globe as _client_1
from . import _globe_models as _models_1

class Globe:
    """Clients and types for Globe actors."""
    Stub: _TypeAlias = _client_1.AsyncStub
    Metadata: _TypeAlias = _models_1.SocketMetadata
    Incoming: _TypeAlias = _models_1.SocketIncoming
    Outgoing: _TypeAlias = _models_1.SocketOutgoing
    State: _TypeAlias = _models_1.SocketState
    EmittedState: _TypeAlias = _models_1.SocketEmittedState
    StatePatch: _TypeAlias = _models_1.SocketStatePatch

    @_builtins.staticmethod
    def get(actor_id: _builtins.str, transport: _ActorTransport | None = None) -> _client_1.AsyncStub:
        """Return a async actor handle without sending a request.
        
        Args:
            actor_id: Identity of the actor to call.
            transport: Optional caller-owned transport. Uses the SDK-managed
                transport when omitted.
        
        The returned Stub provides the actor's typed RPC methods.
        """
        return _client_1.AsyncStub(actor_id, transport)

    Authorization: _TypeAlias = _sync_actors.Globe.Authorization

    @_builtins.staticmethod
    async def prepare_websocket(authorization: Globe.Authorization, transport: _ActorTransport | None = None) -> _SocketGrant:
        """Issue browser access after authenticating the user and authorizing this actor."""
        return await _prepare_authorization(_TypeAdapter(Globe.Authorization).validate_python(authorization), transport)

    class Methods:
        """Argument tuples and return types for each actor RPC."""
        class all_ids:
            """Types for Globe.all_ids."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_1.RpcMethodAllIdsResult

        class register:
            """Types for Globe.register."""
            Args: _TypeAlias = _builtins.tuple[_models_1.RpcMethodRegisterParameter0]
            Result: _TypeAlias = _models_1.RpcMethodRegisterResult

        class scout_started:
            """Types for Globe.scout_started."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_1.RpcMethodScoutStartedResult

from . import _haunt as _client_2
from . import _haunt_models as _models_2

class Haunt:
    """Clients and types for Haunt actors."""
    Stub: _TypeAlias = _client_2.AsyncStub
    Metadata: _TypeAlias = _models_2.SocketMetadata
    Incoming: _TypeAlias = _models_2.SocketIncoming
    Outgoing: _TypeAlias = _models_2.SocketOutgoing
    State: _TypeAlias = _models_2.SocketState
    EmittedState: _TypeAlias = _models_2.SocketEmittedState
    StatePatch: _TypeAlias = _models_2.SocketStatePatch
    Article: _TypeAlias = _models_2.Article
    Reading: _TypeAlias = _models_2.Reading
    HauntState: _TypeAlias = _models_2.HauntState

    @_builtins.staticmethod
    def get(actor_id: _builtins.str, transport: _ActorTransport | None = None) -> _client_2.AsyncStub:
        """Return a async actor handle without sending a request.
        
        Args:
            actor_id: Identity of the actor to call.
            transport: Optional caller-owned transport. Uses the SDK-managed
                transport when omitted.
        
        The returned Stub provides the actor's typed RPC methods.
        """
        return _client_2.AsyncStub(actor_id, transport)

    Authorization: _TypeAlias = _sync_actors.Haunt.Authorization

    @_builtins.staticmethod
    async def prepare_websocket(authorization: Haunt.Authorization, transport: _ActorTransport | None = None) -> _SocketGrant:
        """Issue browser access after authenticating the user and authorizing this actor."""
        return await _prepare_authorization(_TypeAdapter(Haunt.Authorization).validate_python(authorization), transport)

    class Methods:
        """Argument tuples and return types for each actor RPC."""
        class add_alert:
            """Link a county alert to this haunt once. Returns True the first time."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodAddAlertParameter0]
            Result: _TypeAlias = _models_2.RpcMethodAddAlertResult

        class add_articles:
            """Herald files articles (JSON list). Returns ids of the ones that were new."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodAddArticlesParameter0, _models_2.RpcMethodAddArticlesParameter1]
            Result: _TypeAlias = _models_2.RpcMethodAddArticlesResult

        class add_report:
            """Store one agency's report of this quake. Returns True if it is new or changed."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodAddReportParameter0, _models_2.RpcMethodAddReportParameter1]
            Result: _TypeAlias = _models_2.RpcMethodAddReportResult

        class close:
            """Scouts call this when an event disappears from its feed."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodCloseParameter0]
            Result: _TypeAlias = _models_2.RpcMethodCloseResult

        class last_news_check:
            """Types for Haunt.last_news_check."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_2.RpcMethodLastNewsCheckResult

        class list_articles:
            """Types for Haunt.list_articles."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_2.RpcMethodListArticlesResult

        class mark_checked:
            """Types for Haunt.mark_checked."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodMarkCheckedParameter0, _models_2.RpcMethodMarkCheckedParameter1]
            Result: _TypeAlias = None

        class needs_analysis:
            """Types for Haunt.needs_analysis."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_2.RpcMethodNeedsAnalysisResult

        class needs_story:
            """Types for Haunt.needs_story."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_2.RpcMethodNeedsStoryResult

        class pending_articles:
            """Types for Haunt.pending_articles."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodPendingArticlesParameter0]
            Result: _TypeAlias = _models_2.RpcMethodPendingArticlesResult

        class reports:
            """Types for Haunt.reports."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_2.RpcMethodReportsResult

        class set_consensus:
            """Types for Haunt.set_consensus."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodSetConsensusParameter0]
            Result: _TypeAlias = None

        class set_story:
            """Types for Haunt.set_story."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodSetStoryParameter0, _models_2.RpcMethodSetStoryParameter1]
            Result: _TypeAlias = None

        class set_verdict:
            """Types for Haunt.set_verdict."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodSetVerdictParameter0]
            Result: _TypeAlias = None

        class sight:
            """A scout reports this event. Returns 'new', 'changed' or 'same'."""
            Args: _TypeAlias = _builtins.tuple[_models_2.RpcMethodSightParameter0, _models_2.RpcMethodSightParameter1, _models_2.RpcMethodSightParameter2, _models_2.RpcMethodSightParameter3, _models_2.RpcMethodSightParameter4, _models_2.RpcMethodSightParameter5, _models_2.RpcMethodSightParameter6, _models_2.RpcMethodSightParameter7]
            Result: _TypeAlias = _models_2.RpcMethodSightResult

        class state:
            """Types for Haunt.state."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_2.RpcMethodStateResult

from . import _mission as _client_3
from . import _mission_models as _models_3

class Mission:
    """One relief mission per (place, hazard). Tasks can spawn follow-up tasks (bounded depth),
    so a warning grows its own plan; one call at a time keeps two workers off the same task.
    """
    Stub: _TypeAlias = _client_3.AsyncStub
    Metadata: _TypeAlias = _models_3.SocketMetadata
    Incoming: _TypeAlias = _models_3.SocketIncoming
    Outgoing: _TypeAlias = _models_3.SocketOutgoing
    State: _TypeAlias = _models_3.SocketState
    EmittedState: _TypeAlias = _models_3.SocketEmittedState
    StatePatch: _TypeAlias = _models_3.SocketStatePatch
    Task: _TypeAlias = _models_3.Task
    MissionState: _TypeAlias = _models_3.MissionState

    @_builtins.staticmethod
    def get(actor_id: _builtins.str, transport: _ActorTransport | None = None) -> _client_3.AsyncStub:
        """Return a async actor handle without sending a request.
        
        Args:
            actor_id: Identity of the actor to call.
            transport: Optional caller-owned transport. Uses the SDK-managed
                transport when omitted.
        
        The returned Stub provides the actor's typed RPC methods.
        """
        return _client_3.AsyncStub(actor_id, transport)

    Authorization: _TypeAlias = _sync_actors.Mission.Authorization

    @_builtins.staticmethod
    async def prepare_websocket(authorization: Mission.Authorization, transport: _ActorTransport | None = None) -> _SocketGrant:
        """Issue browser access after authenticating the user and authorizing this actor."""
        return await _prepare_authorization(_TypeAdapter(Mission.Authorization).validate_python(authorization), transport)

    class Methods:
        """Argument tuples and return types for each actor RPC."""
        class complete:
            """Finish a task and add its follow-ups (deduplicated, depth-limited). Returns new task ids."""
            Args: _TypeAlias = _builtins.tuple[_models_3.RpcMethodCompleteParameter0, _models_3.RpcMethodCompleteParameter1, _models_3.RpcMethodCompleteParameter2]
            Result: _TypeAlias = _models_3.RpcMethodCompleteResult

        class open:
            """Open (or re-open / escalate) the mission. Returns True if it was newly opened."""
            Args: _TypeAlias = _builtins.tuple[_models_3.RpcMethodOpenParameter0, _models_3.RpcMethodOpenParameter1, _models_3.RpcMethodOpenParameter2, _models_3.RpcMethodOpenParameter3, _models_3.RpcMethodOpenParameter4, _models_3.RpcMethodOpenParameter5]
            Result: _TypeAlias = _models_3.RpcMethodOpenResult

        class pending:
            """Types for Mission.pending."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_3.RpcMethodPendingResult

        class stand_down:
            """Types for Mission.stand_down."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_3.RpcMethodStandDownResult

        class state:
            """Types for Mission.state."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_3.RpcMethodStateResult

from . import _outlet as _client_4
from . import _outlet_models as _models_4

class Outlet:
    """One per news outlet (actor id = domain): a durable credibility ledger built from physics checks."""
    Stub: _TypeAlias = _client_4.AsyncStub
    Metadata: _TypeAlias = _models_4.SocketMetadata
    Incoming: _TypeAlias = _models_4.SocketIncoming
    Outgoing: _TypeAlias = _models_4.SocketOutgoing
    State: _TypeAlias = _models_4.SocketState
    EmittedState: _TypeAlias = _models_4.SocketEmittedState
    StatePatch: _TypeAlias = _models_4.SocketStatePatch
    OutletLedger: _TypeAlias = _models_4.OutletLedger

    @_builtins.staticmethod
    def get(actor_id: _builtins.str, transport: _ActorTransport | None = None) -> _client_4.AsyncStub:
        """Return a async actor handle without sending a request.
        
        Args:
            actor_id: Identity of the actor to call.
            transport: Optional caller-owned transport. Uses the SDK-managed
                transport when omitted.
        
        The returned Stub provides the actor's typed RPC methods.
        """
        return _client_4.AsyncStub(actor_id, transport)

    Authorization: _TypeAlias = _sync_actors.Outlet.Authorization

    @_builtins.staticmethod
    async def prepare_websocket(authorization: Outlet.Authorization, transport: _ActorTransport | None = None) -> _SocketGrant:
        """Issue browser access after authenticating the user and authorizing this actor."""
        return await _prepare_authorization(_TypeAdapter(Outlet.Authorization).validate_python(authorization), transport)

    class Methods:
        """Argument tuples and return types for each actor RPC."""
        class ledger:
            """Types for Outlet.ledger."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_4.RpcMethodLedgerResult

        class record:
            """Count one checked claim once (idempotent on key). Returns True if it was new."""
            Args: _TypeAlias = _builtins.tuple[_models_4.RpcMethodRecordParameter0, _models_4.RpcMethodRecordParameter1]
            Result: _TypeAlias = _models_4.RpcMethodRecordResult

from . import _place as _client_5
from . import _place_models as _models_5

class Place:
    """One per watched place. Remembers active warnings so it only alerts on real changes."""
    Stub: _TypeAlias = _client_5.AsyncStub
    Metadata: _TypeAlias = _models_5.SocketMetadata
    Incoming: _TypeAlias = _models_5.SocketIncoming
    Outgoing: _TypeAlias = _models_5.SocketOutgoing
    State: _TypeAlias = _models_5.SocketState
    EmittedState: _TypeAlias = _models_5.SocketEmittedState
    StatePatch: _TypeAlias = _models_5.SocketStatePatch
    Change: _TypeAlias = _models_5.Change
    WarningItem: _TypeAlias = _models_5.WarningItem

    @_builtins.staticmethod
    def get(actor_id: _builtins.str, transport: _ActorTransport | None = None) -> _client_5.AsyncStub:
        """Return a async actor handle without sending a request.
        
        Args:
            actor_id: Identity of the actor to call.
            transport: Optional caller-owned transport. Uses the SDK-managed
                transport when omitted.
        
        The returned Stub provides the actor's typed RPC methods.
        """
        return _client_5.AsyncStub(actor_id, transport)

    Authorization: _TypeAlias = _sync_actors.Place.Authorization

    @_builtins.staticmethod
    async def prepare_websocket(authorization: Place.Authorization, transport: _ActorTransport | None = None) -> _SocketGrant:
        """Issue browser access after authenticating the user and authorizing this actor."""
        return await _prepare_authorization(_TypeAdapter(Place.Authorization).validate_python(authorization), transport)

    class Methods:
        """Argument tuples and return types for each actor RPC."""
        class history:
            """Types for Place.history."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_5.RpcMethodHistoryResult

        class update:
            """Reconcile freshly computed threats with active warnings. Returns only the changes."""
            Args: _TypeAlias = _builtins.tuple[_models_5.RpcMethodUpdateParameter0, _models_5.RpcMethodUpdateParameter1, _models_5.RpcMethodUpdateParameter2, _models_5.RpcMethodUpdateParameter3, _models_5.RpcMethodUpdateParameter4]
            Result: _TypeAlias = _models_5.RpcMethodUpdateResult

        class warnings:
            """Types for Place.warnings."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_5.RpcMethodWarningsResult

        class welcome:
            """True the first time we see this email for this place (send a welcome once)."""
            Args: _TypeAlias = _builtins.tuple[_models_5.RpcMethodWelcomeParameter0]
            Result: _TypeAlias = _models_5.RpcMethodWelcomeResult

__all__ = ['Crew', 'Globe', 'Haunt', 'Mission', 'Outlet', 'Place']
