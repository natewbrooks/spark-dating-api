from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
from logging import log
import logging

from controllers.preferences import _get_user_prefs
from controllers.profile import _get_profile

# Configurable matchmaking settings
MATCHMAKING_TIMEOUT_SECONDS = 15
MATCHMAKING_POLL_INTERVAL_SECONDS = 3

def _get_queue(uid: str, db: Session):
    """Get user's current queue entry."""
    stmt = text("""
        SELECT *
        FROM sessions.matchmaking_queue
        WHERE uid = :uid
        AND expires_at > NOW()
        LIMIT 1
    """)
    queue = db.execute(stmt, {"uid": uid}).mappings().first()
    
    if not queue:
        raise HTTPException(status_code=404, detail=f"User with uid '{uid}' is not currently in the queue!")
    
    return queue


def _user_in_queue(uid: str, db: Session) -> bool:
    """Check if user is in queue (and not expired)."""
    stmt = text("""
        SELECT EXISTS(
            SELECT 1
            FROM sessions.matchmaking_queue
            WHERE uid = :uid
            AND expires_at > NOW()
        ) as in_queue
    """)
    result = db.execute(stmt, {"uid": uid}).mappings().first()
    return result['in_queue'] if result else False


def _join_queue(uid: str, db: Session):
    """Add user to matchmaking queue with their current preferences."""
    if _user_in_queue(uid=uid, db=db):
        raise HTTPException(status_code=409, detail=f"User with uid '{uid}' is already in the queue!")
    
    # Check if user is already in an active session
    from controllers.session import _user_in_session
    if _user_in_session(uid=uid, db=db):
        raise HTTPException(status_code=409, detail=f"User is already in an active session!")
    
    # Get user's current preferences and profile
    user_prefs = _get_user_prefs(uid=uid, db=db)
    user_profile = _get_profile(uid=uid, db=db)
    
    stmt = text("""
        INSERT INTO sessions.matchmaking_queue
            (uid, mode_id, prefs_snapshot, location_snapshot, expires_at)
        VALUES (:uid, :mode_id, CAST(:prefs_snapshot AS jsonb), CAST(:location_snapshot AS jsonb), :expires_at)
        RETURNING *
    """)
    
    # Calculate expiry time (timeout + buffer)
    expires_at = datetime.utcnow() + timedelta(seconds=MATCHMAKING_TIMEOUT_SECONDS + 60)
    
    params = {
        "uid": uid,
        "mode_id": None,
        "prefs_snapshot": json.dumps(jsonable_encoder(user_prefs)),
        "location_snapshot": json.dumps(user_profile.get("location", "")),
        "expires_at": expires_at
    }
    
    res = db.execute(stmt, params).mappings().first()
    return res


def _leave_queue(uid: str, db: Session):
    """Remove user from matchmaking queue."""
    stmt = text("""
        DELETE FROM sessions.matchmaking_queue
        WHERE uid = :uid
        RETURNING *
    """)
    res = db.execute(stmt, {"uid": uid}).mappings().first()
    
    if not res:
        return None
    
    return res

def _exit_matchmaking(uid: str, db: Session):
    """Make user fully exit from matchmaking without putting them back in queue"""
    from controllers.session import _user_in_session, _leave_session
    
    queue_entry = None
    session_result = None

    if _user_in_queue(uid=uid, db=db):
        queue_entry = _leave_queue(uid=uid, db=db)

    if _user_in_session(uid=uid, db=db):
        session_result = _leave_session(uid=uid, db=db)

    return {
        "message": "User fully exited matchmaking",
        "queue_entry": dict(queue_entry) if queue_entry else None,
        "session": dict(session_result) if session_result else None,
    }

def _calculate_age_from_dob(dob) -> int:
    if not dob:
        return 0

    if isinstance(dob, date):
        birth_date = dob
    elif isinstance(dob, str):
        try:
            birth_date = datetime.strptime(dob[:10], "%Y-%m-%d").date()
        except ValueError:
            return 0
    else:
        return 0

    today = datetime.utcnow().date()
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    return age

