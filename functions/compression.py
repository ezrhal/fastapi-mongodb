# helpers/compress_zstd.py
import io, os, re, unicodedata, mimetypes
import zstandard as zstd
from typing import Iterable

# MIME types that are already compressed (skip to save CPU)
ALREADY_COMPRESSED = {
    "application/zip",
    "application/x-gzip",
    "application/gzip",
    "application/x-7z-compressed",
    "application/x-rar-compressed",
    "application/x-xz",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/avif",
    "image/gif",
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "audio/mpeg",
    "audio/aac",
    "audio/ogg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

def should_compress(content_type: str | None) -> bool:
    if not content_type:
        return True
    ct = content_type.split(";")[0].strip().lower()
    return ct not in ALREADY_COMPRESSED

def safe_filename(original: str) -> str:
    name, ext = os.path.splitext(original)
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    return f"{name}{ext.lower()}"

def zstd_compress_bytes(b: bytes, level: int = 9, threads: int = 0) -> bytes:
    """
    Compress whole payload in-memory. For big files, prefer the streaming-to-temp-file variant.
    threads: -1 uses all cores; 0 means single-threaded.
    """
    cctx = zstd.ZstdCompressor(level=level, threads=threads if threads else 0)
    return cctx.compress(b)

def zstd_decompress_stream(minio_obj, chunk_size: int = 64 * 1024) -> Iterable[bytes]:
    """
    Stream-decompress from MinIO object to plain bytes.
    """
    dctx = zstd.ZstdDecompressor()
    reader = dctx.stream_reader(minio_obj)  # wraps the file-like object
    try:
        while True:
            chunk = reader.read(chunk_size)
            if not chunk:
                break
            yield chunk
    finally:
        reader.close()
        minio_obj.close()
        minio_obj.release_conn()
