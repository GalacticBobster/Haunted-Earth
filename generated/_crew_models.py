from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
from typing import Annotated, Optional, Union
from pydantic import Field
from durable_actors.generated import ClientModel
from typing_extensions import TypeAliasType

class CrewState(ClientModel):
    cycles: Annotated[int, Field(title='Cycles')]
    last_action: Annotated[str, Field(title='Last Action')]
    last_seen: Annotated[str, Field(title='Last Seen')]
    name: Annotated[str, Field(title='Name')]
    runs: Annotated[int, Field(title='Runs')]
    started: Annotated[str, Field(title='Started')]
RpcMethodBeatParameter0: TypeAlias = str
RpcMethodBeatParameter1: TypeAlias = str
RpcMethodBeatResult: TypeAlias = int
RpcMethodStartParameter0: TypeAlias = str
RpcMethodStartResult: TypeAlias = int
RpcMethodStateResult: TypeAlias = CrewState
FieldCycles: TypeAlias = int
FieldLastAction: TypeAlias = str
FieldLastSeen: TypeAlias = str
FieldRuns: TypeAlias = int
FieldStarted: TypeAlias = str
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
    cycles: FieldCycles
    last_action: FieldLastAction
    last_seen: FieldLastSeen
    runs: FieldRuns
    started: FieldStarted
Tag: TypeAlias = str

class SocketEmittedState(ClientModel):
    """
    Complete current values of the actor's emitted fields.
    """

class SocketStatePatch(ClientModel):
    """
    Changed emitted fields; omitted fields are unchanged.
    """
SocketIncoming: TypeAlias = JsonValueInput

class ContractTypes(ClientModel):
    """
    Named wire types used by this generated actor client.
    """
    RpcMethod_beat_Parameter_0: RpcMethodBeatParameter0
    RpcMethod_beat_Parameter_1: RpcMethodBeatParameter1
    RpcMethod_beat_Result: RpcMethodBeatResult
    RpcMethod_start_Parameter_0: RpcMethodStartParameter0
    RpcMethod_start_Result: RpcMethodStartResult
    RpcMethod_state_Result: RpcMethodStateResult
    SocketIncoming_1: Annotated[SocketIncoming, Field(alias='SocketIncoming')]
    SocketMetadata_1: Annotated[SocketMetadata, Field(alias='SocketMetadata')]
    SocketOutgoing_1: Annotated[SocketOutgoing, Field(alias='SocketOutgoing')]
    SocketState_1: Annotated[SocketState, Field(alias='SocketState')]
    SocketEmittedState_1: Annotated[SocketEmittedState, Field(alias='SocketEmittedState')]
    SocketStatePatch_1: Annotated[SocketStatePatch, Field(alias='SocketStatePatch')]
