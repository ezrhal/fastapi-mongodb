from fastapi import APIRouter

from config.database import db
from models.DTS.document import DocumentModel, AttachmentModel, PostAttachmentModel
from fastapi.encoders import jsonable_encoder
from models.RouteToEmployeeModel import PostRouteModel
from models.DTS.RoutedDocumentModel import StatusHistoryModel

router = APIRouter()

@router.post("/savedocument")
async def save_document(post_request: DocumentModel):
    doc = jsonable_encoder(post_request)
    document = db["Documents"].insert_one(doc)


@router.get("/saveattachment")
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
