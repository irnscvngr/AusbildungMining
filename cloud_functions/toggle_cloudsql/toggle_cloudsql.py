"""
This function is used to start the Cloud SQL instance
"""

import os

# pylint:disable=no-name-in-module
from google.cloud import sqladmin
from google.cloud import secretmanager

# pylint:disable=unused-argument
def toggle_cloudsql():
    """
    Connects to specified Cloud SQL instance and starts it.
    """

    # Get project ID from environment variables
    project_id = os.environ.get('GCP_PROJECT_ID')
    # Get SQL instance name from secret manager
    name = f"projects/{project_id}/secrets/{'SQL_INSTANCE_NAME'}/versions/latest"
    # Client for secretmanager
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": name})
    instance_name = response.payload.data.decode("UTF-8")

    # New client for sqladmin
    client = sqladmin.SqlAdminServiceClient()

    try:
        print(f"Starting Cloud SQL instance: {instance_name}")
        # Replace with client.stop to stop instance
        operation = client.start(project=project_id, instance=instance_name)
        operation_name = operation.name
        return "Instance start initiated"  # Return success message
    # pylint:disable=broad-exception-caught
    except Exception as e:
        print(f"Error starting Cloud SQL instance: {e}")
        return f"Error: {e}", 500  # Return error message with 500 status code
