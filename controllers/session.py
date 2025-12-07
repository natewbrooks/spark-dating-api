from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from typing import Mapping, Optional

from schemas.user import UserInfoSchema
from schemas.session import SessionSchema, CreateSessionSchema
from schemas.session.status import SessionStatusEnum
from controllers.matchmaking import _user_in_queue, _leave_queue, _join_queue

def _user_in_session(uid: str, db: Session):
    exists = _get_active_session(uid=uid, db=db)
    return bool(exists)

def _get_all_user_sessions(uid: str, db: Session):
    stmt = text("""
        SELECT *
        FROM sessions.sessions
        WHERE (
            host_uid = :uid OR guest_uid = :uid
        )
    """)
    sessions = db.execute(stmt, {"uid": uid}).mappings().all()
    return sessions

def _get_active_session_by_id(session_id: str, db: Session) -> Mapping | None:
    """
    Retrieves an active (open) session by its ID. Used primarily by WebSocket handlers.
    """
    stmt = text("""
        SELECT host_uid, guest_uid, status
        FROM sessions.sessions
        WHERE id = :session_id
        AND status = 'open'
        LIMIT 1
    """)
    session = db.execute(stmt, {"session_id": session_id}).mappings().first()
    return session

def _get_active_session(uid: str, db: Session):
    stmt = text("""
        SELECT *
        FROM sessions.sessions
        WHERE (
            host_uid = :uid OR guest_uid = :uid
        ) AND status = 'open'
        LIMIT 1
    """)
    session = db.execute(stmt, {"uid": uid}).mappings().first()
    return session


def _create_session(payload: CreateSessionSchema, host_uid: str, db: Session):
    # Must be in queue to create session
    if not _user_in_queue(uid=host_uid, db=db):
        raise HTTPException(status_code=403, detail=f"User with uid '{host_uid}' is not in the matchmaking queue!")
    
    if _user_in_session(uid=host_uid, db=db):
        raise HTTPException(status_code=409, detail=f"User with uid '{host_uid}' is already in a session!")
    
    payload = jsonable_encoder(payload)
    mode_id = payload.get("mode_id")
    
    # Remove from queue when creating session
    _leave_queue(uid=host_uid, db=db)
    
    stmt = text("""
        INSERT INTO sessions.sessions (status, host_uid, mode_id)
        VALUES (:status, :host_uid, :mode_id)
        RETURNING *
    """)
    res = db.execute(stmt, {"status": SessionStatusEnum.open.value, "host_uid": host_uid, "mode_id": mode_id}).mappings().first()
    return res


def _join_session(guest_uid: str, db: Session):
    # Must be in queue to join session
    if not _user_in_queue(uid=guest_uid, db=db):
        raise HTTPException(status_code=403, detail=f"User with uid '{guest_uid}' is not in the matchmaking queue!")
    
    if _user_in_session(uid=guest_uid, db=db):
        raise HTTPException(status_code=409, detail=f"User with uid '{guest_uid}' is already in a session!")

    # TODO: Make sure the guest_uid preferences are compatible with the session host first
    stmt = text("""
        UPDATE sessions.sessions
        SET guest_uid = :guest_uid
        WHERE (
            closed_at IS NULL
            AND guest_uid IS NULL
            AND status = 'open'
            AND host_uid != :guest_uid
        )
        LIMIT 1
        RETURNING *
    """)
    res = db.execute(stmt, {"guest_uid": guest_uid}).mappings().first()
    
    if not res:
        raise HTTPException(status_code=404, detail="No available open session found to join")
    
    # Remove from queue after successfully joining
    _leave_queue(uid=guest_uid, db=db)
    
    return res

def _join_session_by_id(session_id: str, guest_uid: str, db: Session):
    """Join a specific session by ID (used by matchmaking)."""
    
    if _user_in_session(uid=guest_uid, db=db):
        raise HTTPException(status_code=409, detail=f"User with uid '{guest_uid}' is already in a session!")

    stmt = text("""
        UPDATE sessions.sessions
        SET guest_uid = :guest_uid
        WHERE id = :session_id
          AND guest_uid IS NULL
          AND status = 'open'
          AND closed_at IS NULL
          AND host_uid != :guest_uid
        RETURNING *
    """)
    
    res = db.execute(stmt, {
        "session_id": session_id,
        "guest_uid": guest_uid
    }).mappings().first()
    
    if not res:
        raise HTTPException(status_code=404, detail="Session not available")
    
    return res

