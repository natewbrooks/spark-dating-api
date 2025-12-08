from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from sqlalchemy.exc import OperationalError
from fastapi import HTTPException

"""
THE PURPOSE OF THIS FILE IS TO CREATE A REUSABLE SINGLETON SESSION WITH THE SUPABASE DATABASE
IT IS USED IN ALL DATABASE DEPENDENT API ENDPOINTS VIA THE PARAM 'def foo(db: Session = Depends(get_db))'
IT HAS A VERBOSE SAFETY ROLLBACK ALTHOUGH THIS IS REDUNDANT BECAUSE WHEN USING THE DATABASE YOU SHOULD
USE 'with db.begin():' WHICH AUTOMATICALLY COMMITS IF NO EXCEPTIONS / ROLLBACK IF THERE ARE EXCEPTIONS
"""

USER = settings.db_user
PASSWORD = settings.db_pass
HOST = settings.db_host
PORT = settings.db_port
DBNAME = settings.db_name

if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
    raise RuntimeError("Missing DB configuration variables")

# SQLAlchemy string w/ SSL required for Supabase
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# An Engine, which the Session will use for connection
# Increased pool size to match Supabase backend capacity
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=3,
    pool_recycle=1800,
    pool_timeout=30,
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
    future=True,
)

# Session generator
# https://docs.sqlalchemy.org/en/20/orm/session_basics.html
"""The sessionmaker is analogous to the Engine as a module-level factory for function-level sessions / connections. 
As such it also has its own sessionmaker.begin() method, analogous to Engine.begin(), which returns a Session object 
and also maintains a begin/commit/rollback block"""
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# FastAPI dependency with verbose safety rollback and close if it fails
def get_db():
    db = None
    try:
        db = SessionLocal()
    except OperationalError as e:
        # Detect the Supabase MaxClientsInSessionMode error
        msg = str(e.orig) if hasattr(e, "orig") else str(e)
        if "MaxClientsInSessionMode" in msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection limit reached, please try again shortly.",
            )
        # Detect SSL connection errors
        if "SSL connection has been closed unexpectedly" in msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection error, please try again.",
            )
        raise
    
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        if db:
            db.close()