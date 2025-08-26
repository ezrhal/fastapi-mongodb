from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional


class DatesModel(BaseModel):
    daterouted: str
    timerouted: str
    dateopened: str
    timeopened: str


class InstructionModel(BaseModel):
    id: str
    from_: str  # 'from' is a reserved keyword in Python, so we rename it
    act: Optional[str] = None
    inst: Optional[str] = None

    class Config:
        fields = {
            'from_': 'from'  # Map JSON field "from" to Python attribute from_
        }


class UserActionModel(BaseModel):
    routed: int
    acted: int
    completed: int


class StatusHistoryModel(BaseModel):
    id: str
    status: str
    remarks: str
    userid: int
    name: str
    statusdate: datetime
    statustime: str
    officeid: int

class StatusHistoryViewModel(StatusHistoryModel):
    statusdatestr: str


class RoutedDocumentModel(BaseModel):
    id: str
    subject: str
    description: str
    documenttype: str
    sourceoffice: str
    sender: str
    datereceived: str
    guidocid: str
    doceid: int
    docid: int
    dates: DatesModel
    instruction: List[InstructionModel]
    useraction: UserActionModel
    statushistory: List[StatusHistoryModel]

class RoutedDocumentViewModel(RoutedDocumentModel):
    statushistory: List[StatusHistoryViewModel]


