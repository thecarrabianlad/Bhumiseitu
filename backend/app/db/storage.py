"""
Thin helper around Supabase Storage for uploading raw document files.

Kept separate from `supabase_client.py` (the DB client factory) so the
upload logic has one clear home.
"""
import uuid

from app.core.config import get_settings
from app.db.supabase_client import get_supabase


def upload_document_file(file_bytes: bytes, original_filename: str, content_type: str) -> str:
    """
    Uploads a file to the configured Supabase Storage bucket and returns
    the storage path (key) it was saved under.
    """
    settings = get_settings()
    supabase = get_supabase()

    extension = ""
    if "." in original_filename:
        extension = "." + original_filename.rsplit(".", 1)[-1]
    storage_path = f"{uuid.uuid4()}{extension}"

    supabase.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )
    return storage_path
