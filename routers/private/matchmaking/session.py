from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from middleware.auth import auth_user
from models.db import get_db
from controllers.session import  _leave_session, _get_session_chats
from controllers.matchmaking import (
    _get_matchmaking_state,
    _match_user,
    _get_match_status
)

router = APIRouter(prefix="/me/session")

# @router.get("")
# def get_user_session(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
#     """
#     Get user's current active session (if any).
#     Useful for:
#     - Checking if user is already in a session on page load
#     - Reconnecting to existing session after refresh
#     - Showing session status in UI
#     """
#     return _get_active_session(uid=uid, db=db)


@router.delete("")
def leave_user_session(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Leave current active session.
    Handles cleanup:
    - If host leaves with no guest: closes session
    - If host leaves with guest: abandons session, re-queues guest
    - If guest leaves: clears guest_uid, session stays open
    """
    return _leave_session(uid=uid, db=db)

@router.get("")
def get_matchmaking_state(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_matchmaking_state(uid=uid, db=db)

@router.get("/chats")
def get_current_session_chats(
    limit: int = 100,
    uid: str = Depends(auth_user),
    db: Session = Depends(get_db),
):
    return _get_session_chats(uid=uid, db=db, limit=limit)

@router.post("/match")
async def match_current_partner(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return await _match_user(uid=uid, db=db)

@router.get("/match-status")
def get_match_status(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Get the current match status for the user in their active session.
    
    Returns information about:
    - Whether the current user has matched/liked their partner (you_matched)
    - Whether their partner has matched/liked them (they_matched)
    - Whether it's a mutual match (is_mutual)
    
    Returns:
        {
            "you_matched": bool,      # True if current user liked their partner
            "they_matched": bool,     # True if partner liked current user
            "is_mutual": bool,        # True if both users liked each other
            "session_id": str,        # Current session ID
            "other_uid": str          # Partner's user ID
        }
    
    Raises:
        404: User is not in an active session
        400: User is not properly part of the session
    """
    return _get_match_status(uid=uid, db=db)

