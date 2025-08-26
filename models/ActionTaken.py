from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from models.RoutedDocumentModel import DatesModel, InstructionModel, UserActionModel

class ActionTakenModel(BaseModel):
    guidocid:str
    fromeid:int
    status: str
    remarks: str
    userid: int
    name: str
    statustime: str
    officeid: int
    useraction: UserActionModel