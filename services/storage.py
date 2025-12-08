import io
from .supabase import supabase_for_user as supabase
from sqlalchemy.orm import Session
from sqlalchemy import text
from storage3 import SyncStorageClient
from fastapi import HTTPException

from schemas.photos import PhotoMetaSchema, PhotoSchema, PhotoMetadataSchema

import mimetypes
import uuid
from typing import Optional, Dict, Any

BUCKET = 'user_media'
BASE_PREFIX = "profile"
MAX_PHOTOS = 6

def _mime_to_ext(mime_type: str):
    ext = mimetypes.guess_extension(mime_type) or ""
    if ext == ".jpe":
        ext = ".jpg"
    return ext

def _photo_exists(uid: str, id: str, db: Session):
    stmt = text("""
        SELECT 1 FROM profiles.photos WHERE id = :id AND uid = :uid;
    """)
    row = db.execute(stmt, {"id": id, "uid": uid})
    return bool(row)

def get_user_photos(
    storage: SyncStorageClient,
    uid: str,
    db: Session,
    ttl_seconds: int = 500,
    only_approved: bool = False,
):
    where = ["uid = :uid"]
    params = {"uid": uid}
    if only_approved:
        where.append("moderation_status = 'approved'")

    stmt = text(f"""
        SELECT id, uid, path, mime_type, size_bytes, slot, is_primary, moderation_status, created_at
        FROM profiles.photos
        WHERE {' AND '.join(where)}
        ORDER BY is_primary DESC, created_at DESC
    """)
    rows = db.execute(stmt, params).mappings().all()
    if not rows:
        return []

    bucket = storage.from_(BUCKET)
    items: list[PhotoMetaSchema] = []

    for row in rows:
        try:
            signed = bucket.create_signed_url(row["path"], ttl_seconds) or {}
        except Exception:
            continue

        url = signed.get("signedUrl") or signed.get("signedURL")
        if not url:
            continue

        items.append(
            PhotoMetaSchema(
                id=row["id"],
                mime_type=row.get("mime_type"),
                size_bytes=row.get("size_bytes"),
                url=url,
                path=row["path"],
                metadata=PhotoMetadataSchema(
                    slot=row.get("slot"),
                    is_primary=row["is_primary"],
                    moderation_status=row["moderation_status"],
                ),
            )
        )

    return items

def upload_profile_photo(
    uid: str,
    file_bytes: bytes,
    storage: SyncStorageClient,
    mime_type: str,
    db: Session,
    slot: Optional[int] = None,
) -> Dict[str, Any]:
    photo_id = uuid.uuid4()
    path = f"{BASE_PREFIX}/{uid}/photos/{photo_id}{_mime_to_ext(mime_type)}"

    bucket = storage.from_(BUCKET)

    # Literally cannot get the database to handle this with RLS idk why
    if (len(get_user_photos(storage=storage, uid=uid, db=db))+1) > MAX_PHOTOS:
        raise HTTPException(status_code=400, detail=f"There can only be a maximum of {MAX_PHOTOS} per user!")

    stmt = text("""
        INSERT INTO profiles.photos 
            (id, uid, bucket, path, mime_type, size_bytes, slot)
        VALUES
            (:photo_id, :uid, :bucket, :path, :mime_type, :size_bytes, :slot)
        RETURNING *
    """)
    row = db.execute(stmt, {"photo_id": photo_id, "uid": uid, "bucket": BUCKET, "path": path, "mime_type": mime_type, "size_bytes": len(file_bytes), "slot": slot}).mappings().one()

    bucket.upload(
        path=path,
        file=file_bytes if isinstance(file_bytes, (bytes, bytearray)) else io.BytesIO(file_bytes).getvalue(),
        file_options={"content-type": mime_type, "upsert": False},
    )
    signed = bucket.create_signed_url(path, 300) or {}

    return PhotoMetaSchema (
        id = row["id"],
        mime_type = row.get("mime_type"),
        size_bytes = row.get("size_bytes"),
        path = path,
        url = signed.get("signedUrl") or signed.get("signedURL"),
        metadata=PhotoMetadataSchema(
            slot = row.get("slot"),
            is_primary = row["is_primary"],
            moderation_status = row["moderation_status"],
        )
    )
    
