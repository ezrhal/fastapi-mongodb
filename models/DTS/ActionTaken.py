from pydantic import BaseModel
from models.DTS.RoutedDocument import UserActionModel

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