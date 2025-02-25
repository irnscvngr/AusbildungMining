"""
Main function that acts as entry point for Google Cloud Run Functions
"""
import os

# pylint:disable=import-error
import functions_framework
import requests

from google.cloud import secretmanager

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

    db_endpoint_url = get_secret('DB_ENDPOINT_URL')

    requests.get(db_endpoint_url,timeout=20)

    # Return results as string
    return "Done!", 200
