from supabase import create_client, Client
from storage3 import SyncStorageClient as StorageClient
from config import settings

SUPABASE_URL = settings.supabase_url
SUPABASE_ANON_KEY = settings.supabase_anon_key
SUPABASE_SERVICE_KEY = settings.supabase_service_key

def supabase_for_user(user_jwt: str) -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(user_jwt)
    return client

def storage_for_user(user_jwt: str) -> StorageClient:
    # Storage calls under user identity (RLS applies)
    return StorageClient(
        f"{SUPABASE_URL}/storage/v1/",
        headers={
            "Authorization": f"Bearer {user_jwt}",
            "apiKey": SUPABASE_ANON_KEY, 
        },
    )

supabase_for_service = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    