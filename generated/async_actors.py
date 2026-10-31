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
from . import _globe as _client_0
from . import _globe_models as _models_0

class Globe:
    """Clients and types for Globe actors."""
    Stub: _TypeAlias = _client_0.AsyncStub
    Metadata: _TypeAlias = _models_0.SocketMetadata
    Incoming: _TypeAlias = _models_0.SocketIncoming
    Outgoing: _TypeAlias = _models_0.SocketOutgoing
    State: _TypeAlias = _models_0.SocketState
    EmittedState: _TypeAlias = _models_0.SocketEmittedState
    StatePatch: _TypeAlias = _models_0.SocketStatePatch

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
            Result: _TypeAlias = _models_0.RpcMethodAllIdsResult

        class register:
            """Types for Globe.register."""
            Args: _TypeAlias = _builtins.tuple[_models_0.RpcMethodRegisterParameter0]
            Result: _TypeAlias = _models_0.RpcMethodRegisterResult

        class scout_started:
            """Types for Globe.scout_started."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_0.RpcMethodScoutStartedResult

from . import _haunt as _client_1
from . import _haunt_models as _models_1

class Haunt:
    """Clients and types for Haunt actors."""
    Stub: _TypeAlias = _client_1.AsyncStub
    Metadata: _TypeAlias = _models_1.SocketMetadata
    Incoming: _TypeAlias = _models_1.SocketIncoming
    Outgoing: _TypeAlias = _models_1.SocketOutgoing
    State: _TypeAlias = _models_1.SocketState
    EmittedState: _TypeAlias = _models_1.SocketEmittedState
    StatePatch: _TypeAlias = _models_1.SocketStatePatch
    Reading: _TypeAlias = _models_1.Reading
    HauntState: _TypeAlias = _models_1.HauntState

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

    Authorization: _TypeAlias = _sync_actors.Haunt.Authorization

    @_builtins.staticmethod
    async def prepare_websocket(authorization: Haunt.Authorization, transport: _ActorTransport | None = None) -> _SocketGrant:
        """Issue browser access after authenticating the user and authorizing this actor."""
        return await _prepare_authorization(_TypeAdapter(Haunt.Authorization).validate_python(authorization), transport)

    class Methods:
        """Argument tuples and return types for each actor RPC."""
        class close:
            """Scouts call this when an event disappears from its feed."""
            Args: _TypeAlias = _builtins.tuple[_models_1.RpcMethodCloseParameter0]
            Result: _TypeAlias = _models_1.RpcMethodCloseResult

        class needs_analysis:
            """Types for Haunt.needs_analysis."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_1.RpcMethodNeedsAnalysisResult

        class needs_story:
            """Types for Haunt.needs_story."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_1.RpcMethodNeedsStoryResult

        class set_story:
            """Types for Haunt.set_story."""
            Args: _TypeAlias = _builtins.tuple[_models_1.RpcMethodSetStoryParameter0, _models_1.RpcMethodSetStoryParameter1]
            Result: _TypeAlias = None

        class set_verdict:
            """Types for Haunt.set_verdict."""
            Args: _TypeAlias = _builtins.tuple[_models_1.RpcMethodSetVerdictParameter0]
            Result: _TypeAlias = None

        class sight:
            """A scout reports this event. Returns 'new', 'changed' or 'same'."""
            Args: _TypeAlias = _builtins.tuple[_models_1.RpcMethodSightParameter0, _models_1.RpcMethodSightParameter1, _models_1.RpcMethodSightParameter2, _models_1.RpcMethodSightParameter3, _models_1.RpcMethodSightParameter4, _models_1.RpcMethodSightParameter5, _models_1.RpcMethodSightParameter6, _models_1.RpcMethodSightParameter7]
            Result: _TypeAlias = _models_1.RpcMethodSightResult

        class state:
            """Types for Haunt.state."""
            Args: _TypeAlias = _builtins.tuple[()]
            Result: _TypeAlias = _models_1.RpcMethodStateResult

__all__ = ['Globe', 'Haunt']
