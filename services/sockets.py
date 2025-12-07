import logging
from jose import jwt, JWTError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.exceptions import HTTPException

from config import settings
from models.db import SessionLocal
from controllers.user import _set_user_online, _set_user_offline


SECRET = settings.supabase_jwt_secret

logging.basicConfig(level=logging.INFO)

user_sid_map: dict[str, str] = {}
sid_user_map: dict[str, str] = {}

socket_manager = None


async def _get_auth_user_id(sid, auth_data):
    try:
        if not isinstance(auth_data, dict):
            logging.error(f"Invalid socket auth for SID {sid}: {auth_data}")
            return None

        token = auth_data.get("token")
        if not token:
            logging.error(f"Missing token in socket auth for SID {sid}")
            return None

        payload = jwt.decode(
            token,
            SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        sub = payload.get("sub")
        if not sub:
            logging.error(f"Missing sub in JWT for SID {sid}")
            return None

        logging.info(f"User {sub} authenticated via socket")
        return sub

    except JWTError as e:
        logging.error(f"JWT error during socket auth for SID {sid}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during socket auth for SID {sid}: {e}")
        return None


def register_socket_handlers(sm):
    global socket_manager
    socket_manager = sm

    @sm.on("connect")
    async def handle_connect(sid, environ, auth):
        logging.info(f"Connect attempt from SID {sid}")
        logging.info(f"Auth data received: {auth}")

        uid = await _get_auth_user_id(sid, auth)
        if not uid:
            logging.error(f"Authentication failed for SID {sid}")
            await sm.emit("error", {"message": "Invalid or expired authorization token"}, room=sid)
            return False

        uid_str = str(uid)
        user_sid_map[uid_str] = sid
        sid_user_map[sid] = uid_str

        user_room = f"user:{uid_str}"
        await sm.enter_room(sid, user_room)

        db = SessionLocal()
        try:
            _set_user_online(uid=uid_str, db=db)
            db.commit()
            logging.info(f"User {uid_str} set ONLINE via socket")
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"DB error setting user ONLINE for uid={uid_str}: {e}")
        finally:
            db.close()

        logging.info(f"User {uid_str} connected with SID {sid}")
        return True

    @sm.on("disconnect")
    async def handle_disconnect(sid):
        uid = sid_user_map.pop(sid, None)
        if not uid:
            return

        uid_str = str(uid)

        db = SessionLocal()
        try:
            _set_user_offline(uid=uid_str, db=db)
            db.commit()
            logging.info(f"User {uid_str} set OFFLINE via socket")
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"DB error setting user OFFLINE for uid={uid_str}: {e}")
        finally:
            db.close()

        user_sid_map.pop(uid_str, None)
        logging.info(f"User {uid_str} disconnected SID {sid}")

    @sm.on("join_session")
    async def handle_join_session(sid, data):
        raw_uid = sid_user_map.get(sid)
        uid = str(raw_uid) if raw_uid is not None else None
        session_id = None
        if isinstance(data, dict):
            sid_val = data.get("session_id")
            if sid_val is not None:
                session_id = str(sid_val)

        logging.info(f"join_session from SID={sid}, uid={uid}, data={data}")

        if not uid or not session_id:
            await sm.emit("error", {"message": "Invalid session join payload"}, room=sid)
            return

        db = SessionLocal()
        try:
            from controllers.session import _get_active_session_by_id
            session = _get_active_session_by_id(session_id, db)
            logging.info(f"join_session fetched session={session}")

            if not session:
                await sm.emit("error", {"message": "Session not found or inactive"}, room=sid)
                return

            if isinstance(session, dict):
                host_uid = session.get("host_uid")
                guest_uid = session.get("guest_uid")
            else:
                host_uid = getattr(session, "host_uid", None)
                guest_uid = getattr(session, "guest_uid", None)

            host_uid_str = str(host_uid) if host_uid is not None else None
            guest_uid_str = str(guest_uid) if guest_uid is not None else None

            logging.info(f"join_session uid={uid}, host_uid={host_uid_str}, guest_uid={guest_uid_str}")

            if uid not in {host_uid_str, guest_uid_str}:
                await sm.emit("error", {"message": "Not allowed to join this session"}, room=sid)
                return

            room = f"session:{session_id}"
            await sm.enter_room(sid, room)
            logging.info(f"User {uid} joined session {session_id} in room {room}")
            await sm.emit("session_joined", {"session_id": session_id}, room=sid)

        except SQLAlchemyError as e:
            logging.error(f"DB error in join_session for uid={uid}, session_id={session_id}: {e}")
            await sm.emit("error", {"message": "Server error joining session"}, room=sid)
        except Exception as e:
            logging.error(f"Unexpected error in join_session for uid={uid}, session_id={session_id}: {e}")
            await sm.emit("error", {"message": "Server error joining session"}, room=sid)
        finally:
            db.close()

    @sm.on("leave_session")
    async def handle_leave_session(sid, data):
        raw_uid = sid_user_map.get(sid)
        uid = str(raw_uid) if raw_uid is not None else None

        session_id = None
        if isinstance(data, dict):
            sid_val = data.get("session_id")
            if sid_val is not None:
                session_id = str(sid_val)

        if not uid or not session_id:
            return

        room = f"session:{session_id}"
        await sm.leave_room(sid, room)
        logging.info(f"User {uid} left session {session_id} room {room}")
        await sm.emit("session_left", {"session_id": session_id}, room=sid)

    async def _handle_session_chat_message(uid: str, session_id: str, content: str, db: Session, sid: str):
        logging.info(
            f"Persisting chat_message: uid={uid}, session_id={session_id}, content_len={len(content)}"
        )

        from controllers.session import _add_chat_message, _get_active_session_by_id

        message_data = _add_chat_message(
            session_id=session_id,
            author_uid=uid,
            content=content,
            db=db,
        )

        logging.info(f"_add_chat_message returned: {message_data}")

        if isinstance(message_data, dict):
            created_at = message_data["created_at"]
            message_id = message_data["id"]
        else:
            created_at = getattr(message_data, "created_at", None)
            message_id = getattr(message_data, "id", None)

        if created_at is None or message_id is None:
            logging.error(f"message_data missing fields: {message_data}")
            raise RuntimeError("message_data missing created_at or id")

        message_id_str = str(message_id)
        created_at_str = created_at.isoformat()

        session = _get_active_session_by_id(session_id, db)
        logging.info(f"_get_active_session_by_id({session_id}) -> {session}")

        if not session:
            await sm.emit("error", {"message": "Chat session is no longer active"}, room=sid)
            return

        payload = {
            "session_id": session_id,
            "author_uid": uid,
            "content": content,
            "created_at": created_at_str,
            "id": message_id_str,
        }

        room = f"session:{session_id}"
        logging.info(f"Emitting chat_received to room {room} with payload={payload}")
        await sm.emit("chat_received", payload, room=room)
        logging.info(f"Message from {uid} in session {session_id} broadcast to room {room}")

    async def _handle_chat_message_with_chat_id(uid: str, chat_id: str, content: str, db: Session, sid: str):
        stmt_chat = text("""
            SELECT user_a_uid, user_b_uid
            FROM users.chats
            WHERE id = :chat_id
            LIMIT 1
        """)

        chat_row = db.execute(stmt_chat, {"chat_id": chat_id}).mappings().first()
        if not chat_row:
            await sm.emit("error", {"message": "Chat not found"}, room=sid)
            return

        user_a_uid = str(chat_row["user_a_uid"])
        user_b_uid = str(chat_row["user_b_uid"])

        if uid not in {user_a_uid, user_b_uid}:
            await sm.emit("error", {"message": "Not allowed to send in this chat"}, room=sid)
            return

        receiver_uid = user_b_uid if uid == user_a_uid else user_a_uid

        stmt_insert = text("""
            INSERT INTO users.chat_messages (author_uid, receiver_uid, content)
            VALUES (:author_uid, :receiver_uid, :content)
            RETURNING id, created_at
        """)

        message_row = db.execute(stmt_insert, {
            "author_uid": uid,
            "receiver_uid": receiver_uid,
            "content": content,
        }).mappings().first()

        stmt_update = text("""
            UPDATE users.chats
            SET last_message_at = NOW()
            WHERE id = :chat_id
        """)

        db.execute(stmt_update, {"chat_id": chat_id})

        db.commit()

        payload = {
            "chat_id": chat_id,
            "author_uid": uid,
            "receiver_uid": receiver_uid,
            "content": content,
            "created_at": message_row["created_at"].isoformat(),
            "id": str(message_row["id"]),
        }

        room = f"chat:{chat_id}"
        await sm.emit("chat_received", payload, room=room)

        user_room = f"user:{receiver_uid}"
        await sm.emit("chat_notification", payload, room=user_room)

    @sm.on("chat_message")
    async def handle_chat_message(sid, data):
        raw_uid = sid_user_map.get(sid)
        uid = str(raw_uid) if raw_uid is not None else None

        logging.info(f"chat_message from SID={sid}, uid={uid}, data={data}")

        if not isinstance(data, dict):
            logging.warning(f"chat_message invalid data type: {type(data)}")
            await sm.emit("error", {"message": "Invalid message format"}, room=sid)
            return

        session_id = data.get("session_id")
        if session_id is not None:
            session_id = str(session_id)

        chat_id = data.get("chat_id")
        if chat_id is not None:
            chat_id = str(chat_id)

        content = data.get("content")

        if not uid or not content or (not session_id and not chat_id) or (session_id and chat_id):
            logging.warning(
                f"Invalid message payload or unauthenticated sender: "
                f"sid={sid}, uid={uid}, session_id={session_id}, chat_id={chat_id}, content={content!r}"
            )
            await sm.emit("error", {"message": "Invalid message format"}, room=sid)
            return

        db = SessionLocal()
        try:
            if session_id:
                await _handle_session_chat_message(uid, session_id, content, db, sid)
            elif chat_id:
                await _handle_chat_message_with_chat_id(uid, chat_id, content, db, sid)
        except HTTPException as e:
            logging.warning(f"HTTPException in chat_message: {e.detail}")
            await sm.emit("error", {"message": e.detail}, room=sid)
        except SQLAlchemyError as e:
            logging.exception(f"SQLAlchemyError handling chat_message (uid={uid}, session_id={session_id}, chat_id={chat_id}): {e}")
            await sm.emit("error", {"message": "Server error processing message"}, room=sid)
        except Exception as e:
            logging.exception(f"Critical error handling chat_message (uid={uid}, session_id={session_id}, chat_id={chat_id}): {e}")
            await sm.emit("error", {"message": "Server error processing message"}, room=sid)
        finally:
            db.close()

    @sm.on("join_chat")
    async def handle_join_chat(sid, data):
        raw_uid = sid_user_map.get(sid)
        uid = str(raw_uid) if raw_uid is not None else None

        chat_id = None
        if isinstance(data, dict):
            cid = data.get("chat_id")
            if cid is not None:
                chat_id = str(cid)

        if not uid or not chat_id:
            await socket_manager.emit("error", {"message": "Invalid chat join payload"}, room=sid)
            return

        db = SessionLocal()
        try:
            stmt = text("""
                SELECT 1
                FROM users.chats
                WHERE id = :chat_id
                  AND (user_a_uid = :uid OR user_b_uid = :uid)
                LIMIT 1
            """)

            row = db.execute(stmt, {"chat_id": chat_id, "uid": uid}).mappings().first()
            if not row:
                await socket_manager.emit("error", {"message": "Not allowed to join this chat"}, room=sid)
                return

            room = f"chat:{chat_id}"
            await socket_manager.enter_room(sid, room)
            await socket_manager.emit("chat_joined", {"chat_id": chat_id}, room=sid)
        finally:
            db.close()