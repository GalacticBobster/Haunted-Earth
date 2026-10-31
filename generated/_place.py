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
from . import _place_models as _models

class Stub:
    """One per watched place. Remembers active warnings so it only alerts on real changes."""
    def __init__(self, actor_id: str, transport: _ActorTransport | None = None) -> None:
        """Address an actor. An injected transport remains caller-owned."""
        self._actor_id = actor_id
        self._transport = transport if transport is not None else _default_client()

    def history(_self) -> _models.RpcMethodHistoryResult:
        """Invoke Place.history synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = _self._transport.invoke('Place', _self._actor_id, 'history', _args)
        _adapter: _TypeAdapter[_models.RpcMethodHistoryResult] = _TypeAdapter(_models.RpcMethodHistoryResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def update(_self, name: _models.RpcMethodUpdateParameter0, lat: _models.RpcMethodUpdateParameter1, lon: _models.RpcMethodUpdateParameter2, items_json: _models.RpcMethodUpdateParameter3, at: _models.RpcMethodUpdateParameter4) -> _models.RpcMethodUpdateResult:
        """Reconcile freshly computed threats with active warnings. Returns only the changes."""
        _args = _arguments([_argument(name, _TypeAdapter(_models.RpcMethodUpdateParameter0)), _argument(lat, _TypeAdapter(_models.RpcMethodUpdateParameter1)), _argument(lon, _TypeAdapter(_models.RpcMethodUpdateParameter2)), _argument(items_json, _TypeAdapter(_models.RpcMethodUpdateParameter3)), _argument(at, _TypeAdapter(_models.RpcMethodUpdateParameter4))], [_UNSET, _UNSET, _UNSET, _UNSET, _UNSET])
        _result = _self._transport.invoke('Place', _self._actor_id, 'update', _args)
        _adapter: _TypeAdapter[_models.RpcMethodUpdateResult] = _TypeAdapter(_models.RpcMethodUpdateResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def warnings(_self) -> _models.RpcMethodWarningsResult:
        """Invoke Place.warnings synchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = _self._transport.invoke('Place', _self._actor_id, 'warnings', _args)
        _adapter: _TypeAdapter[_models.RpcMethodWarningsResult] = _TypeAdapter(_models.RpcMethodWarningsResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def welcome(_self, email: _models.RpcMethodWelcomeParameter0) -> _models.RpcMethodWelcomeResult:
        """True the first time we see this email for this place (send a welcome once)."""
        _args = _arguments([_argument(email, _TypeAdapter(_models.RpcMethodWelcomeParameter0))], [_UNSET])
        _result = _self._transport.invoke('Place', _self._actor_id, 'welcome', _args)
        _adapter: _TypeAdapter[_models.RpcMethodWelcomeResult] = _TypeAdapter(_models.RpcMethodWelcomeResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    def broadcast(self, message: _models.SocketOutgoing) -> None:
        """Broadcast a typed application message to every connection without persisting it."""
        self._transport.broadcast('Place', self._actor_id, _argument(message, _TypeAdapter(_models.SocketOutgoing)))

    def prepare_websocket(self, metadata: _models.SocketMetadata) -> _SocketGrant:
        """Authorize a WebSocket connection without opening it.
        
        Args:
            metadata: Typed metadata passed to the actor's on_connect hook.
        
        Returns:
            A grant containing the connection URL and admission deadline.
            Accepted connections remain authorized until they close.
        """
        return self._transport.prepare_websocket('Place', self._actor_id, _argument(metadata, _TypeAdapter(_models.SocketMetadata)))

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
    """One per watched place. Remembers active warnings so it only alerts on real changes."""
    def __init__(self, actor_id: str, transport: _AsyncActorTransport | None = None) -> None:
        """Address an actor. An injected transport remains caller-owned."""
        self._actor_id = actor_id
        self._transport = transport if transport is not None else _default_async_client()

    async def history(_self) -> _models.RpcMethodHistoryResult:
        """Invoke Place.history asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = await _self._transport.invoke('Place', _self._actor_id, 'history', _args)
        _adapter: _TypeAdapter[_models.RpcMethodHistoryResult] = _TypeAdapter(_models.RpcMethodHistoryResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def update(_self, name: _models.RpcMethodUpdateParameter0, lat: _models.RpcMethodUpdateParameter1, lon: _models.RpcMethodUpdateParameter2, items_json: _models.RpcMethodUpdateParameter3, at: _models.RpcMethodUpdateParameter4) -> _models.RpcMethodUpdateResult:
        """Reconcile freshly computed threats with active warnings. Returns only the changes."""
        _args = _arguments([_argument(name, _TypeAdapter(_models.RpcMethodUpdateParameter0)), _argument(lat, _TypeAdapter(_models.RpcMethodUpdateParameter1)), _argument(lon, _TypeAdapter(_models.RpcMethodUpdateParameter2)), _argument(items_json, _TypeAdapter(_models.RpcMethodUpdateParameter3)), _argument(at, _TypeAdapter(_models.RpcMethodUpdateParameter4))], [_UNSET, _UNSET, _UNSET, _UNSET, _UNSET])
        _result = await _self._transport.invoke('Place', _self._actor_id, 'update', _args)
        _adapter: _TypeAdapter[_models.RpcMethodUpdateResult] = _TypeAdapter(_models.RpcMethodUpdateResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def warnings(_self) -> _models.RpcMethodWarningsResult:
        """Invoke Place.warnings asynchronously.
        
        Arguments and results are validated against the actor contract.
        Remote failures raise ActorInvocationError.
        """
        _args = _arguments([], [])
        _result = await _self._transport.invoke('Place', _self._actor_id, 'warnings', _args)
        _adapter: _TypeAdapter[_models.RpcMethodWarningsResult] = _TypeAdapter(_models.RpcMethodWarningsResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def welcome(_self, email: _models.RpcMethodWelcomeParameter0) -> _models.RpcMethodWelcomeResult:
        """True the first time we see this email for this place (send a welcome once)."""
        _args = _arguments([_argument(email, _TypeAdapter(_models.RpcMethodWelcomeParameter0))], [_UNSET])
        _result = await _self._transport.invoke('Place', _self._actor_id, 'welcome', _args)
        _adapter: _TypeAdapter[_models.RpcMethodWelcomeResult] = _TypeAdapter(_models.RpcMethodWelcomeResult)
        return _adapter.validate_json(_json.dumps(_result), strict=True)

    async def broadcast(self, message: _models.SocketOutgoing) -> None:
        """Broadcast a typed application message to every connection without persisting it."""
        await self._transport.broadcast('Place', self._actor_id, _argument(message, _TypeAdapter(_models.SocketOutgoing)))

    async def prepare_websocket(self, metadata: _models.SocketMetadata) -> _SocketGrant:
        """Authorize a WebSocket connection without opening it.
        
        Args:
            metadata: Typed metadata passed to the actor's on_connect hook.
        
        Returns:
            A grant containing the connection URL and admission deadline.
            Accepted connections remain authorized until they close.
        """
        return await self._transport.prepare_websocket('Place', self._actor_id, _argument(metadata, _TypeAdapter(_models.SocketMetadata)))

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