def delete_profile_photo(photo: PhotoSchema, uid: str, storage: SyncStorageClient, db: Session):
    if not _photo_exists(uid=uid, id=photo.id, db=db):
        raise HTTPException(status_code=404, detail=f"The photo with id '{id}' does not exist!")
    
    if len(get_user_photos(storage=storage, uid=uid, db=db)) == 0:
        raise HTTPException(status_code=400, detail=f"The user with uid '{uid}' has no photos uploaded!")

    stmt = text("""
        DELETE FROM profiles.photos WHERE id = :id AND uid = :uid;
    """)

    row = db.execute(stmt, {"id": photo.id, "uid": uid})

    bucket = storage.from_(BUCKET)

    res = bucket.remove([photo.path])
    return res


def update_profile_photo(photo: PhotoSchema, mime_type: str, file_bytes: bytes, uid: str, storage: SyncStorageClient, db: Session) -> PhotoMetaSchema:
    if not _photo_exists(uid=uid, id=photo.id, db=db):
        raise HTTPException(status_code=404, detail=f"The photo with id '{photo.id}' does not exist!")
    
    stmt = text("""
        UPDATE profiles.photos 
        SET updated_at = now(), 
            size_bytes = :size_bytes, 
            mime_type = :mime_type
        WHERE id = :id AND uid = :uid
        RETURNING *
    """)

    row = db.execute(stmt, {"size_bytes": len(file_bytes), "mime_type": mime_type, "id": str(photo.id), "uid": uid}).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"The photo with id '{photo.id}' does not exist!")

    bucket = storage.from_(BUCKET)

    res = bucket.update(
        path=photo.path,
        file=file_bytes,
        file_options={"content-type": mime_type, "upsert": True}
    )

    signed = bucket.create_signed_url(photo.path, 300) or {}
    url = signed.get("signedUrl") or signed.get("signedURL")

    return PhotoMetaSchema(
        id = row["id"],
        mime_type = row.get("mime_type"),
        size_bytes = row.get("size_bytes"),
        path = row["path"],
        url = signed.get("signedUrl") or signed.get("signedURL"),
        metadata=PhotoMetadataSchema(
            slot = row.get("slot"),
            is_primary = row["is_primary"],
            moderation_status = row["moderation_status"],

        )
    )


def update_profile_photo_metadata(photo: PhotoSchema, metadata: PhotoMetadataSchema, storage: SyncStorageClient, uid: str, db: Session) -> PhotoMetaSchema:
    if not _photo_exists(uid=uid, id=photo.id, db=db):
        raise HTTPException(status_code=404, detail=f"The photo with id '{photo.id}' does not exist!")
    
    stmt = text("""
        UPDATE profiles.photos
        SET
            updated_at = now(),
            slot = COALESCE(:slot, slot),
            moderation_status = COALESCE(:moderation_status, moderation_status),
            is_primary = COALESCE(:is_primary, is_primary)
        WHERE id = :id AND uid = :uid
        RETURNING *
    """)

    row = db.execute(stmt, {"slot": metadata.slot, "moderation_status": metadata.moderation_status.value or None, "is_primary": metadata.is_primary, "id": str(photo.id), "uid": uid}).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"The photo with id '{photo.id}' does not exist!")

    bucket = storage.from_(BUCKET)

    signed = bucket.create_signed_url(photo.path, 300) or {}
    url = signed.get("signedUrl") or signed.get("signedURL")

    return PhotoMetaSchema(
        id = row["id"],
        mime_type = row.get("mime_type"),
        size_bytes = row.get("size_bytes"),
        path = row["path"],
        url = signed.get("signedUrl") or signed.get("signedURL"),
        metadata=PhotoMetadataSchema(
            slot = row.get("slot"),
            is_primary = row["is_primary"],
            moderation_status = row["moderation_status"],
        )
    )