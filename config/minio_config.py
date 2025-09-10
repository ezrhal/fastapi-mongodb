import io
import os

import uuid
from datetime import timedelta
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from minio import Minio
from uvicorn import Config

from config.config import settings
from minio.error import S3Error


S3_ENDPOINT   = settings.S3_ENDPOINT.get_secret_value()
S3_ACCESS_KEY = settings.S3_ACCESS_KEY.get_secret_value()
S3_SECRET_KEY = settings.S3_SECRET_KEY.get_secret_value()
S3_REGION     = os.getenv("S3_REGION", "us-east-1")
S3_DTS_BUCKET = settings.S3_DTS_BUCKET.get_secret_value()
S3_SECURE     = False # settings.S3_SECURE.get_secret_value()

minio_client = Minio(
    endpoint=S3_ENDPOINT.replace("http://", "").replace("https://", ""),
    access_key=S3_ACCESS_KEY,
    secret_key=S3_SECRET_KEY,
    secure=S3_SECURE,
    region=S3_REGION,

)