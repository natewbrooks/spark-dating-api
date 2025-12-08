from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List
import logging

from controllers.preferences import _get_user_prefs
from controllers.profile import _get_profile
import uuid

# Configurable matchmaking settings
MATCHMAKING_TIMEOUT_SECONDS = 15
MATCHMAKING_POLL_INTERVAL_SECONDS = 3
RECENT_SESSION_COOLDOWN_MINUTES = 15

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
        db.execute(
            text("DELETE FROM sessions.matchmaking_queue WHERE uid = :uid"),
            {"uid": uid},
        )
        
    # Check if user is already in an active session
    from controllers.session import _user_in_session
    if _user_in_session(uid=uid, db=db):
        raise HTTPException(status_code=409, detail=f"User is already in an active session!")
    
    # Get user's current preferences and profile
    try:
        user_prefs = _get_user_prefs(uid=uid, db=db)
    except HTTPException as e:
        # If user has no preferences set, use defaults (match with anyone)
        if e.status_code == 404:
            log = logging.getLogger("matchmaking")
            log.info(f"User {uid} has no preferences set, using defaults (match with anyone)")
            
            user_prefs = {
                "target_gender": "any",
                "age_min": 18,
                "age_max": 99,
                "max_distance": 999999,  # Essentially unlimited
                "extra_options": {}  # No filters
            }
        else:
            raise
    
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

def _have_matched_before(uid_a: str, uid_b: str, db: Session) -> bool:
    a, b = sorted([str(uid_a), str(uid_b)])
    row = db.execute(
        text(
            """
            SELECT 1
            FROM users.chats
            WHERE user_a_uid = :a
              AND user_b_uid = :b
            LIMIT 1
            """
        ),
        {"a": a, "b": b},
    ).first()
    return row is not None


def _has_recent_session(uid_a: str, uid_b: str, db: Session) -> bool:
    cooldown_seconds = RECENT_SESSION_COOLDOWN_MINUTES * 60
    row = db.execute(
        text(
            """
            SELECT 1
            FROM sessions.sessions s
            WHERE (
                (s.host_uid = :a AND s.guest_uid = :b)
                OR
                (s.host_uid = :b AND s.guest_uid = :a)
            )
              AND s.closed_at IS NOT NULL
              AND s.closed_at > NOW() - make_interval(secs => :cooldown_seconds)
            LIMIT 1
            """
        ),
        {"a": uid_a, "b": uid_b, "cooldown_seconds": cooldown_seconds},
    ).first()
    return row is not None


def _normalize_value(val):
    """Normalize a value to lowercase string for comparison."""
    if val is None:
        return None
    return str(val).lower().strip()


def _to_list(val):
    """Convert value to list if it isn't already."""
    if val is None:
        return []
    if isinstance(val, list):
        return [_normalize_value(v) for v in val]
    return [_normalize_value(val)]


def _check_preference_match(profile_value, preference_filter) -> bool:
    """
    Check if a profile value matches a preference filter.
    
    Args:
        profile_value: The actual value from the user's profile (single value or list)
        preference_filter: The preference filter (list of acceptable values)
    
    Returns:
        True if there's at least one match, False otherwise
    """
    # If no preference filter set, accept anything
    if not preference_filter:
        return True
    
    # Convert both to lists for comparison
    profile_values = _to_list(profile_value)
    filter_values = _to_list(preference_filter)
    
    # If no profile values, fail
    if not profile_values:
        return False
    
    # Check if ANY profile value matches ANY filter value
    for pval in profile_values:
        if pval in filter_values:
            return True
    
    return False


