from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.db import get_db
from middleware.auth import auth_user
from controllers.chats import _get_user_chats, _get_chat_detail
from schemas.chats import ChatListItemSchema, ChatDetailSchema

router = APIRouter(prefix="/me/chats", tags=["Chats"])

@router.get("", response_model=List[ChatListItemSchema])
def list_my_chats(uid: UUID = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_user_chats(uid=uid, db=db)

@router.get("/{chat_id}", response_model=ChatDetailSchema)
def get_chat(chat_id: UUID, uid: UUID = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_chat_detail(uid=uid, chat_id=chat_id, db=db)
