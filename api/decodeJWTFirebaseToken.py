import firebase_admin
from firebase_admin import auth, credentials
import os
import json

def check_token(token):
    # Initialize firebase_admin if not already initialized
    if not firebase_admin._apps:
        # Try to find credentials
        cred_path = './api/serviceAccount.json'
        if not os.path.exists(cred_path):
            cred_path = 'hydrocarbures/firebaseData.json'
        
        if os.path.exists(cred_path):
            with open(cred_path) as f:
                config = json.load(f)
            cred = credentials.Certificate(config)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback to default initialization if possible, or it might fail later
            firebase_admin.initialize_app()

    try:
        # verify_id_token handles the verification of Firebase ID tokens
        # It checks the signature, expiration, audience (project_id), and issuer.
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        # Re-raise as an error that can be caught by the authentication class
        raise e