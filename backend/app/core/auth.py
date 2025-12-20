"""
Firebase Authentication Verification

Verifies Firebase ID tokens from frontend requests.
"""
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

# Initialize Firebase Admin SDK
# Service account JSON should be in backend/firebase-service-account.json
cred_path = os.path.join(os.path.dirname(__file__), '../../firebase-service-account.json')

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Warning: Firebase Admin SDK not initialized: {e}")
        print("Download service account JSON from Firebase Console")

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


