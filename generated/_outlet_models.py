from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
from durable_actors.generated import ClientModel
from typing_extensions import TypeAliasType
from typing import Annotated, Optional, Union
from pydantic import Field
RpcMethodRecordParameter0: TypeAlias = str
RpcMethodRecordParameter1: TypeAlias = str
RpcMethodRecordResult: TypeAlias = bool

class OutletLedger(ClientModel):
    confirmed: Annotated[int, Field(title='Confirmed')]
    implausible: Annotated[int, Field(title='Implausible')]
    mismatched: Annotated[int, Field(title='Mismatched')]
    outlet: Annotated[str, Field(title='Outlet')]
    plausible: Annotated[int, Field(title='Plausible')]
    unverifiable: Annotated[int, Field(title='Unverifiable')]
FieldConfirmed: TypeAlias = int
FieldImplausible: TypeAlias = int
FieldKeys: TypeAlias = list[str]
FieldMismatched: TypeAlias = int
FieldPlausible: TypeAlias = int
FieldUnverifiable: TypeAlias = int
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
    confirmed: FieldConfirmed
    implausible: FieldImplausible
    keys: FieldKeys
    mismatched: FieldMismatched
    plausible: FieldPlausible
    unverifiable: FieldUnverifiable
Tag: TypeAlias = str

class SocketEmittedState(ClientModel):
    """
    Complete current values of the actor's emitted fields.
    """

class SocketStatePatch(ClientModel):
    """
    Changed emitted fields; omitted fields are unchanged.
    """
RpcMethodLedgerResult: TypeAlias = OutletLedger
SocketIncoming: TypeAlias = JsonValueInput

class ContractTypes(ClientModel):
    """
    Named wire types used by this generated actor client.
    """
    RpcMethod_ledger_Result: RpcMethodLedgerResult
    RpcMethod_record_Parameter_0: RpcMethodRecordParameter0
    RpcMethod_record_Parameter_1: RpcMethodRecordParameter1
    RpcMethod_record_Result: RpcMethodRecordResult
    SocketIncoming_1: Annotated[SocketIncoming, Field(alias='SocketIncoming')]
    SocketMetadata_1: Annotated[SocketMetadata, Field(alias='SocketMetadata')]
    SocketOutgoing_1: Annotated[SocketOutgoing, Field(alias='SocketOutgoing')]
    SocketState_1: Annotated[SocketState, Field(alias='SocketState')]
    SocketEmittedState_1: Annotated[SocketEmittedState, Field(alias='SocketEmittedState')]
    SocketStatePatch_1: Annotated[SocketStatePatch, Field(alias='SocketStatePatch')]
