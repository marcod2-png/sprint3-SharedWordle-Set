import os, sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_PUBLISHABLE_KEY"])

username = sys.argv[1]
email, password = f"{username}@wordle.local", "password123"

try:
    res = client.auth.sign_in_with_password({"email":email, "password":password})
except Exception:
    res = client.auth.sign_up({"email":email, "password":password, "options":{"data":{"username":username}}})

if res.session is None:
    sys.exit("No session returned")

print(res.session.access_token)