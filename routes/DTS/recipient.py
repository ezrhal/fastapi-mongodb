from datetime import  datetime

from fastapi import APIRouter

from config.db.mongodb import db
from models.DTS.Document import AttachmentModel, PostAttachmentModel, PostDocumentModel, PostRecipientModel, \
    RecipientModel, PostRemoveOfficeModel
from fastapi.encoders import jsonable_encoder

router = APIRouter()

@router.post('/remove-office')
async def remove_office(removeoffice: PostRemoveOfficeModel):

    if removeoffice.alloffices == 1:
        await db["Documents"].update_one(
            {"docid": removeoffice.docid},
            {"$set": {"recipient": []}}
        )
    else :

        result = await db["Documents"].update_one(
            {"docid": removeoffice.docid},
            {"$pull": {"recipient": {"officeid": removeoffice.officeid}}}
        )