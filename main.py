import os, sys
print("=" * 50)
print("DEBUGGING INFO")
print("=" * 50)
print("Current working directory:", os.getcwd())
print("__file__ location:", __file__)
print("Contents of current directory:", os.listdir('.'))
print("Does 'routers' exist?:", os.path.exists('routers'))
if os.path.exists('routers'):
    print("Contents of routers/:", os.listdir('routers'))
    print("Does 'routers/open' exist?:", os.path.exists('routers/open'))
    if os.path.exists('routers/open'):
        print("Contents of routers/open/:", os.listdir('routers/open'))
print("Python path:", sys.path)
print("=" * 50)

from fastapi_socketio import SocketManager
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import routers
from routers.open.auth import router as open_auth_router
from routers.open.profile import router as open_profile_router
from routers.open.user import router as open_user_router

from routers.private.profile import router as private_profile_router
from routers.private.user import router as private_user_router
from routers.private.matchmaking import router as private_matchmaking_router

from config import settings
from services.sockets import register_socket_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown

open_router = APIRouter(tags=["Public"])
open_router.include_router(open_auth_router) 
open_router.include_router(open_user_router)
open_router.include_router(open_profile_router)


private_router = APIRouter(tags=["Private"])
private_router.include_router(private_user_router)
private_router.include_router(private_profile_router)
private_router.include_router(private_matchmaking_router)

origins = [
    "http://localhost:5173",
    "http://localhost:8000",
]


app = FastAPI(title="Main API", lifespan=lifespan)
socket_manager = SocketManager(
    app=app, 
    cors_allowed_origins=origins,
    async_mode='asgi',
    mount_location='/socket.io'
)

register_socket_handlers(socket_manager)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(private_router) # private needs to be mounted before open
app.include_router(open_router)

# Mount static files (e.g. images, JS, CSS)
# app.mount("/static", StaticFiles(directory="static"), name="static")

