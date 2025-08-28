from pydantic import BaseModel
from datetime import datetime

class StatusHistoryModel(BaseModel):
    id: str
    status: str
    remarks: str
    userid: int
    name: str
    statusdate: datetime
    statustime: str
    officeid: int

class FileLocationModel(BaseModel):
    cabinet: str
    drawer: str
    filebox: str
    drawer: str

class AttachmentModel(BaseModel):
    id: str
    filename: str

class RecipientModel(BaseModel):
    id: str
    officeid: int
    officename: str
    officeabbr: str
    datereceived: datetime
    timereceived: str
    userid: int
    name: str

class DocumentModel(BaseModel):
    sourceoffice: str
    sender: str
    documenttype: str
    subject: str
    description: str
    statusid: int
    status: str
    actionid: str
    datereceived: datetime
    dateprepared: datetime
    filelocation : FileLocationModel
    attachment: list[AttachmentModel]
    recipient: list[RecipientModel]
    statushistory: list[StatusHistoryModel]