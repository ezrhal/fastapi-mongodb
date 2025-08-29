from fastapi import APIRouter

from config.database import db
from models.DTS.document import DocumentModel, AttachmentModel, PostAttachmentModel, PostDocumentModel
from fastapi.encoders import jsonable_encoder
from models.RouteToEmployeeModel import PostRouteModel
from models.DTS.RoutedDocumentModel import StatusHistoryModel

router = APIRouter()

@router.post("/savedocument")
async def save_document(post_request: PostDocumentModel):
    doc = jsonable_encoder(post_request)
    document = db["Documents"].insert_one(doc)

@router.post("/updatedocument")
async def update_document(document: PostDocumentModel):
    doc = jsonable_encoder(document)
    document = db["Documents"].update_one(
        { "docid" : document.docid},
        {
            "$set": {
                "sourceoffice" : document.sourceoffice,
                "sender" : document.sender,
                "documenttype" : document.documenttype,
                "subject" : document.subject,
                "description" : document.description,
                "filelocation.cabinet" : document.filelocation.cabinet,
                "filelocation.drawer": document.filelocation.drawer,
                "filelocation.filebox": document.filelocation.filebox,
                "filelocation.folder": document.filelocation.folder,
            },
            "$pust" : {
                "statushistory": document.statushistory,
            }
        }
    )

@router.post("/saveattachment")
async def save_attachment(attachment: PostAttachmentModel):
    doc = jsonable_encoder(attachment)

    newAttachment = AttachmentModel(
        id=attachment.id,
        filename=attachment.filename,
    ).model_dump()

    update_action = db["Documents"].update_one(
        {"docid": attachment.docid},
        {
            "$push": {
                "attachment": newAttachment
            }
        }
    )


