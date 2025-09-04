from typing import Optional

from pydantic import BaseModel, Field
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
    folder: str

class AttachmentModel(BaseModel):
    id: str
    filename: str

class PostAttachmentModel(AttachmentModel):
    docid: int


## region RECIPIENT
class RecipientModel(BaseModel):
    id: str
    officeid: int
    officename: str
    officeabbr: str
    datereceived: Optional[datetime] = None
    timereceived: str
    userid: int
    name: str

class PostRecipientModel (RecipientModel):
    docid: int

class PostRemoveOfficeModel(BaseModel):
    docid: int
    officeid: int
    alloffices: int

## endregion

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
    attachment: list[AttachmentModel]  = Field(default_factory=list)
    recipient: list[RecipientModel]  = Field(default_factory=list)
    statushistory: list[StatusHistoryModel]

class PostDocumentModel(DocumentModel):
    docid: int