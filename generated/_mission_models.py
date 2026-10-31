from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
from durable_actors.generated import ClientModel
from typing_extensions import TypeAliasType
from typing import Annotated, Optional, Union
from pydantic import Field
RpcMethodCompleteParameter0: TypeAlias = str
RpcMethodCompleteParameter1: TypeAlias = str
RpcMethodCompleteParameter2: TypeAlias = str
RpcMethodCompleteResult: TypeAlias = list[str]
RpcMethodOpenParameter0: TypeAlias = str
RpcMethodOpenParameter1: TypeAlias = str
RpcMethodOpenParameter2: TypeAlias = str
RpcMethodOpenParameter3: TypeAlias = int
RpcMethodOpenParameter4: TypeAlias = str
RpcMethodOpenParameter5: TypeAlias = str
RpcMethodOpenResult: TypeAlias = bool
RpcMethodStandDownResult: TypeAlias = bool

class Task(ClientModel):
    depth: Annotated[int, Field(title='Depth')]
    id: Annotated[str, Field(title='Id')]
    parent: Annotated[str, Field(title='Parent')]
    result: Annotated[str, Field(title='Result')]
    role: Annotated[str, Field(title='Role')]
    status: Annotated[str, Field(title='Status')]
    title: Annotated[str, Field(title='Title')]
FieldHazard: TypeAlias = str
FieldLevel: TypeAlias = int
FieldOpened: TypeAlias = str
FieldPlaceId: TypeAlias = str
FieldPlaceName: TypeAlias = str
FieldStatus: TypeAlias = str
FieldTasks: TypeAlias = list[Task]
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
    hazard: FieldHazard
    level: FieldLevel
    opened: FieldOpened
    place_id: FieldPlaceId
    place_name: FieldPlaceName
    status: FieldStatus
    tasks: FieldTasks
Tag: TypeAlias = str

class SocketEmittedState(ClientModel):
    """
    Complete current values of the actor's emitted fields.
    """

class SocketStatePatch(ClientModel):
    """
    Changed emitted fields; omitted fields are unchanged.
    """
RpcMethodPendingResult: TypeAlias = list[Task]

class MissionState(ClientModel):
    hazard: Annotated[str, Field(title='Hazard')]
    id: Annotated[str, Field(title='Id')]
    level: Annotated[int, Field(title='Level')]
    opened: Annotated[str, Field(title='Opened')]
    place_id: Annotated[str, Field(title='Place Id')]
    place_name: Annotated[str, Field(title='Place Name')]
    status: Annotated[str, Field(title='Status')]
    tasks: Annotated[list[Task], Field(title='Tasks')]
SocketIncoming: TypeAlias = JsonValueInput
RpcMethodStateResult: TypeAlias = MissionState

class ContractTypes(ClientModel):
    """
    Named wire types used by this generated actor client.
    """
    RpcMethod_complete_Parameter_0: RpcMethodCompleteParameter0
    RpcMethod_complete_Parameter_1: RpcMethodCompleteParameter1
    RpcMethod_complete_Parameter_2: RpcMethodCompleteParameter2
    RpcMethod_complete_Result: RpcMethodCompleteResult
    RpcMethod_open_Parameter_0: RpcMethodOpenParameter0
    RpcMethod_open_Parameter_1: RpcMethodOpenParameter1
    RpcMethod_open_Parameter_2: RpcMethodOpenParameter2
    RpcMethod_open_Parameter_3: RpcMethodOpenParameter3
    RpcMethod_open_Parameter_4: RpcMethodOpenParameter4
    RpcMethod_open_Parameter_5: RpcMethodOpenParameter5
    RpcMethod_open_Result: RpcMethodOpenResult
    RpcMethod_pending_Result: RpcMethodPendingResult
    RpcMethod_stand_down_Result: RpcMethodStandDownResult
    RpcMethod_state_Result: RpcMethodStateResult
    SocketIncoming_1: Annotated[SocketIncoming, Field(alias='SocketIncoming')]
    SocketMetadata_1: Annotated[SocketMetadata, Field(alias='SocketMetadata')]
    SocketOutgoing_1: Annotated[SocketOutgoing, Field(alias='SocketOutgoing')]
    SocketState_1: Annotated[SocketState, Field(alias='SocketState')]
    SocketEmittedState_1: Annotated[SocketEmittedState, Field(alias='SocketEmittedState')]
    SocketStatePatch_1: Annotated[SocketStatePatch, Field(alias='SocketStatePatch')]
