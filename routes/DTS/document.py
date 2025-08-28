from fastapi import APIRouter

from config.database import db
from models.DTS.document import DocumentModel
from models.RouteToEmployeeModel import PostRouteModel
from models.DTS.RoutedDocumentModel import StatusHistoryModel

router = APIRouter()

@router.post("/savedocument")
async def save_document(document: DocumentModel):
    document = db["Documents"].insert_one(document)

