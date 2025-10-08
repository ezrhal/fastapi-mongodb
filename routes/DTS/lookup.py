from datetime import  datetime

from fastapi import APIRouter

from config.db.mongodb import db
from models.DTS.Document import AttachmentModel, PostAttachmentModel, PostDocumentModel, PostRecipientModel, \
    RecipientModel
from fastapi.encoders import jsonable_encoder

router = APIRouter()

@router.get("/getoffices")
async def get_offices():
    offices = db["Documents"].distinct("sourceoffice")

    return offices

@router.get("/getsender")
async def get_sender():
    offices = db["Documents"].distinct("sender")

    return offices