from datetime import  datetime

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from config.db.mongodb import db
from models.DTS.Document import AttachmentModel, PostAttachmentModel, PostDocumentModel, PostRecipientModel, \
    RecipientModel, PostRemoveOfficeModel
from fastapi.encoders import jsonable_encoder

router = APIRouter()

@router.post('/remove-office')
async def remove_office(removeoffice: PostRemoveOfficeModel):
    print(removeoffice)
    if removeoffice.alloffices:
        res = await run_in_threadpool(
            db["Documents"].update_one,
            {"docid": removeoffice.docid},
            {"$set": {"recipient": []}}
        )
    else:
        res = await run_in_threadpool(
            db["Documents"].update_one,
            {"docid": removeoffice.docid},
            {"$pull": {"recipient": {"officeid": removeoffice.officeid}}}
        )

    return {"matched": res.matched_count, "modified": res.modified_count}