"""
Thin wrapper around the Supabase client.

This is the ONLY place that talks to `supabase-py` directly. Every other
module (services/routes) should go through `records_service.py`, which
uses `get_supabase()` from here. This keeps the DB dependency swappable
and easy to mock in tests.
"""
from functools import lru_cache

from supabase import create_client, Client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """
    Returns a cached Supabase client instance.

    NOTE for local dev without real Supabase credentials: calling this
    will raise if SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are unset.
    That's intentional — routes should fail loudly rather than silently
    hitting a bad client. See `records_service.py` for where this is used.
    """
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in the environment "
            "(see .env.example) before the Supabase client can be created."
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
