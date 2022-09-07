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
