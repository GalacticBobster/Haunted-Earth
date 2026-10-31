from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
from typing import Annotated, Optional, Union
from pydantic import Field
from durable_actors.generated import ClientModel
from typing_extensions import TypeAliasType

class Change(ClientModel):
    change: Annotated[str, Field(title='Change')]
    hazard: Annotated[str, Field(title='Hazard')]
    headline: Annotated[str, Field(title='Headline')]
    key: Annotated[str, Field(title='Key')]
    level: Annotated[int, Field(title='Level')]
RpcMethodHistoryResult: TypeAlias = list[Change]
RpcMethodUpdateParameter0: TypeAlias = str
RpcMethodUpdateParameter1: TypeAlias = float
RpcMethodUpdateParameter2: TypeAlias = float
RpcMethodUpdateParameter3: TypeAlias = str
RpcMethodUpdateParameter4: TypeAlias = str
RpcMethodUpdateResult: TypeAlias = list[Change]
RpcMethodWelcomeParameter0: TypeAlias = str
RpcMethodWelcomeResult: TypeAlias = bool

class WarningItem(ClientModel):
    detail: Annotated[str, Field(title='Detail')]
    hazard: Annotated[str, Field(title='Hazard')]
    headline: Annotated[str, Field(title='Headline')]
    issued: Annotated[str, Field(title='Issued')]
    key: Annotated[str, Field(title='Key')]
    level: Annotated[int, Field(title='Level')]
    updated: Annotated[str, Field(title='Updated')]
FieldActive: TypeAlias = list[WarningItem]
FieldLat: TypeAlias = float
FieldLog: TypeAlias = list[Change]
FieldLon: TypeAlias = float
FieldName: TypeAlias = str
FieldWelcomed: TypeAlias = str
if TYPE_CHECKING:
    JsonValueInput: TypeAlias = Optional[Union[str, int, float, bool, list['JsonValueInput'], dict[str, 'JsonValueInput']]]
else:
    JsonValueInput = TypeAliasType('JsonValueInput', Optional[Union[str, int, float, bool, list['JsonValueInput'], dict[str, 'JsonValueInput']]])
if TYPE_CHECKING:
    JsonValueOutput: TypeAlias = Optional[Union[str, int, float, bool, list['JsonValueOutput'], dict[str, 'JsonValueOutput']]]
else:
    JsonValueOutput = TypeAliasType('JsonValueOutput', Optional[Union[str, int, float, bool, list['JsonValueOutput'], dict[str, 'JsonValueOutput']]])
SocketMetadata: TypeAlias = JsonValueInput
SocketOutgoing: TypeAlias = JsonValueOutput

class SocketState(ClientModel):
    """
    Public persisted fields of the actor.
    """
    active: FieldActive
    lat: FieldLat
    log: FieldLog
    lon: FieldLon
    name: FieldName
    welcomed: FieldWelcomed
Tag: TypeAlias = str

class SocketEmittedState(ClientModel):
    """
    Complete current values of the actor's emitted fields.
    """

class SocketStatePatch(ClientModel):
    """
    Changed emitted fields; omitted fields are unchanged.
    """
RpcMethodWarningsResult: TypeAlias = list[WarningItem]
SocketIncoming: TypeAlias = JsonValueInput

class ContractTypes(ClientModel):
    """
    Named wire types used by this generated actor client.
    """
    RpcMethod_history_Result: RpcMethodHistoryResult
    RpcMethod_update_Parameter_0: RpcMethodUpdateParameter0
    RpcMethod_update_Parameter_1: RpcMethodUpdateParameter1
    RpcMethod_update_Parameter_2: RpcMethodUpdateParameter2
    RpcMethod_update_Parameter_3: RpcMethodUpdateParameter3
    RpcMethod_update_Parameter_4: RpcMethodUpdateParameter4
    RpcMethod_update_Result: RpcMethodUpdateResult
    RpcMethod_warnings_Result: RpcMethodWarningsResult
    RpcMethod_welcome_Parameter_0: RpcMethodWelcomeParameter0
    RpcMethod_welcome_Result: RpcMethodWelcomeResult
    SocketIncoming_1: Annotated[SocketIncoming, Field(alias='SocketIncoming')]
    SocketMetadata_1: Annotated[SocketMetadata, Field(alias='SocketMetadata')]
    SocketOutgoing_1: Annotated[SocketOutgoing, Field(alias='SocketOutgoing')]
    SocketState_1: Annotated[SocketState, Field(alias='SocketState')]
    SocketEmittedState_1: Annotated[SocketEmittedState, Field(alias='SocketEmittedState')]
    SocketStatePatch_1: Annotated[SocketStatePatch, Field(alias='SocketStatePatch')]
