from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
from durable_actors.generated import ClientModel
from typing_extensions import TypeAliasType
from typing import Annotated, Optional, Union
from pydantic import Field
RpcMethodCloseParameter0: TypeAlias = str
RpcMethodCloseResult: TypeAlias = bool
RpcMethodNeedsAnalysisResult: TypeAlias = bool
RpcMethodNeedsStoryResult: TypeAlias = bool
RpcMethodSetStoryParameter0: TypeAlias = str
RpcMethodSetStoryParameter1: TypeAlias = str
RpcMethodSetVerdictParameter0: TypeAlias = str
RpcMethodSightParameter0: TypeAlias = str
RpcMethodSightParameter1: TypeAlias = str
RpcMethodSightParameter2: TypeAlias = float
RpcMethodSightParameter3: TypeAlias = float
RpcMethodSightParameter4: TypeAlias = float
RpcMethodSightParameter5: TypeAlias = str
RpcMethodSightParameter6: TypeAlias = str
RpcMethodSightParameter7: TypeAlias = str
RpcMethodSightResult: TypeAlias = str

class Reading(ClientModel):
    severity: Annotated[float, Field(title='Severity')]
    status: Annotated[str, Field(title='Status')]
    t: Annotated[str, Field(title='T')]
FieldAnalyzedSeverity: TypeAlias = float
FieldExtraJson: TypeAlias = str
FieldFirstSeen: TypeAlias = str
FieldHistory: TypeAlias = list[Reading]
FieldKind: TypeAlias = str
FieldLastSeen: TypeAlias = str
FieldLat: TypeAlias = float
FieldLon: TypeAlias = float
FieldSeverity: TypeAlias = float
FieldSightings: TypeAlias = int
FieldStatus: TypeAlias = str
FieldStory: TypeAlias = str
FieldStoryVerdict: TypeAlias = str
FieldTitle: TypeAlias = str
FieldVerdict: TypeAlias = str
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
    analyzed_severity: FieldAnalyzedSeverity
    extra_json: FieldExtraJson
    first_seen: FieldFirstSeen
    history: FieldHistory
    kind: FieldKind
    last_seen: FieldLastSeen
    lat: FieldLat
    lon: FieldLon
    severity: FieldSeverity
    sightings: FieldSightings
    status: FieldStatus
    story: FieldStory
    story_verdict: FieldStoryVerdict
    title: FieldTitle
    verdict: FieldVerdict
Tag: TypeAlias = str

class SocketEmittedState(ClientModel):
    """
    Complete current values of the actor's emitted fields.
    """

class SocketStatePatch(ClientModel):
    """
    Changed emitted fields; omitted fields are unchanged.
    """

class HauntState(ClientModel):
    analyzed_severity: Annotated[float, Field(title='Analyzed Severity')]
    extra_json: Annotated[str, Field(title='Extra Json')]
    first_seen: Annotated[str, Field(title='First Seen')]
    history: Annotated[list[Reading], Field(title='History')]
    id: Annotated[str, Field(title='Id')]
    kind: Annotated[str, Field(title='Kind')]
    last_seen: Annotated[str, Field(title='Last Seen')]
    lat: Annotated[float, Field(title='Lat')]
    lon: Annotated[float, Field(title='Lon')]
    severity: Annotated[float, Field(title='Severity')]
    sightings: Annotated[int, Field(title='Sightings')]
    status: Annotated[str, Field(title='Status')]
    story: Annotated[str, Field(title='Story')]
    title: Annotated[str, Field(title='Title')]
    verdict: Annotated[str, Field(title='Verdict')]
RpcMethodStateResult: TypeAlias = HauntState
SocketIncoming: TypeAlias = JsonValueInput

class ContractTypes(ClientModel):
    """
    Named wire types used by this generated actor client.
    """
    RpcMethod_close_Parameter_0: RpcMethodCloseParameter0
    RpcMethod_close_Result: RpcMethodCloseResult
    RpcMethod_needs_analysis_Result: RpcMethodNeedsAnalysisResult
    RpcMethod_needs_story_Result: RpcMethodNeedsStoryResult
    RpcMethod_set_story_Parameter_0: RpcMethodSetStoryParameter0
    RpcMethod_set_story_Parameter_1: RpcMethodSetStoryParameter1
    RpcMethod_set_verdict_Parameter_0: RpcMethodSetVerdictParameter0
    RpcMethod_sight_Parameter_0: RpcMethodSightParameter0
    RpcMethod_sight_Parameter_1: RpcMethodSightParameter1
    RpcMethod_sight_Parameter_2: RpcMethodSightParameter2
    RpcMethod_sight_Parameter_3: RpcMethodSightParameter3
    RpcMethod_sight_Parameter_4: RpcMethodSightParameter4
    RpcMethod_sight_Parameter_5: RpcMethodSightParameter5
    RpcMethod_sight_Parameter_6: RpcMethodSightParameter6
    RpcMethod_sight_Parameter_7: RpcMethodSightParameter7
    RpcMethod_sight_Result: RpcMethodSightResult
    RpcMethod_state_Result: RpcMethodStateResult
    SocketIncoming_1: Annotated[SocketIncoming, Field(alias='SocketIncoming')]
    SocketMetadata_1: Annotated[SocketMetadata, Field(alias='SocketMetadata')]
    SocketOutgoing_1: Annotated[SocketOutgoing, Field(alias='SocketOutgoing')]
    SocketState_1: Annotated[SocketState, Field(alias='SocketState')]
    SocketEmittedState_1: Annotated[SocketEmittedState, Field(alias='SocketEmittedState')]
    SocketStatePatch_1: Annotated[SocketStatePatch, Field(alias='SocketStatePatch')]
