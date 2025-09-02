from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from models.DTS.RoutedDocument import DatesModel, InstructionModel, UserActionModel

class keyValueModel(BaseModel):
    key: str
    value: str

class baseRouteModel(BaseModel):
    guidocid: str
    doceid: int
    docid: int
    fromeid: int
    dates: DatesModel

class PostRouteModel(baseRouteModel):
    employees: list[keyValueModel]
    actions: str
    instruction: str
    name: str
    useraction: UserActionModel

class RouteModel(baseRouteModel):
    dateinserted: datetime
    toeid: int
    instruction: list[InstructionModel]
    useraction: Optional[UserActionModel] = None
    isactive: int

