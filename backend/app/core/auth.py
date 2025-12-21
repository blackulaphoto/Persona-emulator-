"""
Firebase Authentication Verification

Verifies Firebase ID tokens from frontend requests.
"""
import os
import json
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

# Initialize Firebase Admin SDK
# Try environment variable first, then fall back to file
if not firebase_admin._apps:
    try:
        # First try to get credentials from environment variable
        firebase_creds_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')

        if firebase_creds_json:
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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verify Firebase ID token and return user ID.
    
    Use this as a dependency in your API routes:
    @app.get("/api/personas")
    async def get_personas(user_id: str = Depends(get_current_user)):
        # user_id is the Firebase UID
        pass
    """
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


