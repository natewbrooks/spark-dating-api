from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from middleware.auth import auth_user
from models.db import get_db
from controllers.matchmaking import (
    _get_queue, 
    _join_queue, 
    _leave_queue, 
    _exit_matchmaking,
    _poll_for_match,
    MATCHMAKING_TIMEOUT_SECONDS,
    MATCHMAKING_POLL_INTERVAL_SECONDS
)

router = APIRouter(prefix="/me")


@router.get("/queue")
def get_user_queue(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Get user's current queue status.
    Returns 404 if not in queue.
    """
    return _get_queue(uid=uid, db=db)


@router.post("/join")
def enqueue(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Join matchmaking queue.
    
    After joining, frontend should:
    1. Start polling GET /matchmaking/me/poll every 3 seconds
    2. Show "Searching for match..." UI with countdown
    3. Continue until status is 'matched' or 'timeout'
    
    Returns queue entry information.
    """
    queue_entry = _join_queue(uid=uid, db=db)
    
    return {
        "message": "Joined matchmaking queue",
        "queue_entry": dict(queue_entry),
        "next_steps": {
            "poll_endpoint": "/matchmaking/me/poll",
            "poll_interval_seconds": MATCHMAKING_POLL_INTERVAL_SECONDS,
            "timeout_seconds": MATCHMAKING_TIMEOUT_SECONDS
        }
    }


@router.get("/poll")
def poll_for_match(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Poll for match status. Frontend should call this every POLL_INTERVAL seconds.
    
    Response status values:
    - 'searching': Still looking for match, keep polling
    - 'matched': Match found! Join the session
    - 'timeout': Created session as host, wait for guest
    - 'cancelled': User left queue (edge case)
    
    Frontend should:
    1. If status='searching': Keep polling
    2. If status='matched' or 'timeout': Stop polling, join WebSocket session
    3. If status='cancelled': Handle error state
    """
    return _poll_for_match(uid=uid, db=db)


@router.delete("/queue")
def dequeue(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Leave the matchmaking queue.
    Use this when user cancels matchmaking.
    """
    result = _leave_queue(uid=uid, db=db)
    
    if not result:
        return {"message": "User not in queue (already matched or expired)"}
    
    return {
        "message": "Left matchmaking queue",
        "queue_entry": dict(result)
    }


@router.get("/config")
def get_matchmaking_config():
    """
    Get matchmaking configuration.
    Frontend uses this to configure polling behavior.
    """
    return {
        "timeout_seconds": MATCHMAKING_TIMEOUT_SECONDS,
        "poll_interval_seconds": MATCHMAKING_POLL_INTERVAL_SECONDS,
        "description": f"Poll every {MATCHMAKING_POLL_INTERVAL_SECONDS}s for up to {MATCHMAKING_TIMEOUT_SECONDS}s"
    }
    
@router.delete("/exit")
def exit_matchmaking_session(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Fully exit matchmaking for the current user.

    Intended for guests:
    - Removes user from matchmaking queue (if present)
    - Leaves any active session without re-queuing them
    """
    return _exit_matchmaking(uid=uid, db=db)


# Session state transitions:
# open → closed (host leaves, no guest)
# open → abandoned (host leaves with guest) → guest re-queued
# open → open (guest leaves) → guest_uid cleared