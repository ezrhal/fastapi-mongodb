import uuid
from typing import Optional


def build_object_name(filename: str, idem_key: Optional[str]) -> str:
    # You can change this to a path scheme like tenant/user/date prefixing
    safe_name = filename.replace("\\", "/").split("/")[-1]
    if idem_key:
        return f"idempotent/{idem_key}/{safe_name}"
    return f"uploads/{uuid.uuid4()}/{safe_name}"