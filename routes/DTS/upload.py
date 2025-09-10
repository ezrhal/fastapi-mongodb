import io
import mimetypes
import os
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Header, Response
from minio import S3Error
from starlette.responses import StreamingResponse
from tenacity import retry, stop_after_attempt, wait_exponential

from Helpers.MInIO.helper import build_object_name
from config.db.mongodb import db
from config.minio_config import minio_client, S3_DTS_BUCKET
from config.config import settings
from functions.compression import safe_filename, should_compress, zstd_compress_bytes, zstd_decompress_stream
from models.DTS.Document import AttachmentModel, PostAttachmentModel, PostDocumentModel, PostRecipientModel, \
    RecipientModel, PostRemoveOfficeModel
from fastapi.encoders import jsonable_encoder

from models.MinIO.minio_model import PresignUploadOut, PresignUploadIn, PresignDownloadOut, PresignDownloadIn
from config.config import settings

router = APIRouter()


@router.post("/files/presign-upload", response_model=PresignUploadOut)
def presign_upload(body: PresignUploadIn, S3_BUCKET=None):
    object_name = build_object_name(body.filename, body.idempotency_key)
    extra_headers = {}
    if body.content_type:
        extra_headers["Content-Type"] = body.content_type

    url = minio_client.presigned_put_object(
        S3_DTS_BUCKET,
        object_name,
        expires=timedelta(seconds=body.expires_seconds),
    )
    return PresignUploadOut(object_name=object_name, url=url, headers=extra_headers)

# ---------- Presigned Download ----------
@router.post("/files/presign-download", response_model=PresignDownloadOut)
def presign_download(body: PresignDownloadIn):
    url = minio_client.presigned_get_object(
        S3_DTS_BUCKET,
        body.object_name,
        expires=timedelta(seconds=body.expires_seconds),
    )
    return PresignDownloadOut(url=url)

# ---------- Direct Streaming Upload (multipart/form-data) ----------
#@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.3, max=3))
@router.post("/files/upload")
async def upload_file(
    doctype: str,
    docyear: str,
    docid: str,
    file: UploadFile = File(...),
    prefix: str = Query("uploads", description="Path prefix, e.g. Memo/2025"),
):
    original_ct = (file.content_type or "application/octet-stream").split(";")[0]
    raw = await file.read()
    original_size = len(raw)

    key_base = f"{safe_filename(file.filename)}"
    prefix = f"{doctype}/{docyear}/{key_base}"

    # Decide whether to compress
    if original_size > settings.THRESHOLD_BYTES * 1024 * 1024:
        compressed = zstd_compress_bytes(raw, level=9, threads=-1)  # good default
        object_name = prefix + ".zst"
        stored_ct = "application/zstd"  # commonly used; clients will download
        metadata = {
            "x-amz-meta-compressed": "zstd",
            "x-amz-meta-original-content-type": original_ct,
            "x-amz-meta-original-size": str(original_size),
            "x-amz-meta-docid" : docid,
        }
        data = io.BytesIO(compressed)
        length = len(compressed)
    else:
        object_name = prefix
        stored_ct = original_ct
        metadata = {
            "x-amz-meta-compressed": "none",
            "x-amz-meta-original-content-type": original_ct,
            "x-amz-meta-original-size": str(original_size),
            "x-amz-meta-docid": docid,
        }
        data = io.BytesIO(raw)
        length = original_size

    try:
        result = minio_client.put_object(
            bucket_name=S3_DTS_BUCKET,
            object_name=object_name,
            data=data,
            length=length,
            content_type=stored_ct,
            metadata=metadata,
        )
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {e.code}") from e

    return {
        "object_name": object_name,
        "stored_content_type": stored_ct,
        "stored_size": length,
        "original_content_type": original_ct,
        "original_size": original_size,
        "compressed": metadata["x-amz-meta-compressed"],
        "etag": result.etag,
    }