def _create_session_from_queue(
    host_uid: str, 
    mode_id: Optional[str], 
    prefs_snapshot: dict, 
    db: Session
):
    """
    Create a session for a user who couldn't find a match.
    User stays in queue so others can find and join their session.
    """
    if _user_in_session(uid=host_uid, db=db):
        raise HTTPException(status_code=409, detail=f"User already in a session!")
    
    stmt = text("""
        INSERT INTO sessions.sessions (status, host_uid, mode_id)
        VALUES (:status, :host_uid, :mode_id)
        RETURNING *
    """)
    
    res = db.execute(stmt, {
        "status": SessionStatusEnum.open.value,
        "host_uid": host_uid,
        "mode_id": mode_id
    }).mappings().first()
    
    # Keep user in queue so their session can be found by others
    # They'll be removed from queue when someone joins
    
    return res

def _leave_session(uid: str, db: Session):
    """Leave current session and handle cleanup."""
    if not _user_in_session(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"User with uid '{uid}' is not in a session!")
    
    session = _get_active_session(uid=uid, db=db)
    
    stmt = text("""
        UPDATE sessions.sessions
        SET 
            status = CASE 
                -- If host is leaving and no guest, close session
                WHEN host_uid = :uid AND guest_uid IS NULL THEN 'closed'
                -- If host is leaving and there is a guest, abandon session
                WHEN host_uid = :uid AND guest_uid IS NOT NULL THEN 'abandoned'
                -- If guest is leaving, keep current status (stay open)
                ELSE status
            END,
            closed_at = CASE
                -- Set closed_at timestamp when closing or abandoning
                WHEN host_uid = :uid THEN NOW()
                ELSE closed_at
            END
        WHERE (host_uid = :uid OR guest_uid = :uid)
          AND closed_at IS NULL
          AND status = 'open'
        RETURNING *
    """)
    
    res = db.execute(stmt, {"uid": uid}).mappings().first()
    
    if not res:
        raise HTTPException(status_code=404, detail="No active session found to leave")
    
    # If host left and there was a guest (abandoned), re-queue the guest
    if res['status'] == 'abandoned' and res['guest_uid']:
        try:
            _join_queue(uid=res['guest_uid'], db=db)
        except:
            pass
    
    # If guest is leaving, set guest_uid to NULL
    if res['guest_uid'] == uid:
        clear_guest_stmt = text("""
            UPDATE sessions.sessions
            SET guest_uid = NULL
            WHERE id = :session_id
            RETURNING *
        """)
        res = db.execute(clear_guest_stmt, {"session_id": res['id']}).mappings().first()
    
    return res

def _add_chat_message(session_id: str, author_uid: str, content: str, db: Session) -> Mapping:
    session = _get_active_session_by_id(session_id, db)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session ID '{session_id}' is not currently active or open."
        )

    host_raw = session["host_uid"]
    guest_raw = session["guest_uid"]

    host_uid = str(host_raw) if host_raw is not None else None
    guest_uid = str(guest_raw) if guest_raw is not None else None
    author_uid_str = str(author_uid)

    if author_uid_str == host_uid:
        receiver_uid = guest_uid
    elif author_uid_str == guest_uid:
        receiver_uid = host_uid
    else:
        raise HTTPException(
            status_code=403,
            detail="User is not part of this active session."
        )

    if receiver_uid is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot send chat message: Session is missing the other participant."
        )

    stmt = text("""
        INSERT INTO sessions.chats (session_id, author_uid, receiver_uid, content, created_at)
        VALUES (:session_id, :author_uid, :receiver_uid, :content, NOW())
        RETURNING id, created_at, content
    """)

    res = (
        db.execute(
            stmt,
            {
                "session_id": session_id,
                "author_uid": author_uid_str,
                "receiver_uid": receiver_uid,
                "content": content,
            },
        )
        .mappings()
        .first()
    )

    return res