def _are_preferences_compatible(host_prefs: dict, guest_prefs: dict, host_profile: dict, guest_profile: dict) -> bool:
    """
    Enhanced compatibility check with extra_options preference filtering.
    
    Logic:
    - Core preferences (gender, age, distance) must match (both ways)
    - Extra options preferences: If a preference field has values, the other user's profile
      must have AT LEAST ONE matching value in that field
    """
    log = logging.getLogger("matchmaking")
    log.info("=== Checking compatibility ===")

    # ========== CORE PREFERENCES ==========
    
    # Extract core preferences
    host_age_min = host_prefs.get('age_min', 18)
    host_age_max = host_prefs.get('age_max', 99)
    host_max_distance = host_prefs.get('max_distance', 999999)
    
    guest_age_min = guest_prefs.get('age_min', 18)
    guest_age_max = guest_prefs.get('age_max', 99)
    guest_max_distance = guest_prefs.get('max_distance', 999999)

    # Extract profile info
    host_dob = host_profile.get('birthdate')
    guest_dob = guest_profile.get('birthdate')
    host_location = host_profile.get('location')
    guest_location = guest_profile.get('location')

    # Calculate ages
    host_age = _calculate_age_from_dob(host_dob) if host_dob else 0
    guest_age = _calculate_age_from_dob(guest_dob) if guest_dob else 0

    log.info(f"Ages -> Host: {host_age}, Guest: {guest_age}")

    # Gender compatibility (both ways)
    host_gender_name = _normalize_value(host_profile.get("gender"))
    guest_gender_name = _normalize_value(guest_profile.get("gender"))
    host_target_name = _normalize_value(host_prefs.get("target_gender"))
    guest_target_name = _normalize_value(guest_prefs.get("target_gender"))

    def accepts_gender(target, actual):
        if not target or target == "any":
            return True
        return target == actual

    if not accepts_gender(host_target_name, guest_gender_name):
        log.info(f"Gender fail: host wants {host_target_name}, guest is {guest_gender_name}")
        return False

    if not accepts_gender(guest_target_name, host_gender_name):
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

    if host_coords and guest_coords:
        host_lat, host_lon = host_coords
        guest_lat, guest_lon = guest_coords

        distance_miles = _calculate_distance_miles(host_lat, host_lon, guest_lat, guest_lon)
        log.info(f"Distance: {distance_miles:.1f} miles")

        if distance_miles > host_max_distance:
            log.info(f"Distance fail: {distance_miles:.1f} > host max {host_max_distance}")
            return False

        if distance_miles > guest_max_distance:
            log.info(f"Distance fail: {distance_miles:.1f} > guest max {guest_max_distance}")
            return False

    # ========== EXTRA OPTIONS PREFERENCES ==========
    
    host_extra = host_prefs.get('extra_options', {}) or {}
    guest_extra = guest_prefs.get('extra_options', {}) or {}
    
    # Define preference fields to check
    # Format: (preference_key, profile_key)
    preference_fields = [
        ('relationship_goal', 'relationship_goal'),
        ('personality_type', 'personality_type'),
        ('love_language', 'love_language'),
        ('attachment_style', 'attachment_style'),
        ('political_view', 'political_view'),
        ('zodiac_sign', 'zodiac_sign'),
        ('religion', 'religion'),
        ('diet', 'diet'),
        ('exercise_frequency', 'exercise_frequency'),
        ('smoke_frequency', 'smoke_frequency'),
        ('drink_frequency', 'drink_frequency'),
        ('sleep_schedule', 'sleep_schedule'),
        ('weed_use', 'weed_use'),
        ('drug_use', 'drug_use'),
        ('interests', 'interests'),
        ('languages_spoken', 'languages_spoken'),
        ('pets', 'pets'),
        ('school', 'school'),
    ]
    
    # Check HOST preferences against GUEST profile
    for pref_key, profile_key in preference_fields:
        host_pref_filter = host_extra.get(pref_key)
        
        # Skip if host has no preference for this field
        if not host_pref_filter:
            continue
        
        # Skip if it's an empty list
        if isinstance(host_pref_filter, list) and len(host_pref_filter) == 0:
            continue
        
        guest_profile_value = guest_profile.get(profile_key)
        
        if not _check_preference_match(guest_profile_value, host_pref_filter):
            log.info(f"Preference fail: host wants {pref_key}={host_pref_filter}, guest has {profile_key}={guest_profile_value}")
            return False
    
    # Check GUEST preferences against HOST profile
    for pref_key, profile_key in preference_fields:
        guest_pref_filter = guest_extra.get(pref_key)
        
        # Skip if guest has no preference for this field
        if not guest_pref_filter:
            continue
        
        # Skip if it's an empty list
        if isinstance(guest_pref_filter, list) and len(guest_pref_filter) == 0:
            continue
        
        host_profile_value = host_profile.get(profile_key)
        
        if not _check_preference_match(host_profile_value, guest_pref_filter):
            log.info(f"Preference fail: guest wants {pref_key}={guest_pref_filter}, host has {profile_key}={host_profile_value}")
            return False

    log.info("✓ Users ARE compatible!")
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
        
        if _have_matched_before(guest_uid, host_uid, db):
            continue
        if _has_recent_session(guest_uid, host_uid, db):
            continue
    
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
        host_uid = row["host_uid"]
        if _have_matched_before(guest_uid, host_uid, db):
            continue
        if _has_recent_session(guest_uid, host_uid, db):
            continue
    
        host_prefs = row["host_prefs"]
        
        # Get full host profile for preference matching
        host_profile = _get_profile(uid=host_uid, db=db)
        if not host_profile:
            continue

        if _are_preferences_compatible(host_prefs, guest_prefs, host_profile, guest_profile):
            return row["id"]

    return None

