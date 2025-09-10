import os
from google_auth_oauthlib.flow import Flow

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = ['https://www.googleapis.com/auth/contacts']


def get_google_flow(REDIRECT_URI):
    flow = Flow.from_client_secrets_file(
        os.path.join(BASE_DIR, 'credentials.json'),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow
