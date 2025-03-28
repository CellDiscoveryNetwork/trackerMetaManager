import os
from google.oauth2 import service_account
import json

# Google Sheets config
# For this metadata manager, we need google sheets and google drive
GOOGLE_API_CONFIG = {
    'api_service_name': 'sheets',
    'api_version': 'v4',
    'credentials_variable': 'GOOGLE_SERVICE_ACCOUNT',
    'scopes': ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
}

def authenticate_with_google(scopes, credentials_variable):
    return service_account.Credentials.from_service_account_info(json.loads(os.environ[credentials_variable]), scopes=scopes)