# ---------- Direct Download (supports Range) ----------
@router.get(
    "/files/{object_name:path}",
    responses={
        200: {"description": "Full file",
              "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}},
        206: {"description": "Partial content",
              "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}},
        404: {"description": "File not found"},
        416: {"description": "Range Not Satisfiable"},
    },
)
def download_file(
    object_name: str,
    range_header: Optional[str] = Header(None, alias="Range"),
):
    try:
        stat = minio_client.stat_object(S3_DTS_BUCKET, object_name)
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(status_code=404, detail="File not found")
        raise

    size = stat.size
    stored_ct = stat.content_type or "application/octet-stream"
    meta = {k.lower(): v for k, v in (stat.metadata or {}).items()}
    compressed = meta.get("x-amz-meta-compressed", "none")
    original_ct = meta.get("x-amz-meta-original-content-type", stored_ct)

    filename = object_name.split("/")[-1]
    dispo = f"inline; filename*=UTF-8''{quote(filename)}; filename=\"{filename}\""

    # ---------- Range handling: serve stored bytes as-is ----------
    if range_header and range_header.startswith("bytes="):
        try:
            start_s, end_s = range_header.split("=", 1)[1].split("-", 1)
            if start_s == "" and end_s == "":
                raise ValueError("invalid range")
            if start_s == "":
                # suffix range
                suffix_len = int(end_s)
                if suffix_len <= 0:
                    raise ValueError("invalid suffix")
                length = min(suffix_len, size)
                offset = size - length
                end = size - 1
            else:
                offset = int(start_s)
                if offset >= size:
                    return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})
                if end_s == "":
                    end = size - 1
                else:
                    end = min(int(end_s), size - 1)
                    if end < offset:
                        raise ValueError("end < start")
                length = end - offset + 1
        except Exception:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})

        obj = minio_client.get_object(S3_DTS_BUCKET, object_name, offset=offset, length=length)
        headers = {
            "Content-Type": stored_ct,
            "Content-Range": f"bytes {offset}-{end}/{size}",
            "Content-Length": str(length),
            "Accept-Ranges": "bytes",
            "Content-Disposition": dispo,
            "ETag": stat.etag,
        }
        if compressed == "zstd":
            headers["Content-Encoding"] = "zstd"
        return StreamingResponse(
            (chunk for chunk in obj.stream(64 * 1024)),
            status_code=206,
            headers=headers,
            media_type=stored_ct,
        )

    # ---------- No Range ----------
    if compressed == "zstd":
        # Stream-decompress → original content-type; length unknown in advance
        obj = minio_client.get_object(S3_DTS_BUCKET, object_name)
        headers = {
            "Content-Type": original_ct,
            "Accept-Ranges": "bytes",
            "Content-Disposition": dispo,
            "ETag": stat.etag,             # ETag of stored (compressed) object
            "X-Source-Content-Type": stored_ct,
            "X-Source-ETag": stat.etag,
        }
        return StreamingResponse(
            zstd_decompress_stream(obj),
            status_code=200,
            headers=headers,
            media_type=original_ct,
        )

    # Stored uncompressed → proxy as-is
    obj = minio_client.get_object(S3_DTS_BUCKET, object_name)
    headers = {
        "Content-Type": stored_ct,
        "Content-Length": str(size),
        "Accept-Ranges": "bytes",
        "Content-Disposition": dispo,
        "ETag": stat.etag,
    }
    def stream_plain():
        try:
            for chunk in obj.stream(64 * 1024):
                yield chunk
        finally:
            obj.close()
            obj.release_conn()
    return StreamingResponse(stream_plain(), status_code=200, headers=headers, media_type=stored_ct)

# ---------- List & Delete ----------
@router.get("/files")
def list_files(prefix: str, separateFile: bool = True):
    # In production, page with continuation tokens
    objects = minio_client.list_objects(S3_DTS_BUCKET, prefix=prefix, recursive=True)
    out = []

    if not separateFile:
        for o in objects:
            out.append({"name": o.object_name, "size": o.size, "last_modified": o.last_modified.isoformat()})
    else:
        for o in objects:
            filename = o.object_name.split("/")[-1]
            directory = os.path.dirname(o.object_name)
            out.append({"name": filename, "path" : directory, "size": o.size, "last_modified": o.last_modified.isoformat()})

    return out

@router.delete("/files/{object_name:path}")
def delete_file(object_name: str):
    try:
        minio_client.remove_object(S3_DTS_BUCKET, object_name)
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(status_code=404, detail="File not found")
        raise
    return {"deleted": object_name}