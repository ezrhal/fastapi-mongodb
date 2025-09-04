from datetime import  datetime

from fastapi import APIRouter

from config.db.mongodb import db
from models.DTS.Document import AttachmentModel, PostAttachmentModel, PostDocumentModel, PostRecipientModel, \
    RecipientModel
from fastapi.encoders import jsonable_encoder

router = APIRouter()

@router.post("/savedocument")
async def save_document(post_request: PostDocumentModel):
    doc = jsonable_encoder(post_request)
    document = db["Documents"].insert_one(doc)

@router.post("/updatedocument")
async def update_document(document: PostDocumentModel):
    data = jsonable_encoder(document)  # dict-safe (handles datetimes, enums, etc.)

    # If your document is keyed by Mongo _id (ObjectId), use this instead:
    # selector = {"_id": ObjectId(data["docid"])}
    selector = {"docid": data["docid"]}

    update_doc = {
        "$set": {
            "sourceoffice": data["sourceoffice"],
            "sender": data["sender"],
            "documenttype": data["documenttype"],
            "subject": data["subject"],
            "description": data["description"],
            # update nested fields
            "filelocation.cabinet": data["filelocation"]["cabinet"],
            "filelocation.drawer": data["filelocation"]["drawer"],
            "filelocation.filebox": data["filelocation"]["filebox"],
            "filelocation.folder": data["filelocation"]["folder"],
        }
    }

    # Append to statushistory if provided
    sh = data.get("statushistory")
    if sh:
        if isinstance(sh, list):
            update_doc["$push"] = {"statushistory": {"$each": sh}}
        else:
            update_doc["$push"] = {"statushistory": sh}

    result = db["Documents"].update_one(selector, update_doc)

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

@router.post("/saverecipient")
async def save_recipient(recipient: PostRecipientModel):
    # Build the subdocument that goes into the array (no docid)
    new_recipient = RecipientModel(
        id=recipient.id,
        officeid=recipient.officeid,
        officename=recipient.officename,
        officeabbr=recipient.officeabbr or "",
        datereceived=None,  # or datetime.utcnow() if you want to set it
        timereceived=datetime.now().strftime("%H:%M"),
        userid=recipient.userid,
        name=recipient.name,
    )

    # Convert to plain dict for Mongo (omit None fields if you prefer)
    recipient_doc = new_recipient.model_dump(exclude_none=True)
    # If you want to keep nulls instead, use: new_recipient.model_dump()

    result = db["Documents"].update_one(
        {"docid": recipient.docid},
        {"$push": {"recipient": recipient_doc}},
        upsert=False,
    )

    return {"matched": result.matched_count, "modified": result.modified_count}
