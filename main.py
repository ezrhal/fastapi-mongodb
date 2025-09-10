from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel
from starlette.middleware.cors import CORSMiddleware
from config.db.pmis_db import engine
from routes import doc_route, reference, verify_user, refresh, calendar
from routes.DTS import document, recipient, upload
from routes.route import router
from config.minio_config import minio_client, S3_DTS_BUCKET

app = FastAPI()

origins = [
    "http://localhost:5173",  # Example: Allow a frontend running on localhost:3000
    "https://pgas.ph",  # Example: Allow a specific production domain
    "http://localhost"
]

# Add CORSMiddleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods (e.g., GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allow all headers
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await ensure_bucket()
    yield

async def ensure_bucket():
    found = minio_client.bucket_exists(S3_DTS_BUCKET)
    if not found:
        minio_client.make_bucket(S3_DTS_BUCKET)

#
# @app.on_event("startup")
# async def on_startup():
#     # Create tables
#     async with engine.begin() as conn:
#         await conn.run_sync(SQLModel.metadata.create_all)

app.include_router(doc_route.router, prefix="/docs", tags=["docs"])
app.include_router(reference.router, prefix="/refs", tags=["refs"])
app.include_router(verify_user.router, prefix="/auth", tags=["auth"])
app.include_router(refresh.router, prefix="/authorize", tags=["authorize"])
app.include_router(calendar.router, prefix="/test", tags=["test"])

## region DTS
app.include_router(document.router, prefix="/document", tags=["document"])
app.include_router(recipient.router, prefix="/document/recipient", tags=["document"])

app.include_router(upload.router, prefix="/document/upload", tags=["document"])

## endregion

app.include_router(router)