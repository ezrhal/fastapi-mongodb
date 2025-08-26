from pydantic import BaseModel

class DocumentModel(BaseModel):
    subject: str
    description: str
    sourceoffice: str

