# CMSC447 - Shared-State Wordle
# auth.py - Is for firguring out which player is making a request

# Guests still have tokens, when someone clicks "Continue as gusets" /users/guests
# calls Supabase's anonymous sign-in. Supabase will hand back a real access token
# it's the same kinda that someone with an account would get. Guests like
# registered uses, send in the access token in the Authorization header

from functools import wraps # Helper for writing decorators, copies original functions name onto wrapper
from flask import request, abort, g
from db import admin

def require_user(allow_guests=True): # TODO: We still need to decide who guests play against
    # The decorator rejects requests that do not have a valid Supabase token
    # on success, the Supabase user is available as g.user wihtin this route
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Read token from "Authorization: Bearer <token>" header
            header = request.headers.get("Authorization", "") # If header is missing .get returns "" instead of crashing
            if not header.startswith("Bearer "):
                abort(401)  # 401 Unauthorized. If there is no token, then user is not signed in
            token = header.removeprefix("Bearer ")

            # Verify the token with Supabase
            # The client raises an error on a bad token, which Flask treats as
            # a "500 Internal Server Error" even though it's not really a server
            # error, returning a "401 Unauthorized" makes it more clear that the
            # token is the real problem
            try:
                res = admin().auth.get_user(token)
            except Exception:
                abort(401) # Token could not be validated
            if not res or not res.user:
                abort(401) # No user but also no error safety net

            # Guests have is_anonymous = True, here we are just
            # verifying that the guest is allowed. If guests were
            # not allowed this would fail and return "403 Forbidden"
            if res.user.is_anonymous and not allow_guests:
                abort(403)

            # Give the user to the route. This saves the verified
            # user so that the route can read g.user.id which is
            # the same UUID as player_id from the player table
            g.user = res.user
            return f(*args, **kwargs)
        return wrapper
    return decorator