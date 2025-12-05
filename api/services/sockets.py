import logging
from jose import jwt, JWTError
from sqlalchemy.exc import SQLAlchemyError
from fastapi.exceptions import HTTPException

from config import settings
from models.db import SessionLocal
from controllers.session import _add_chat_message, _get_active_session_by_id
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

        user_sid_map[uid] = sid
        sid_user_map[sid] = uid

        db = SessionLocal()
        try:
            _set_user_online(uid=uid, db=db)
            db.commit()
            logging.info(f"User {uid} set ONLINE via socket")
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"DB error setting user ONLINE for uid={uid}: {e}")
        finally:
            db.close()

        logging.info(f"User {uid} connected with SID {sid}")
        return True

    @sm.on("disconnect")
    async def handle_disconnect(sid):
        uid = sid_user_map.pop(sid, None)
        if not uid:
            return
        
        db = SessionLocal()
        try:
            _set_user_offline(uid=uid, db=db)
            db.commit()
            logging.info(f"User {uid} set OFFLINE via socket")
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"DB error setting user OFFLINE for uid={uid}: {e}")
        finally:
            db.close()

        user_sid_map.pop(uid, None)
        logging.info(f"User {uid} disconnected SID {sid}")

    @sm.on("join_session")
    async def handle_join_session(sid, data):
        uid = sid_user_map.get(sid)
        session_id = data.get("session_id") if isinstance(data, dict) else None
        logging.info(f"join_session from SID={sid}, uid={uid}, data={data}")

        if not uid or not session_id:
            await sm.emit("error", {"message": "Invalid session join payload"}, room=sid)
            return

        db = SessionLocal()
        try:
            session = _get_active_session_by_id(session_id, db)
            if not session:
                await sm.emit("error", {"message": "Session not found or inactive"}, room=sid)
                return

            host_uid = session["host_uid"]
            guest_uid = session["guest_uid"]

            if uid not in {host_uid, guest_uid}:
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
        uid = sid_user_map.get(sid)
        session_id = data.get("session_id") if isinstance(data, dict) else None

        if not uid or not session_id:
            return

        room = f"session:{session_id}"
        await sm.leave_room(sid, room)
        logging.info(f"User {uid} left session {session_id} room {room}")
        await sm.emit("session_left", {"session_id": session_id}, room=sid)

    @sm.on("chat_message")
    async def handle_chat_message(sid, data):
        uid = sid_user_map.get(sid)
        if not isinstance(data, dict):
            await sm.emit("error", {"message": "Invalid message format"}, room=sid)
            return

        session_id = data.get("session_id")
        content = data.get("content")

        if not uid or not session_id or not content:
            logging.warning(f"Invalid message payload or unauthenticated sender: {sid}")
            await sm.emit("error", {"message": "Invalid message format"}, room=sid)
            return

        db = SessionLocal()
        try:
            message_data = _add_chat_message(
                session_id=session_id,
                author_uid=uid,
                content=content,
                db=db,
            )

            session = _get_active_session_by_id(session_id, db)
            if not session:
                await sm.emit("error", {"message": "Chat session is no longer active"}, room=sid)
                return

            payload = {
                "session_id": session_id,
                "author_uid": uid,
                "content": content,
                "created_at": message_data["created_at"].isoformat(),
                "id": message_data["id"],
            }

            room = f"session:{session_id}"
            await sm.emit("chat_received", payload, room=room)
            logging.info(f"Message from {uid} in session {session_id} broadcast to room {room}")

        except HTTPException as e:
            await sm.emit("error", {"message": e.detail}, room=sid)
        except SQLAlchemyError as e:
            logging.error(f"DB error handling chat_message: {e}")
            await sm.emit("error", {"message": "Server error processing message"}, room=sid)
        except Exception as e:
            logging.error(f"Critical error handling chat_message: {e}")
            await sm.emit("error", {"message": "Server error processing message"}, room=sid)
        finally:
            db.close()