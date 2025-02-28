"""
Main function that acts as entry point for Google Cloud Run Functions
"""
import os
import warnings

# pylint:disable=import-error
import functions_framework
import requests

from google.cloud import secretmanager
# For authenticating with database-endpoint cloud function
import google.auth.transport.requests
import google.oauth2.id_token

from ba_official_stats import get_data

def get_secret(secret_name):
    """
    Retrieves a secret from Secret Manager
    to setup database connection later.
    """
    # Get project ID from environment variables
    project_id = os.environ.get('GCP_PROJECT_ID')
    # Setup connection to GCP secret manager
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": name})
    # Return secret value
    return response.payload.data.decode("UTF-8")

# Get the cloud function's URL to setup a request
db_endpoint_url = get_secret('DB_ENDPOINT_RUN_URL')

audience = get_secret('DB_ENDPOINT_URL')

# Some authentication stuff...
auth_req = google.auth.transport.requests.Request()
id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)

# Setup header to send ID token for authentication
headers = {"Authorization": f"Bearer {id_token}"}

def send_data_to_db(wtype,dict_key,table_name):
    """
    Send selected scraped data to Cloud SQL
    """
    # Get data for wtype "Arbeit"
    data = get_data(wtype)
    res_dict = data[dict_key]
    res_dict['schema_name'] = 'ArbeitsagenturMining'
    res_dict['table_name'] = table_name

    # Send request to database endpoint using ID token for authentication
    try:
        response = requests.post(db_endpoint_url,
        headers=headers,
        params=res_dict,
        timeout=20)
        return response
    except Exception as e:
        warnings.warn(f'Connection to database failed! {e}')
        return

# pylint:disable=unused-argument
@functions_framework.http
def main(request):
    """
    Entry point for GCP.
    """

    # Test call to database-endpoint to verify internal/PRIVATE connection
    try:
        response = requests.get(db_endpoint_url,
        headers=headers,
        timeout=20)
        print('--Private request successful!--')
        print(f"Empty GET request to database endpoint: {response.status_code}, {response.content}")
    except Exception as e:
        warnings.warn(f'Private request failed! {e}')

    # Test call to curlmyip to verify external/PUBLIC connection
    try:
        response = requests.get("https://curlmyip.org/",timeout=20)
        print('--Public request successful!--')
        print(f"External call: {response.status_code}, {response.content}")
    except Exception as e:
        warnings.warn(f'Public request failed! {e}')

    response = send_data_to_db(wtype=0,dict_key='befristung',table_name='arbeit_befristung')
    response = send_data_to_db(wtype=0,dict_key='branche',table_name='arbeit_branche')

    # # Get data for wtype "Arbeit"
    # data = get_data(wtype=0)
    # res_dict = data['befristung']
    # res_dict['schema_name'] = 'ArbeitsagenturMining'
    # res_dict['table_name'] = 'arbeit_befristung'

    # # Send request to database endpoint using ID token for authentication
    # response = requests.post(db_endpoint_url,
    # headers=headers,
    # params=res_dict,
    # timeout=20)

    # Give simple feedback
    return response.content, response.status_code
