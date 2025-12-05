from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from middleware.auth import auth_user
from models.db import get_db
from controllers.session import _get_active_session, _leave_session

router = APIRouter(prefix="/me/session")

@router.get("")
def get_user_session(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Get user's current active session (if any).
    Useful for:
    - Checking if user is already in a session on page load
    - Reconnecting to existing session after refresh
    - Showing session status in UI
    """
    return _get_active_session(uid=uid, db=db)


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