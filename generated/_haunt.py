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
from . import _haunt_models as _models

class Stub:
    """Synchronous client for Haunt actors."""
    def __init__(self, actor_id: str, transport: _ActorTransport | None = None) -> None:
        """Address an actor. An injected transport remains caller-owned."""
        self._actor_id = actor_id
        self._transport = transport if transport is not None else _default_client()

    def close(_self, at: _models.RpcMethodCloseParameter0) -> _models.RpcMethodCloseResult:
        """Scouts call this when an event disappears from its feed."""
        _args = _arguments([_argument(at, _TypeAdapter(_models.RpcMethodCloseParameter0))], [_UNSET])
        _result = _self._transport.invoke('Haunt', _self._actor_id, 'close', _args)
        _adapter: _TypeAdapter[_models.RpcMethodCloseResult] = _TypeAdapter(_models.RpcMethodCloseResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def needs_analysis(_self) -> _models.RpcMethodNeedsAnalysisResult:
        """Invoke Haunt.needs_analysis synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = _self._transport.invoke('Haunt', _self._actor_id, 'needs_analysis', _args)
        _adapter: _TypeAdapter[_models.RpcMethodNeedsAnalysisResult] = _TypeAdapter(_models.RpcMethodNeedsAnalysisResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def needs_story(_self) -> _models.RpcMethodNeedsStoryResult:
        """Invoke Haunt.needs_story synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = _self._transport.invoke('Haunt', _self._actor_id, 'needs_story', _args)
        _adapter: _TypeAdapter[_models.RpcMethodNeedsStoryResult] = _TypeAdapter(_models.RpcMethodNeedsStoryResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def set_story(_self, story: _models.RpcMethodSetStoryParameter0, for_verdict: _models.RpcMethodSetStoryParameter1) -> None:
        """Invoke Haunt.set_story synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([_argument(story, _TypeAdapter(_models.RpcMethodSetStoryParameter0)), _argument(for_verdict, _TypeAdapter(_models.RpcMethodSetStoryParameter1))], [_UNSET, _UNSET])
        _result = _self._transport.invoke('Haunt', _self._actor_id, 'set_story', _args)

    def set_verdict(_self, verdict: _models.RpcMethodSetVerdictParameter0) -> None:
        """Invoke Haunt.set_verdict synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([_argument(verdict, _TypeAdapter(_models.RpcMethodSetVerdictParameter0))], [_UNSET])
        _result = _self._transport.invoke('Haunt', _self._actor_id, 'set_verdict', _args)

    def sight(_self, kind: _models.RpcMethodSightParameter0, title: _models.RpcMethodSightParameter1, lat: _models.RpcMethodSightParameter2, lon: _models.RpcMethodSightParameter3, severity: _models.RpcMethodSightParameter4, status: _models.RpcMethodSightParameter5, seen_at: _models.RpcMethodSightParameter6, extra_json: _models.RpcMethodSightParameter7) -> _models.RpcMethodSightResult:
        """A scout reports this event. Returns 'new', 'changed' or 'same'."""
        _args = _arguments([_argument(kind, _TypeAdapter(_models.RpcMethodSightParameter0)), _argument(title, _TypeAdapter(_models.RpcMethodSightParameter1)), _argument(lat, _TypeAdapter(_models.RpcMethodSightParameter2)), _argument(lon, _TypeAdapter(_models.RpcMethodSightParameter3)), _argument(severity, _TypeAdapter(_models.RpcMethodSightParameter4)), _argument(status, _TypeAdapter(_models.RpcMethodSightParameter5)), _argument(seen_at, _TypeAdapter(_models.RpcMethodSightParameter6)), _argument(extra_json, _TypeAdapter(_models.RpcMethodSightParameter7))], [_UNSET, _UNSET, _UNSET, _UNSET, _UNSET, _UNSET, _UNSET, _UNSET])
        _result = _self._transport.invoke('Haunt', _self._actor_id, 'sight', _args)
        _adapter: _TypeAdapter[_models.RpcMethodSightResult] = _TypeAdapter(_models.RpcMethodSightResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def state(_self) -> _models.RpcMethodStateResult:
        """Invoke Haunt.state synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = _self._transport.invoke('Haunt', _self._actor_id, 'state', _args)
        _adapter: _TypeAdapter[_models.RpcMethodStateResult] = _TypeAdapter(_models.RpcMethodStateResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def broadcast(self, message: _models.SocketOutgoing) -> None:
        """Broadcast a typed application message to every connection without persisting it."""
        self._transport.broadcast('Haunt', self._actor_id, _argument(message, _TypeAdapter(_models.SocketOutgoing)))

    def prepare_websocket(self, metadata: _models.SocketMetadata) -> _SocketGrant:
        """Authorize a WebSocket connection without opening it.
        
        Args:
            metadata: Typed metadata passed to the actor's on_connect hook.
        
        Returns:
            A grant containing the connection URL and admission deadline.
            Accepted connections remain authorized until they close.
        """
        return self._transport.prepare_websocket('Haunt', self._actor_id, _argument(metadata, _TypeAdapter(_models.SocketMetadata)))

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
    """Async client for Haunt actors."""
    def __init__(self, actor_id: str, transport: _AsyncActorTransport | None = None) -> None:
        """Address an actor. An injected transport remains caller-owned."""
        self._actor_id = actor_id
        self._transport = transport if transport is not None else _default_async_client()

    async def close(_self, at: _models.RpcMethodCloseParameter0) -> _models.RpcMethodCloseResult:
        """Scouts call this when an event disappears from its feed."""
        _args = _arguments([_argument(at, _TypeAdapter(_models.RpcMethodCloseParameter0))], [_UNSET])
        _result = await _self._transport.invoke('Haunt', _self._actor_id, 'close', _args)
        _adapter: _TypeAdapter[_models.RpcMethodCloseResult] = _TypeAdapter(_models.RpcMethodCloseResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def needs_analysis(_self) -> _models.RpcMethodNeedsAnalysisResult:
        """Invoke Haunt.needs_analysis asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = await _self._transport.invoke('Haunt', _self._actor_id, 'needs_analysis', _args)
        _adapter: _TypeAdapter[_models.RpcMethodNeedsAnalysisResult] = _TypeAdapter(_models.RpcMethodNeedsAnalysisResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def needs_story(_self) -> _models.RpcMethodNeedsStoryResult:
        """Invoke Haunt.needs_story asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = await _self._transport.invoke('Haunt', _self._actor_id, 'needs_story', _args)
        _adapter: _TypeAdapter[_models.RpcMethodNeedsStoryResult] = _TypeAdapter(_models.RpcMethodNeedsStoryResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def set_story(_self, story: _models.RpcMethodSetStoryParameter0, for_verdict: _models.RpcMethodSetStoryParameter1) -> None:
        """Invoke Haunt.set_story asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([_argument(story, _TypeAdapter(_models.RpcMethodSetStoryParameter0)), _argument(for_verdict, _TypeAdapter(_models.RpcMethodSetStoryParameter1))], [_UNSET, _UNSET])
        _result = await _self._transport.invoke('Haunt', _self._actor_id, 'set_story', _args)

    async def set_verdict(_self, verdict: _models.RpcMethodSetVerdictParameter0) -> None:
        """Invoke Haunt.set_verdict asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([_argument(verdict, _TypeAdapter(_models.RpcMethodSetVerdictParameter0))], [_UNSET])
        _result = await _self._transport.invoke('Haunt', _self._actor_id, 'set_verdict', _args)

    async def sight(_self, kind: _models.RpcMethodSightParameter0, title: _models.RpcMethodSightParameter1, lat: _models.RpcMethodSightParameter2, lon: _models.RpcMethodSightParameter3, severity: _models.RpcMethodSightParameter4, status: _models.RpcMethodSightParameter5, seen_at: _models.RpcMethodSightParameter6, extra_json: _models.RpcMethodSightParameter7) -> _models.RpcMethodSightResult:
        """A scout reports this event. Returns 'new', 'changed' or 'same'."""
        _args = _arguments([_argument(kind, _TypeAdapter(_models.RpcMethodSightParameter0)), _argument(title, _TypeAdapter(_models.RpcMethodSightParameter1)), _argument(lat, _TypeAdapter(_models.RpcMethodSightParameter2)), _argument(lon, _TypeAdapter(_models.RpcMethodSightParameter3)), _argument(severity, _TypeAdapter(_models.RpcMethodSightParameter4)), _argument(status, _TypeAdapter(_models.RpcMethodSightParameter5)), _argument(seen_at, _TypeAdapter(_models.RpcMethodSightParameter6)), _argument(extra_json, _TypeAdapter(_models.RpcMethodSightParameter7))], [_UNSET, _UNSET, _UNSET, _UNSET, _UNSET, _UNSET, _UNSET, _UNSET])
        _result = await _self._transport.invoke('Haunt', _self._actor_id, 'sight', _args)
        _adapter: _TypeAdapter[_models.RpcMethodSightResult] = _TypeAdapter(_models.RpcMethodSightResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def state(_self) -> _models.RpcMethodStateResult:
        """Invoke Haunt.state asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = await _self._transport.invoke('Haunt', _self._actor_id, 'state', _args)
        _adapter: _TypeAdapter[_models.RpcMethodStateResult] = _TypeAdapter(_models.RpcMethodStateResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def broadcast(self, message: _models.SocketOutgoing) -> None:
        """Broadcast a typed application message to every connection without persisting it."""
        await self._transport.broadcast('Haunt', self._actor_id, _argument(message, _TypeAdapter(_models.SocketOutgoing)))

    async def prepare_websocket(self, metadata: _models.SocketMetadata) -> _SocketGrant:
        """Authorize a WebSocket connection without opening it.
        
        Args:
            metadata: Typed metadata passed to the actor's on_connect hook.
        
        Returns:
            A grant containing the connection URL and admission deadline.
            Accepted connections remain authorized until they close.
        """
        return await self._transport.prepare_websocket('Haunt', self._actor_id, _argument(metadata, _TypeAdapter(_models.SocketMetadata)))

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