def _parse_location(location_text: str) -> Optional[tuple[float, float]]:
    """
    Parse location text to extract latitude and longitude.
    
    Supports formats:
    - JSON string: '{"lat": 40.7128, "lng": -74.0060}'
    - Comma-separated: '40.7128,-74.0060'
    - Dict (if already parsed): {'lat': 40.7128, 'lng': -74.0060}
    
    Returns tuple of (latitude, longitude) or None if parsing fails.
    """
    if not location_text:
        return None
    
    try:
        # If it's a string, try to parse as JSON first
        if isinstance(location_text, str):
            # Try JSON format
            if location_text.strip().startswith('{'):
                loc_dict = json.loads(location_text)
                lat = loc_dict.get('lat') or loc_dict.get('latitude')
                lng = loc_dict.get('lng') or loc_dict.get('longitude') or loc_dict.get('lon')
                if lat is not None and lng is not None:
                    return (float(lat), float(lng))
            
            # Try comma-separated format
            if ',' in location_text:
                parts = location_text.split(',')
                if len(parts) == 2:
                    return (float(parts[0].strip()), float(parts[1].strip()))
        
        # If it's already a dict
        elif isinstance(location_text, dict):
            lat = location_text.get('lat') or location_text.get('latitude')
            lng = location_text.get('lng') or location_text.get('longitude') or location_text.get('lon')
            if lat is not None and lng is not None:
                return (float(lat), float(lng))
    
    except (ValueError, json.JSONDecodeError, KeyError, AttributeError):
        return None
    
    return None


