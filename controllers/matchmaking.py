from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

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


def _calculate_age_from_dob(dob: str) -> int:
    """Calculate age from date of birth string."""
    try:
        birth_date = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.utcnow()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return 0

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
    """
    Determine if two users' preferences are compatible.
    Both users must satisfy each other's criteria.
    """
    
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
    host_dob = host_profile.get('dob')
    guest_dob = guest_profile.get('dob')
    host_location = host_profile.get('location')
    guest_location = guest_profile.get('location')
    
    # Calculate ages
    host_age = _calculate_age_from_dob(host_dob) if host_dob else 0
    guest_age = _calculate_age_from_dob(guest_dob) if guest_dob else 0
    
    # Check gender compatibility (both ways)
    if host_target_gender_id and guest_gender_id:
        if host_target_gender_id != guest_gender_id:
            return False
    
    if guest_target_gender_id and host_gender_id:
        if guest_target_gender_id != host_gender_id:
            return False
    
    # Check age compatibility (both ways)
    if guest_age > 0:
        if not (host_age_min <= guest_age <= host_age_max):
            return False
    
    if host_age > 0:
        if not (guest_age_min <= host_age <= guest_age_max):
            return False
    
    # Check location/distance compatibility (both ways)
    # Parse locations
    host_coords = _parse_location(host_location)
    guest_coords = _parse_location(guest_location)
    
    # Only check distance if both users have valid coordinates
    if host_coords and guest_coords:
        host_lat, host_lon = host_coords
        guest_lat, guest_lon = guest_coords
        
        # Calculate actual distance between users
        distance_miles = _calculate_distance_miles(host_lat, host_lon, guest_lat, guest_lon)
        
        # Both users must be within each other's max distance
        if distance_miles > host_max_distance:
            return False
        
        if distance_miles > guest_max_distance:
            return False
        
    # TODO: Check extra_options compatibility
    
    return True


def _find_compatible_session(guest_uid: str, guest_prefs: dict, guest_profile: dict, db: Session) -> Optional[str]:
    """
    Find a compatible open session based on preferences.
    Returns session_id if found, None otherwise.
    """
    
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
    
    # Check compatibility with each potential session
    for session in potential_sessions:
        host_prefs = session['host_prefs']
        host_profile = {
            'dob': session['host_dob'],
            'gender_id': session['host_gender_id'],
            'location': session['host_location']
        }
        
        if _are_preferences_compatible(host_prefs, guest_prefs, host_profile, guest_profile):
            return session['id']
    
    return None


def _poll_for_match(uid: str, db: Session):
    """
    Poll for a match. Called by frontend every POLL_INTERVAL seconds.
    
    Returns:
    - dict with status indicating what happened:
      - 'matched': Found a match and joined as guest
      - 'timeout': Timeout reached, created session as host
      - 'searching': Still searching, keep polling
      - 'cancelled': User left queue (shouldn't happen in normal flow)
    """
    # Check if user is still in queue
    if not _user_in_queue(uid=uid, db=db):
        # User was either matched or left queue
        from controllers.session import _get_active_session
        session = _get_active_session(uid=uid, db=db)
        if session:
            return {
                "status": "matched",
                "role": "guest" if session['guest_uid'] == uid else "host",
                "session": dict(session),
                "message": "Match found!"
            }
        else:
            return {
                "status": "cancelled",
                "message": "User not in queue and not in session"
            }
    
    # Get queue entry to check timing
    queue_entry = _get_queue(uid=uid, db=db)
    enqueued_at = queue_entry['enqueued_at']
    time_elapsed = (datetime.utcnow() - enqueued_at).total_seconds()
    
    # Check if timeout has been reached
    if time_elapsed >= MATCHMAKING_TIMEOUT_SECONDS:
        # Timeout reached - create session as host
        mode_id = queue_entry.get('mode_id')
        prefs_snapshot = queue_entry['prefs_snapshot']
        
        from controllers.session import _create_session_from_queue
        session = _create_session_from_queue(
            host_uid=uid,
            mode_id=mode_id,
            prefs_snapshot=prefs_snapshot,
            db=db
        )
        
        # Keep user in queue so others can find their session
        
        return {
            "status": "timeout",
            "role": "host",
            "session": dict(session),
            "message": "No matches found. Created session as host. Waiting for a compatible user..."
        }
    
    # Try to find a match
    guest_prefs = queue_entry['prefs_snapshot']
    guest_profile = _get_profile(uid=uid, db=db)
    
    session_id = _find_compatible_session(
        guest_uid=uid,
        guest_prefs=guest_prefs,
        guest_profile=guest_profile,
        db=db
    )
    
    if session_id:
        # Found a match! Join as guest
        from controllers.session import _join_session_by_id
        session = _join_session_by_id(session_id=session_id, guest_uid=uid, db=db)
        _leave_queue(uid=uid, db=db)
        
        # Notify host via WebSocket
        _notify_host_of_match(session['host_uid'], session['id'], uid)
        
        return {
            "status": "matched",
            "role": "guest",
            "session": dict(session),
            "message": "Match found!"
        }
    
    # No match yet - keep searching
    time_remaining = MATCHMAKING_TIMEOUT_SECONDS - time_elapsed
    return {
        "status": "searching",
        "message": "Still searching for a match...",
        "time_elapsed": int(time_elapsed),
        "time_remaining": int(time_remaining),
        "poll_again_in": MATCHMAKING_POLL_INTERVAL_SECONDS
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
