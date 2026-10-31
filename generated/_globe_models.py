from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
from durable_actors.generated import ClientModel
from typing_extensions import TypeAliasType
from typing import Annotated, Optional, Union
from pydantic import Field
RpcMethodAllIdsResult: TypeAlias = list[str]
RpcMethodRegisterParameter0: TypeAlias = str
RpcMethodRegisterResult: TypeAlias = bool
RpcMethodScoutStartedResult: TypeAlias = int
FieldIds: TypeAlias = list[str]
FieldScoutRuns: TypeAlias = int
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
    ids: FieldIds
    scout_runs: FieldScoutRuns
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
    RpcMethod_all_ids_Result: RpcMethodAllIdsResult
    RpcMethod_register_Parameter_0: RpcMethodRegisterParameter0
    RpcMethod_register_Result: RpcMethodRegisterResult
    RpcMethod_scout_started_Result: RpcMethodScoutStartedResult
    SocketIncoming_1: Annotated[SocketIncoming, Field(alias='SocketIncoming')]
    SocketMetadata_1: Annotated[SocketMetadata, Field(alias='SocketMetadata')]
    SocketOutgoing_1: Annotated[SocketOutgoing, Field(alias='SocketOutgoing')]
    SocketState_1: Annotated[SocketState, Field(alias='SocketState')]
    SocketEmittedState_1: Annotated[SocketEmittedState, Field(alias='SocketEmittedState')]
    SocketStatePatch_1: Annotated[SocketStatePatch, Field(alias='SocketStatePatch')]