async def _poll_for_match(uid: str, db: Session):
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
            "status": "found",
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

        await _notify_users_of_session_found(host_uid=host_uid, session_id=session_dict["id"], guest_uid=uid)

        return {
            "status": "found",
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

        await _notify_users_of_session_found(session["host_uid"], session["id"], uid)

        return {
            "status": "found",
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

async def _notify_users_of_session_found(host_uid: str, session_id: str, guest_uid: str):
    log = logging.getLogger("matchmaking")
    
    from services.sockets import user_sid_map, socket_manager

    if socket_manager is None:
        return

    notifications = [
        (host_uid, guest_uid),
        (guest_uid, host_uid)
    ]
    
    for recipient_uid, partner_uid in notifications:
        try:
            recipient_uid_str = str(recipient_uid)
            partner_uid_str = str(partner_uid)
            recipient_sid = user_sid_map.get(recipient_uid_str)

            if not recipient_sid:
                log.info(f"Recipient {recipient_uid_str} not connected, skipping socket notification.")
                continue

            await socket_manager.emit(
                "session_found",
                {
                    "role": "host" if str(host_uid) == str(recipient_uid) else "guest",
                    "session_id": str(session_id),
                    "partner_uid": partner_uid_str,
                    "message": "A match has been found!",
                },
                room=recipient_sid,
            )
            log.info(f"Match notification sent to {recipient_uid_str} (partner: {partner_uid_str}) for session {session_id}.")

        except Exception as e:
            log.error(f"Failed to send WebSocket notification to {recipient_uid_str}: {e}")

async def _match_user(uid: str, db: Session):
    log = logging.getLogger("matchmaking")
    from controllers.session import _get_active_session
    
    session = _get_active_session(uid=uid, db=db)
    if not session:
        raise HTTPException(status_code=404, detail="User is not in an active session")

    session_dict = dict(session)
    host_uid = str(session_dict.get("host_uid")) if session_dict.get("host_uid") else None
    guest_uid = str(session_dict.get("guest_uid")) if session_dict.get("guest_uid") else None
    current_uid = str(uid)

    if current_uid == host_uid:
        other_uid = guest_uid
    elif current_uid == guest_uid:
        other_uid = host_uid
    else:
        raise HTTPException(status_code=400, detail="User is not part of this session")

    if not other_uid:
        raise HTTPException(status_code=400, detail="No partner in this session")

    session_id = session_dict["id"]

    # Check if interaction already exists
    existing = db.execute(
        text(
            """
            SELECT *
            FROM sessions.interactions
            WHERE kind = 'match'
              AND from_uid = :from_uid
              AND to_uid = :to_uid
              AND session_id = :session_id
            LIMIT 1
            """
        ),
        {
            "from_uid": uid,
            "to_uid": other_uid,
            "session_id": session_id,
        },
    ).mappings().first()

    if existing:
        interaction_row = existing
    else:
        interaction_row = db.execute(
            text(
                """
                INSERT INTO sessions.interactions (kind, created_at, from_uid, to_uid, session_id)
                VALUES ('match', NOW(), :from_uid, :to_uid, :session_id)
                RETURNING *
                """
            ),
            {
                "from_uid": uid,
                "to_uid": other_uid,
                "session_id": session_id,
            },
        ).mappings().first()

    # Check if the other user has also matched (reciprocal)
    reciprocal = db.execute(
        text(
            """
            SELECT 1
            FROM sessions.interactions
            WHERE kind = 'match'
              AND from_uid = :other_uid
              AND to_uid = :from_uid
              AND session_id = :session_id
            LIMIT 1
            """
        ),
        {
            "from_uid": uid,
            "other_uid": other_uid,
            "session_id": session_id,
        },
    ).mappings().first()

    is_mutual = reciprocal is not None

    # Get user's display name
    user_row = db.execute(
        text("SELECT first_name FROM users.users WHERE id = :id LIMIT 1"),
        {"id": uid},
    ).mappings().first()

    display_name = user_row["first_name"] if user_row and user_row["first_name"] else "Someone"
    content = f"{display_name} is interested!"

    # Create system message in session chat
    session_message_row = db.execute(
        text(
            """
            INSERT INTO sessions.chats (
                session_id,
                author_uid,
                content,
                is_system,
                created_at
            )
            VALUES (:session_id, :author_uid, :content, true, NOW())
            RETURNING id, session_id, author_uid, content, is_system, created_at
            """
        ),
        {
            "session_id": session_id,
            "author_uid": uid,
            "content": content,
        },
    ).mappings().first()

    msg_payload = {
        "id": str(session_message_row["id"]),
        "session_id": str(session_message_row["session_id"]),
        "author_uid": str(session_message_row["author_uid"]),
        "content": session_message_row["content"],
        "created_at": session_message_row["created_at"].isoformat() + "Z",
        "system": bool(session_message_row["is_system"]),
    }

    # Send WebSocket notifications to both users
    from services.sockets import user_sid_map, socket_manager
    
    if socket_manager is not None:
        notifications = [
            (uid, other_uid),
            (other_uid, uid)
        ]
        
        for recipient_uid, from_uid in notifications:
            try:
                recipient_uid_str = str(recipient_uid)
                from_uid_str = str(from_uid)
                recipient_sid = user_sid_map.get(recipient_uid_str)

                if not recipient_sid:
                    log.info(f"User {recipient_uid_str} not connected, skipping match notification.")
                    continue

                await socket_manager.emit(
                    "chat_received",
                    msg_payload,
                    room=recipient_sid,
                )
                log.info(f"Match chat notification sent to {recipient_uid_str} for session {session_id}.")

                await socket_manager.emit(
                    "match_interaction",
                    {
                        "from_uid": from_uid_str,
                        "to_uid": recipient_uid_str,
                        "session_id": str(session_id),
                        "is_mutual": is_mutual,
                        "message": f"{display_name} is interested!",
                    },
                    room=recipient_sid,
                )
                log.info(f"Match interaction event sent to {recipient_uid_str}.")

            except Exception as e:
                log.error(f"Failed to send WebSocket notification to {recipient_uid_str}: {e}")

    # If mutual, create chat entry
    mutual_chat_row = None
    if is_mutual:
        a, b = sorted([str(uid), str(other_uid)])
        existing_chat = db.execute(
            text(
                """
                SELECT *
                FROM users.chats
                WHERE user_a_uid = :a
                  AND user_b_uid = :b
                LIMIT 1
                """
            ),
            {"a": a, "b": b},
        ).mappings().first()

        if not existing_chat:
            mutual_chat_row = db.execute(
                text(
                    """
                    INSERT INTO users.chats (
                        user_a_uid,
                        user_b_uid,
                        match_session_id,
                        last_message_at,
                        status
                    )
                    VALUES (:a, :b, :session_id, NOW(), 'active')
                    RETURNING *
                    """
                ),
                {"a": a, "b": b, "session_id": session_id},
            ).mappings().first()
            log.info(f"Created mutual chat between {a} and {b}.")
        else:
            mutual_chat_row = existing_chat
            log.info(f"Mutual chat already exists between {a} and {b}.")
            
        # Notify both users of mutual match
        if socket_manager is not None:
            for target_uid in (str(uid), str(other_uid)):
                try:
                    target_sid = user_sid_map.get(target_uid)
                    if target_sid:
                        await socket_manager.emit(
                            "mutual_match",
                            {
                                "session_id": str(session_id),
                                "chat_id": str(mutual_chat_row["id"]) if mutual_chat_row else None,
                                "partner_uid": str(other_uid) if target_uid == str(uid) else str(uid),
                                "message": "It's a mutual match!",
                            },
                            room=target_sid,
                        )
                        log.info(f"Mutual match notification sent to {target_uid}.")
                except Exception as e:
                    log.error(f"Failed to send mutual match notification to {target_uid}: {e}")

    return {
        "message": "Match recorded",
        "session_id": str(session_id),
        "you_uid": str(uid),
        "other_uid": str(other_uid),
        "interaction": dict(interaction_row) if interaction_row else None,
        "is_mutual": is_mutual,
        "chat": dict(mutual_chat_row) if mutual_chat_row else None,
        "system_message": msg_payload,
    }
    
def _get_match_status(uid: str, db: Session):
    """
    Get the match status for the current user in their active session.
    """
    from controllers.session import _get_active_session
    
    session = _get_active_session(uid=uid, db=db)
    if not session:
        raise HTTPException(status_code=404, detail="User is not in an active session")

    session_dict = dict(session)
    host_uid = str(session_dict.get("host_uid")) if session_dict.get("host_uid") else None
    guest_uid = str(session_dict.get("guest_uid")) if session_dict.get("guest_uid") else None
    current_uid = str(uid)

    if current_uid == host_uid:
        other_uid = guest_uid
    elif current_uid == guest_uid:
        other_uid = host_uid
    else:
        raise HTTPException(status_code=400, detail="User is not part of this session")

    if not other_uid:
        return {
            "you_matched": False,
            "they_matched": False,
            "is_mutual": False,
        }

    session_id = session_dict["id"]

    you_matched = db.execute(
        text(
            """
            SELECT EXISTS(
                SELECT 1
                FROM sessions.interactions
                WHERE kind = 'match'
                  AND from_uid = :from_uid
                  AND to_uid = :to_uid
                  AND session_id = :session_id
            ) as matched
            """
        ),
        {
            "from_uid": uid,
            "to_uid": other_uid,
            "session_id": session_id,
        },
    ).mappings().first()

    they_matched = db.execute(
        text(
            """
            SELECT EXISTS(
                SELECT 1
                FROM sessions.interactions
                WHERE kind = 'match'
                  AND from_uid = :from_uid
                  AND to_uid = :to_uid
                  AND session_id = :session_id
            ) as matched
            """
        ),
        {
            "from_uid": other_uid,
            "to_uid": uid,
            "session_id": session_id,
        },
    ).mappings().first()

    you_matched_bool = you_matched["matched"] if you_matched else False
    they_matched_bool = they_matched["matched"] if they_matched else False
    is_mutual = you_matched_bool and they_matched_bool

    return {
        "you_matched": you_matched_bool,
        "they_matched": they_matched_bool,
        "is_mutual": is_mutual,
        "session_id": str(session_id),
        "other_uid": str(other_uid),
    }