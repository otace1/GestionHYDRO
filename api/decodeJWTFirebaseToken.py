import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography import x509


def check_token(token):
    n_decoded = jwt.get_unverified_header(token)
    kid_claim = n_decoded['kid']

    response = requests.get(
        "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-r5wop%40cgw-mobile-apps.iam.gserviceaccount.com")
    x509_key = response.json()[kid_claim]
    key = x509.load_pem_x509_certificate(x509_key.encode('utf-8'), backend=default_backend())
    public_key = key.public_key()
    audience = "https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit"

    decoded_token = jwt.decode(token, public_key, ["RS256"], options=None, audience=audience)

    return decoded_token




# FIREBASE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
# PROJECT_ID = "cgw-mobile-apps"
#
# def check_token(token: str):
#     header = jwt.get_unverified_header(token)
#     kid = header.get("kid")
#     if not kid:
#         raise ValueError("Missing kid in token header")
#
#     resp = requests.get(FIREBASE_CERTS_URL, timeout=10)
#     resp.raise_for_status()
#     certs = resp.json()
#
#     if kid not in certs:
#         raise ValueError("kid not found in Google certs")
#
#     cert_pem = certs[kid]
#     cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"), default_backend())
#     public_key = cert.public_key()
#
#     decoded = jwt.decode(
#         token,
#         public_key,
#         algorithms=["RS256"],
#         audience=PROJECT_ID,
#         options={"verify_exp": True, "verify_aud": True},
#     )
#
#     # Optional but recommended issuer validation
#     expected_iss = f"https://securetoken.google.com/{PROJECT_ID}"
#     if decoded.get("iss") != expected_iss:
#         raise ValueError("Invalid issuer")
#
#     return decoded