def _calculate_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    Uses the Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point (in degrees)
        lat2, lon2: Latitude and longitude of second point (in degrees)
    
    Returns:
        Distance in miles
    """
    import math
    
    # Earth's radius in miles
    R = 3958.8
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def _are_preferences_compatible(host_prefs: dict, guest_prefs: dict, host_profile: dict, guest_profile: dict) -> bool:
    log = logging.getLogger("matchmaking")
    log.info("=== Checking compatibility ===")

    log.info(f"Host prefs: {host_prefs}")
    log.info(f"Guest prefs: {guest_prefs}")
    log.info(f"Host profile: {host_profile}")
    log.info(f"Guest profile: {guest_profile}")

    # Extract host preferences
    host_age_min = host_prefs.get('age_min', 18)
    host_age_max = host_prefs.get('age_max', 99)
    host_target_gender_id = host_prefs.get('target_gender_id')
    host_max_distance = host_prefs.get('max_distance', 999999)

    # Extract guest preferences
    guest_age_min = guest_prefs.get('age_min', 18)
    guest_age_max = guest_prefs.get('age_max', 99)
    guest_target_gender_id = guest_prefs.get('target_gender_id')
    guest_max_distance = guest_prefs.get('max_distance', 999999)

    # Extract profile info
    host_gender_id = host_profile.get('gender_id')
    guest_gender_id = guest_profile.get('gender_id')
    host_dob = host_profile.get('birthdate')
    guest_dob = guest_profile.get('birthdate')
    host_location = host_profile.get('location')
    guest_location = guest_profile.get('location')

    # Calculate ages
    host_age = _calculate_age_from_dob(host_dob) if host_dob else 0
    guest_age = _calculate_age_from_dob(guest_dob) if guest_dob else 0

    log.info(f"Computed ages -> Host age: {host_age}, Guest age: {guest_age}")

    # Gender compatibility (both ways)
    # Resolve gender names
    host_gender_name = host_profile.get("gender_name")
    guest_gender_name = guest_profile.get("gender_name")

    # Resolve target preferences
    host_target_name = host_prefs.get("target_gender_name")
    guest_target_name = guest_prefs.get("target_gender_name")

    # Treat "any" as wildcard
    def accepts(target, actual):
        if target is None:
            return True
        if target.lower() == "any":
            return True
        return target == actual

    # Check both directions
    if not accepts(host_target_name, guest_gender_name):
        log.info(f"Gender fail: host wants {host_target_name}, guest is {guest_gender_name}")
        return False

    if not accepts(guest_target_name, host_gender_name):
        log.info(f"Gender fail: guest wants {guest_target_name}, host is {host_gender_name}")
        return False

    # Age compatibility (both ways)
    if guest_age > 0:
        if not (host_age_min <= guest_age <= host_age_max):
            log.info(f"Age fail: guest_age={guest_age} not in host range [{host_age_min}, {host_age_max}]")
            return False

    if host_age > 0:
        if not (guest_age_min <= host_age <= guest_age_max):
            log.info(f"Age fail: host_age={host_age} not in guest range [{guest_age_min}, {guest_age_max}]")
            return False

    # Distance compatibility (both ways)
    host_coords = _parse_location(host_location)
    guest_coords = _parse_location(guest_location)

    log.info(f"Parsed host coords: {host_coords}, guest coords: {guest_coords}")

    if host_coords and guest_coords:
        host_lat, host_lon = host_coords
        guest_lat, guest_lon = guest_coords

        distance_miles = _calculate_distance_miles(host_lat, host_lon, guest_lat, guest_lon)
        log.info(f"Distance between users: {distance_miles} miles")

        if distance_miles > host_max_distance:
            log.info(f"Distance fail: {distance_miles} > host max {host_max_distance}")
            return False

        if distance_miles > guest_max_distance:
            log.info(f"Distance fail: {distance_miles} > guest max {guest_max_distance}")
            return False

    log.info("Users ARE compatible!")
    return True

def _find_compatible_queue_peer(guest_uid: str, guest_prefs: dict, guest_profile: dict, db: Session) -> Optional[str]:
    """
    Find a compatible peer directly from the matchmaking_queue.
    Returns the UID of the peer if found, or None.
    """
    stmt = text("""
        SELECT 
            q.uid,
            q.prefs_snapshot,
            q.location_snapshot,
            q.enqueued_at
        FROM sessions.matchmaking_queue q
        WHERE q.uid != :guest_uid
          AND q.expires_at > NOW()
        ORDER BY q.enqueued_at ASC
        LIMIT 20
    """)

    rows = db.execute(stmt, {"guest_uid": guest_uid}).mappings().all()

    for row in rows:
        host_uid = row["uid"]
        host_prefs = row["prefs_snapshot"]

        host_profile = _get_profile(uid=host_uid, db=db)
        if not host_profile:
            continue

        # If location is not present fall back to snapshot if needed
        if not host_profile.get("location") and row.get("location_snapshot"):
            host_profile = dict(host_profile)
            host_profile["location"] = row["location_snapshot"]

        if _are_preferences_compatible(
            host_prefs=host_prefs,
            guest_prefs=guest_prefs,
            host_profile=host_profile,
            guest_profile=guest_profile,
        ):
            return host_uid

    return None


def _find_compatible_session(guest_uid: str, guest_prefs: dict, guest_profile: dict, db: Session) -> Optional[str]:
    stmt = text("""
        SELECT 
            s.id,
            s.host_uid,
            q.prefs_snapshot AS host_prefs,
            u.birthdate AS host_birthdate,
            pr.gender_id AS host_gender_id,
            pr.location AS host_location
        FROM sessions.sessions s
        JOIN sessions.matchmaking_queue q
            ON q.uid = s.host_uid
            AND q.expires_at > NOW()
        JOIN users.users u
            ON u.id = s.host_uid
            AND u.deleted_at IS NULL
            AND u.paused = FALSE
        LEFT JOIN profiles.profiles pr
            ON pr.uid = s.host_uid
        WHERE s.status = 'open'
          AND s.guest_uid IS NULL
          AND s.closed_at IS NULL
          AND s.host_uid != :guest_uid
        ORDER BY q.enqueued_at ASC
        LIMIT 20
    """)

    potential_sessions = db.execute(stmt, {"guest_uid": guest_uid}).mappings().all()

    for row in potential_sessions:
        host_prefs = row["host_prefs"]
        host_profile = {
            "birthdate": row["host_birthdate"],
            "gender_id": row["host_gender_id"],
            "location": row["host_location"],
        }

        if _are_preferences_compatible(host_prefs, guest_prefs, host_profile, guest_profile):
            return row["id"]

    return None

def _poll_for_match(uid: str, db: Session):
    from controllers.session import _get_active_session
    
    
    session = _get_active_session(uid=uid, db=db)
    if session:
        session_dict = dict(session)

        host_uid = str(session_dict.get("host_uid")) if session_dict.get("host_uid") else None
        guest_uid = str(session_dict.get("guest_uid")) if session_dict.get("guest_uid") else None
        current_uid = str(uid)

        role = "guest" if guest_uid == current_uid else "host"
        if _user_in_queue(uid=uid, db=db):
            _leave_queue(uid=uid, db=db)
            
        return {
            "status": "matched",
            "role": role,
            "session": session_dict,
            "message": "Match found!",
        }

    if not _user_in_queue(uid=uid, db=db):
        return {
            "status": "cancelled",
            "message": "User not in queue and not in session",
        }

    queue_entry = _get_queue(uid=uid, db=db)
    enqueued_at = queue_entry["enqueued_at"]
    time_elapsed = (datetime.utcnow() - enqueued_at).total_seconds()

    guest_prefs = queue_entry["prefs_snapshot"]
    guest_profile = _get_profile(uid=uid, db=db)

    peer_uid = _find_compatible_queue_peer(
        guest_uid=uid,
        guest_prefs=guest_prefs,
        guest_profile=guest_profile,
        db=db,
    )

    if peer_uid:
        from controllers.session import _create_session_from_queue, _join_session_by_id

        host_uid = peer_uid
        host_queue = _get_queue(uid=host_uid, db=db)
        host_mode_id = host_queue.get("mode_id")
        host_prefs_snapshot = host_queue["prefs_snapshot"]

        session = _create_session_from_queue(
            host_uid=host_uid,
            mode_id=host_mode_id,
            prefs_snapshot=host_prefs_snapshot,
            db=db,
        )
        session_dict = dict(session)

        _join_session_by_id(session_id=session_dict["id"], guest_uid=uid, db=db)

        _leave_queue(uid=uid, db=db)
        _leave_queue(uid=host_uid, db=db)

        _notify_host_of_match(host_uid=host_uid, session_id=session_dict["id"], guest_uid=uid)

        return {
            "status": "matched",
            "role": "guest",
            "session": session_dict,
            "message": "Match found!",
        }

    if time_elapsed >= MATCHMAKING_TIMEOUT_SECONDS:
        mode_id = queue_entry.get("mode_id")
        prefs_snapshot = queue_entry["prefs_snapshot"]

        from controllers.session import _create_session_from_queue

        session = _create_session_from_queue(
            host_uid=uid,
            mode_id=mode_id,
            prefs_snapshot=prefs_snapshot,
            db=db,
        )

        return {
            "status": "timeout",
            "role": "host",
            "session": dict(session),
            "message": "No matches found. Created session as host. Waiting for a compatible user...",
        }

    session_id = _find_compatible_session(
        guest_uid=uid,
        guest_prefs=guest_prefs,
        guest_profile=guest_profile,
        db=db,
    )

    if session_id:
        from controllers.session import _join_session_by_id

        session = _join_session_by_id(session_id=session_id, guest_uid=uid, db=db)
        _leave_queue(uid=uid, db=db)

        _notify_host_of_match(session["host_uid"], session["id"], uid)

        return {
            "status": "matched",
            "role": "guest",
            "session": dict(session),
            "message": "Match found!",
        }

    time_remaining = MATCHMAKING_TIMEOUT_SECONDS - time_elapsed
    return {
        "status": "searching",
        "message": "Still searching for a match...",
        "time_elapsed": int(time_elapsed),
        "time_remaining": int(time_remaining),
        "poll_again_in": MATCHMAKING_POLL_INTERVAL_SECONDS,
    }
    
def _get_matchmaking_state(uid: str, db: Session) -> dict:
    from controllers.session import _get_active_session

    session = _get_active_session(uid=uid, db=db)
    config = {
        "timeout_seconds": MATCHMAKING_TIMEOUT_SECONDS,
        "poll_interval_seconds": MATCHMAKING_POLL_INTERVAL_SECONDS,
    }

    if session:
        if _user_in_queue(uid=uid, db=db):
            _leave_queue(uid=uid, db=db)

        session_dict = dict(session)

        host_uid = str(session_dict.get("host_uid")) if session_dict.get("host_uid") else None
        guest_uid = str(session_dict.get("guest_uid")) if session_dict.get("guest_uid") else None
        current_uid = str(uid)

        other_uid = None
        if current_uid == host_uid:
            other_uid = guest_uid
        elif current_uid == guest_uid:
            other_uid = host_uid

        other_first_name = None
        if other_uid:
            row = db.execute(
                text("SELECT first_name FROM users.users WHERE id = :id LIMIT 1"),
                {"id": other_uid},
            ).mappings().first()
            if row:
                other_first_name = row["first_name"]

        session_dict["other_user_uid"] = other_uid
        session_dict["other_user_first_name"] = other_first_name

        return {
            "state": "in_session",
            "role": "guest" if guest_uid == current_uid else "host",
            "session": session_dict,
            "config": config,
        }

    if _user_in_queue(uid=uid, db=db):
        queue_entry = _get_queue(uid=uid, db=db)
        enqueued_at = queue_entry["enqueued_at"]
        time_elapsed = (datetime.utcnow() - enqueued_at).total_seconds()
        time_remaining = max(0, MATCHMAKING_TIMEOUT_SECONDS - time_elapsed)

        return {
            "state": "searching",
            "time_elapsed": int(time_elapsed),
            "time_remaining": int(time_remaining),
            "config": config,
        }

    return {
        "state": "idle",
        "config": config,
    }

def _notify_host_of_match(host_uid: str, session_id: str, guest_uid: str):
    try:
        from services.sockets import user_sid_map, socket_manager
        import asyncio

        if socket_manager is None:
            return

        host_sid = user_sid_map.get(host_uid)
        if not host_sid:
            return

        loop = asyncio.get_event_loop()
        loop.create_task(
            socket_manager.emit(
                "match_found",
                {
                    "session_id": session_id,
                    "guest_uid": guest_uid,
                    "message": "A match has been found!",
                },
                room=host_sid,
            )
        )
    except Exception as e:
        print(f"Failed to send WebSocket notification: {e}")
