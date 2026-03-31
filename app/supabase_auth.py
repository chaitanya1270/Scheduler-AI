# app/supabase_auth.py
from supabase import create_client, Client

SUPABASE_URL = "https://ezxbebqaznshrslfgwbb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV6eGJlYnFhem5zaHJzbGZnd2JiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjYwNzc1MTEsImV4cCI6MjA0MTY1MzUxMX0.eoKGlIlLXwHCFux6hlZ-KpDpjcFL-aLXDE3UQciWU5M"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Verify JWT token from Supabase
async def verify_user(token: str):
    response = supabase.auth.api.get_user(token)
    return response
