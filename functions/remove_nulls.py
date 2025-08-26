def remove_nulls(d: dict) -> dict:
    """Remove keys with None values (recursively)."""
    return {k: remove_nulls(v) if isinstance(v, dict) else v
            for k, v in d.items() if v is not None}