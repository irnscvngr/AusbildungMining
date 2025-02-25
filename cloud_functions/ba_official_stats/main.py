"""
Main function that acts as entry point for Google Cloud Run Functions
"""
import os

# pylint:disable=import-error
import functions_framework
import requests

from google.cloud import secretmanager
# For authenticating with database-endpoint cloud function
import google.auth.transport.requests
import google.oauth2.id_token

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

# pylint:disable=unused-argument
@functions_framework.http
def main(request):
    """
    Entry point for GCP.
    """
    # Get the cloud function's URL to setup a request
    db_endpoint_url = get_secret('DB_ENDPOINT_URL')
    
    # Some authentication stuff...
    auth_req = google.auth.transport.requests.Request()
    # The second argument is "audience" which in this case is also
    # the cloud function's URL
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, db_endpoint_url )
    
    # Setup header to send ID token for authentication
    headers = {"Authorization": f"Bearer {id_token}"}

    test_data = {
        "schema_name":"AusbildungMining",
        "table_name":"mock_official_stats",
        "company_count": "5537",
        "integrated_degree_programs": "26549",
        "educational_trainings": "7198",
        "qualifications": "6750",
        "regular_apprenticeships": "105189",
        "inhouse_trainings": "899",
        "educational_trainings_and_regular_apprenticeships": "4295",
        "training_programs": "9937",
        "total_count": "150649"
    }

    # Send request to database endpoint using ID token for authentication
    response = requests.post(db_endpoint_url,
    headers=headers,
    params=test_data,
    timeout=20)

    # Let's have a look at the endpoint's response
    print(response.content, response)

    # Give simple feedback
    return "Function ba-official-stats executed.", 200
