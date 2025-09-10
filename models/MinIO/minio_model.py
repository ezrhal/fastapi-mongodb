from typing import Optional

from pydantic import BaseModel


class PresignUploadIn(BaseModel):
    filename: str
    content_type: Optional[str] = None
    # optional user-supplied key for idempotency (same key returns same object name)
    idempotency_key: Optional[str] = None
    expires_seconds: int = 900  # 15 minutes

class PresignUploadOut(BaseModel):
    object_name: str
    url: str
    method: str = "PUT"
    headers: dict

class PresignDownloadIn(BaseModel):
    object_name: str
    expires_seconds: int = 900

class PresignDownloadOut(BaseModel):
    url: str
    method: str = "GET"