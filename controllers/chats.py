from uuid import UUID
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from controllers.user import _get_user_by_id

def _get_last_message_for_pair(
    session_id: UUID,
    user_a_uid: UUID,
    user_b_uid: UUID,
    db: Session
) -> Optional[Dict[str, Any]]:

    stmt_session = text("""
        SELECT
            id,
            created_at,
            author_uid,
            receiver_uid,
            content,
            is_system,
            'session' AS source
        FROM sessions.chats
        WHERE
            session_id = :session_id
            AND author_uid IN (:a, :b)
            AND (
                receiver_uid IS NULL OR receiver_uid IN (:a, :b)
            )
            AND is_system = FALSE
        ORDER BY created_at DESC
        LIMIT 1
    """)

    session_last = db.execute(stmt_session, {
        "session_id": str(session_id),
        "a": str(user_a_uid),
        "b": str(user_b_uid)
    }).mappings().first()

    stmt_direct = text("""
        SELECT
            id,
            created_at,
            author_uid,
            receiver_uid,
            content,
            FALSE AS is_system,
            'direct' AS source
        FROM users.chat_messages
        WHERE
            (author_uid = :a AND receiver_uid = :b)
            OR
            (author_uid = :b AND receiver_uid = :a)
        ORDER BY created_at DESC
        LIMIT 1
    """)

    direct_last = db.execute(stmt_direct, {
        "a": str(user_a_uid),
        "b": str(user_b_uid)
    }).mappings().first()

    if session_last and direct_last:
        return session_last if session_last["created_at"] >= direct_last["created_at"] else direct_last
    return session_last or direct_last


def _get_user_chats(uid: UUID, db: Session) -> List[Dict[str, Any]]:
    stmt = text("""
        SELECT
            id,
            user_a_uid,
            user_b_uid,
            match_session_id,
            last_message_at,
            status
        FROM users.chats
        WHERE user_a_uid = :uid OR user_b_uid = :uid
        ORDER BY last_message_at DESC
    """)

    chats = db.execute(stmt, {"uid": str(uid)}).mappings().all()
    result: List[Dict[str, Any]] = []

    for c in chats:
        user_a_uid = c["user_a_uid"]
        user_b_uid = c["user_b_uid"]
        session_id = c["match_session_id"]

        other_uid = user_b_uid if user_a_uid == uid else user_a_uid

        other_user = _get_user_by_id(uid=str(other_uid), db=db)
        if not other_user:
            continue

        last_message = _get_last_message_for_pair(
            session_id,
            user_a_uid,
            user_b_uid,
            db
        )

        result.append({
            "id": c["id"],
            "match_session_id": session_id,
            "last_message_at": c["last_message_at"],
            "status": c["status"],
            "other_user": other_user,
            "last_message": last_message,
        })

    return result


def _get_chat_detail(chat_id: UUID, uid: UUID, db: Session) -> Dict[str, Any]:

    stmt = text("""
        SELECT
            id,
            user_a_uid,
            user_b_uid,
            match_session_id,
            last_message_at,
            status
        FROM users.chats
        WHERE
            id = :chat_id
            AND (user_a_uid = :uid OR user_b_uid = :uid)
        LIMIT 1
    """)

    chat = db.execute(stmt, {
        "chat_id": str(chat_id),
        "uid": str(uid)
    }).mappings().first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user_a_uid = chat["user_a_uid"]
    user_b_uid = chat["user_b_uid"]
    session_id = chat["match_session_id"]

    other_uid = user_b_uid if user_a_uid == uid else user_a_uid
    other_user = _get_user_by_id(uid=str(other_uid), db=db)

    if not other_user:
        raise HTTPException(status_code=404, detail="Chat participant not found")

    stmt_session_msgs = text("""
        SELECT
            id,
            created_at,
            author_uid,
            receiver_uid,
            content,
            is_system,
            'session' AS source
        FROM sessions.chats
        WHERE
            session_id = :session_id
            AND author_uid IN (:a, :b)
            AND (
                receiver_uid IS NULL OR receiver_uid IN (:a, :b)
            )
    """)

    session_msgs = db.execute(stmt_session_msgs, {
        "session_id": str(session_id),
        "a": str(user_a_uid),
        "b": str(user_b_uid)
    }).mappings().all()

    stmt_direct_msgs = text("""
        SELECT
            id,
            created_at,
            author_uid,
            receiver_uid,
            content,
            FALSE AS is_system,
            'direct' AS source
        FROM users.chat_messages
        WHERE
            (author_uid = :a AND receiver_uid = :b)
            OR
            (author_uid = :b AND receiver_uid = :a)
    """)

    direct_msgs = db.execute(stmt_direct_msgs, {
        "a": str(user_a_uid),
        "b": str(user_b_uid)
    }).mappings().all()

    merged = list(session_msgs) + list(direct_msgs)
    merged.sort(key=lambda m: m["created_at"])

    return {
        "id": chat["id"],
        "match_session_id": session_id,
        "last_message_at": chat["last_message_at"],
        "status": chat["status"],
        "other_user": other_user,
        "messages": merged,
    }
