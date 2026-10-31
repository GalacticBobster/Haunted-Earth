from __future__ import annotations
import json as _json
from collections.abc import Callable as _Callable, Awaitable as _Awaitable
from pydantic import TypeAdapter as _TypeAdapter
from durable_actors.client import ActorTransport as _ActorTransport, SocketGrant as _SocketGrant, default_client as _default_client
from durable_actors.async_client import AsyncActorTransport as _AsyncActorTransport, default_async_client as _default_async_client
from durable_actors.async_connection import AsyncConnection as _AsyncConnection
from durable_actors.connection import Connection as _Connection
from durable_actors.subscription import Subscription as _Subscription, AsyncSubscription as _AsyncSubscription
from durable_actors.generated import UNSET as _UNSET, Unset as _Unset, arguments as _arguments, argument as _argument
from . import _mission_models as _models

class Stub:
    """One relief mission per (place, hazard). Tasks can spawn follow-up tasks (bounded depth),
    so a warning grows its own plan; one call at a time keeps two workers off the same task.
    """
    def __init__(self, actor_id: str, transport: _ActorTransport | None = None) -> None:
        """Address an actor. An injected transport remains caller-owned."""
        self._actor_id = actor_id
        self._transport = transport if transport is not None else _default_client()

    def complete(_self, task_id: _models.RpcMethodCompleteParameter0, result: _models.RpcMethodCompleteParameter1, spawn_json: _models.RpcMethodCompleteParameter2) -> _models.RpcMethodCompleteResult:
        """Finish a task and add its follow-ups (deduplicated, depth-limited). Returns new task ids."""
        _args = _arguments([_argument(task_id, _TypeAdapter(_models.RpcMethodCompleteParameter0)), _argument(result, _TypeAdapter(_models.RpcMethodCompleteParameter1)), _argument(spawn_json, _TypeAdapter(_models.RpcMethodCompleteParameter2))], [_UNSET, _UNSET, _UNSET])
        _result = _self._transport.invoke('Mission', _self._actor_id, 'complete', _args)
        _adapter: _TypeAdapter[_models.RpcMethodCompleteResult] = _TypeAdapter(_models.RpcMethodCompleteResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def open(_self, place_id: _models.RpcMethodOpenParameter0, place_name: _models.RpcMethodOpenParameter1, hazard: _models.RpcMethodOpenParameter2, level: _models.RpcMethodOpenParameter3, at: _models.RpcMethodOpenParameter4, seeds_json: _models.RpcMethodOpenParameter5) -> _models.RpcMethodOpenResult:
        """Open (or re-open / escalate) the mission. Returns True if it was newly opened."""
        _args = _arguments([_argument(place_id, _TypeAdapter(_models.RpcMethodOpenParameter0)), _argument(place_name, _TypeAdapter(_models.RpcMethodOpenParameter1)), _argument(hazard, _TypeAdapter(_models.RpcMethodOpenParameter2)), _argument(level, _TypeAdapter(_models.RpcMethodOpenParameter3)), _argument(at, _TypeAdapter(_models.RpcMethodOpenParameter4)), _argument(seeds_json, _TypeAdapter(_models.RpcMethodOpenParameter5))], [_UNSET, _UNSET, _UNSET, _UNSET, _UNSET, _UNSET])
        _result = _self._transport.invoke('Mission', _self._actor_id, 'open', _args)
        _adapter: _TypeAdapter[_models.RpcMethodOpenResult] = _TypeAdapter(_models.RpcMethodOpenResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def pending(_self) -> _models.RpcMethodPendingResult:
        """Invoke Mission.pending synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = _self._transport.invoke('Mission', _self._actor_id, 'pending', _args)
        _adapter: _TypeAdapter[_models.RpcMethodPendingResult] = _TypeAdapter(_models.RpcMethodPendingResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def stand_down(_self) -> _models.RpcMethodStandDownResult:
        """Invoke Mission.stand_down synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = _self._transport.invoke('Mission', _self._actor_id, 'stand_down', _args)
        _adapter: _TypeAdapter[_models.RpcMethodStandDownResult] = _TypeAdapter(_models.RpcMethodStandDownResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def state(_self) -> _models.RpcMethodStateResult:
        """Invoke Mission.state synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = _self._transport.invoke('Mission', _self._actor_id, 'state', _args)
        _adapter: _TypeAdapter[_models.RpcMethodStateResult] = _TypeAdapter(_models.RpcMethodStateResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def broadcast(self, message: _models.SocketOutgoing) -> None:
        """Broadcast a typed application message to every connection without persisting it."""
        self._transport.broadcast('Mission', self._actor_id, _argument(message, _TypeAdapter(_models.SocketOutgoing)))

    def prepare_websocket(self, metadata: _models.SocketMetadata) -> _SocketGrant:
        """Authorize a WebSocket connection without opening it.
        
        Args:
            metadata: Typed metadata passed to the actor's on_connect hook.
        
        Returns:
            A grant containing the connection URL and admission deadline.
            Accepted connections remain authorized until they close.
        """
        return self._transport.prepare_websocket('Mission', self._actor_id, _argument(metadata, _TypeAdapter(_models.SocketMetadata)))

    def connect(self, metadata: _models.SocketMetadata) -> _Connection[_models.SocketIncoming, _models.SocketOutgoing, _models.SocketEmittedState, _models.SocketStatePatch]:
        """Open a typed, synchronous WebSocket connection.
        
        Args:
            metadata: Typed metadata passed to the actor's on_connect hook.
        
        Use send() for application messages and receive() or iteration for
        messages and state events. Use close() or with for cleanup.
        For complete emitted-state callbacks, use subscribe() when available.
        """
        grant = self.prepare_websocket(metadata)
        return _Connection[_models.SocketIncoming, _models.SocketOutgoing, _models.SocketEmittedState, _models.SocketStatePatch].open(grant, _TypeAdapter(_models.SocketIncoming), _TypeAdapter(_models.SocketOutgoing), _TypeAdapter(_models.SocketEmittedState), _TypeAdapter(_models.SocketStatePatch))

class AsyncStub:
    """One relief mission per (place, hazard). Tasks can spawn follow-up tasks (bounded depth),
    so a warning grows its own plan; one call at a time keeps two workers off the same task.
    """
    def __init__(self, actor_id: str, transport: _AsyncActorTransport | None = None) -> None:
        """Address an actor. An injected transport remains caller-owned."""
        self._actor_id = actor_id
        self._transport = transport if transport is not None else _default_async_client()

    async def complete(_self, task_id: _models.RpcMethodCompleteParameter0, result: _models.RpcMethodCompleteParameter1, spawn_json: _models.RpcMethodCompleteParameter2) -> _models.RpcMethodCompleteResult:
        """Finish a task and add its follow-ups (deduplicated, depth-limited). Returns new task ids."""
        _args = _arguments([_argument(task_id, _TypeAdapter(_models.RpcMethodCompleteParameter0)), _argument(result, _TypeAdapter(_models.RpcMethodCompleteParameter1)), _argument(spawn_json, _TypeAdapter(_models.RpcMethodCompleteParameter2))], [_UNSET, _UNSET, _UNSET])
        _result = await _self._transport.invoke('Mission', _self._actor_id, 'complete', _args)
        _adapter: _TypeAdapter[_models.RpcMethodCompleteResult] = _TypeAdapter(_models.RpcMethodCompleteResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def open(_self, place_id: _models.RpcMethodOpenParameter0, place_name: _models.RpcMethodOpenParameter1, hazard: _models.RpcMethodOpenParameter2, level: _models.RpcMethodOpenParameter3, at: _models.RpcMethodOpenParameter4, seeds_json: _models.RpcMethodOpenParameter5) -> _models.RpcMethodOpenResult:
        """Open (or re-open / escalate) the mission. Returns True if it was newly opened."""
        _args = _arguments([_argument(place_id, _TypeAdapter(_models.RpcMethodOpenParameter0)), _argument(place_name, _TypeAdapter(_models.RpcMethodOpenParameter1)), _argument(hazard, _TypeAdapter(_models.RpcMethodOpenParameter2)), _argument(level, _TypeAdapter(_models.RpcMethodOpenParameter3)), _argument(at, _TypeAdapter(_models.RpcMethodOpenParameter4)), _argument(seeds_json, _TypeAdapter(_models.RpcMethodOpenParameter5))], [_UNSET, _UNSET, _UNSET, _UNSET, _UNSET, _UNSET])
        _result = await _self._transport.invoke('Mission', _self._actor_id, 'open', _args)
        _adapter: _TypeAdapter[_models.RpcMethodOpenResult] = _TypeAdapter(_models.RpcMethodOpenResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def pending(_self) -> _models.RpcMethodPendingResult:
        """Invoke Mission.pending asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = await _self._transport.invoke('Mission', _self._actor_id, 'pending', _args)
        _adapter: _TypeAdapter[_models.RpcMethodPendingResult] = _TypeAdapter(_models.RpcMethodPendingResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def stand_down(_self) -> _models.RpcMethodStandDownResult:
        """Invoke Mission.stand_down asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = await _self._transport.invoke('Mission', _self._actor_id, 'stand_down', _args)
        _adapter: _TypeAdapter[_models.RpcMethodStandDownResult] = _TypeAdapter(_models.RpcMethodStandDownResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def state(_self) -> _models.RpcMethodStateResult:
        """Invoke Mission.state asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = await _self._transport.invoke('Mission', _self._actor_id, 'state', _args)
        _adapter: _TypeAdapter[_models.RpcMethodStateResult] = _TypeAdapter(_models.RpcMethodStateResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def broadcast(self, message: _models.SocketOutgoing) -> None:
        """Broadcast a typed application message to every connection without persisting it."""
        await self._transport.broadcast('Mission', self._actor_id, _argument(message, _TypeAdapter(_models.SocketOutgoing)))

    async def prepare_websocket(self, metadata: _models.SocketMetadata) -> _SocketGrant:
        """Authorize a WebSocket connection without opening it.
        
        Args:
            metadata: Typed metadata passed to the actor's on_connect hook.
        
        Returns:
            A grant containing the connection URL and admission deadline.
            Accepted connections remain authorized until they close.
        """
        return await self._transport.prepare_websocket('Mission', self._actor_id, _argument(metadata, _TypeAdapter(_models.SocketMetadata)))

    async def connect(self, metadata: _models.SocketMetadata) -> _AsyncConnection[_models.SocketIncoming, _models.SocketOutgoing, _models.SocketEmittedState, _models.SocketStatePatch]:
        """Open a typed, async WebSocket connection.
        
        Args:
            metadata: Typed metadata passed to the actor's on_connect hook.
        
        Use send() for application messages and receive() or iteration for
        messages and state events. Use aclose() or async with for cleanup.
        For complete emitted-state callbacks, use subscribe() when available.
        """
        grant = await self.prepare_websocket(metadata)
        return await _AsyncConnection[_models.SocketIncoming, _models.SocketOutgoing, _models.SocketEmittedState, _models.SocketStatePatch].open(grant, _TypeAdapter(_models.SocketIncoming), _TypeAdapter(_models.SocketOutgoing), _TypeAdapter(_models.SocketEmittedState), _TypeAdapter(_models.SocketStatePatch))
