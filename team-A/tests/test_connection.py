# Run this program with 'python test_connection.py' ensure you have docker,
# supabase, and .venv running. You can find the variables for your .env file
# by running 'supabase status'

from db import admin

result = admin().table("language").select("*").limit(5).execute()
print (result.data)

# Expected output:
#   [{'language_code': 'eng', 'language_name': 'English'}, {'language_code': 'esp', 'language_name': 'Spanish'}]