"""
Firebase Authentication Verification

Verifies Firebase ID tokens from frontend requests. Accepts real Firebase
users - anonymous, email/password, and Google - identically: all three
produce a real signed Firebase ID token, and this module only ever cares
about the verified `uid` inside it. There is no separate "demo" code path.
"""
import os
import json
from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

# Populate real os.environ from backend/.env if present. Needed because this
# module reads its config via plain os.getenv() (a deployed host sets real
# process env vars directly, so this is a no-op there) - app/core/config.py's
# pydantic-settings Settings object parses backend/.env on its own and does
# NOT put those values into os.environ, so without this, anything in
# backend/.env.example (FIREBASE_SERVICE_ACCOUNT_JSON, AUTH_DEV_BYPASS,
# FIREBASE_AUTH_EMULATOR_HOST, ...) would silently never reach this file.
load_dotenv()

# Initialize Firebase Admin SDK.
# Order: Auth Emulator (local dev/test only) -> env var service account ->
# file-based service account -> unconfigured.
if not firebase_admin._apps:
    try:
        emulator_host = os.getenv('FIREBASE_AUTH_EMULATOR_HOST')
        firebase_creds_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')

        if emulator_host:
            # Local/CI only - real Firebase Auth Emulator, not a bypass.
            # The Admin SDK talks to the emulator over plain HTTP and
            # verifies real (emulator-issued) signed tokens; it does not
            # need or accept a real service account in this mode. Requires
            # GCLOUD_PROJECT (or GOOGLE_CLOUD_PROJECT) to also be set so the
            # emulator's project ID matches the frontend's.
            firebase_admin.initialize_app()
            print(f"Firebase Admin SDK initialized against Auth Emulator at {emulator_host} "
                  "- LOCAL/TEST ONLY, do not set FIREBASE_AUTH_EMULATOR_HOST in production")
        elif firebase_creds_json:
            # Parse JSON from environment variable
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized from environment variable")
        else:
            # Fall back to file-based credentials
            cred_path = os.path.join(os.path.dirname(__file__), '../../firebase-service-account.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialized from file")
            else:
                print("Warning: Firebase credentials not found")
                print("Set FIREBASE_SERVICE_ACCOUNT_JSON environment variable or add firebase-service-account.json file")
    except Exception as e:
        print(f"Warning: Firebase Admin SDK not initialized: {e}")
        print("Authentication will not work until Firebase is configured")

security = HTTPBearer()


def compute_dev_bypass_enabled(bypass_requested: bool, environment: str, firebase_configured: bool) -> bool:
    """
    Pure gating logic for the local-dev-only auth bypass, extracted so it can
    be unit tested directly without needing to reload this module under
    different env vars / firebase_admin global state.

    Bypass is enabled only when ALL of:
      1. bypass_requested - AUTH_DEV_BYPASS=true was explicitly set (not
         merely absent Firebase config - a misconfigured deploy that forgot
         Firebase credentials must fail loudly with 401s, never silently
         fall back to this).
      2. environment != "production".
      3. NOT firebase_configured - Firebase Admin genuinely never
         initialized. Once real credentials or the Auth Emulator are
         configured, every request is verified for real regardless of this
         flag, so there is no way to "forget to turn it off" once a real
         project is wired up.
    """
    return bool(bypass_requested) and environment.strip().lower() != 'production' and not firebase_configured


# LOCAL-DEV-ONLY AUTH BYPASS - see compute_dev_bypass_enabled for the gate.
_AUTH_DEV_BYPASS_REQUESTED = os.getenv('AUTH_DEV_BYPASS', 'false').strip().lower() == 'true'
_ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
_DEV_NO_FIREBASE_CONFIGURED = compute_dev_bypass_enabled(
    _AUTH_DEV_BYPASS_REQUESTED, _ENVIRONMENT, bool(firebase_admin._apps)
)
if not firebase_admin._apps and not _DEV_NO_FIREBASE_CONFIGURED:
    print("Firebase Admin SDK is not configured and AUTH_DEV_BYPASS is not enabled - "
          "every request will be rejected with 401 until Firebase is configured.")
if _DEV_NO_FIREBASE_CONFIGURED:
    print("AUTH BYPASS ACTIVE (AUTH_DEV_BYPASS=true, ENVIRONMENT!=production): "
          "all requests are being treated as a single local dev user. "
          "Do not set AUTH_DEV_BYPASS in a deployed environment.")


def is_dev_auth_bypass_active() -> bool:
    """Expose the already-hardened local bypass decision to server policy."""
    return _DEV_NO_FIREBASE_CONFIGURED


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verify Firebase authentication token and return user ID.

    Use this as a dependency in your API routes:
    @app.get("/api/personas")
    async def get_personas(user_id: str = Depends(get_current_user)):
        # user_id is the Firebase UID - the same real, unique UID for an
        # anonymous demo user, an email/password user, or a Google user.
        pass
    """
    if _DEV_NO_FIREBASE_CONFIGURED:
        return "dev-local-user"

    try:
        token = credentials.credentials

        # Verify the ID token
        decoded_token = firebase_auth.verify_id_token(token)
        user_id = decoded_token['uid']

        return user_id

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}"
        )
