"""
Main function that acts as entry point for Google Cloud Run Functions
"""
# pylint:disable=import-error
import functions_framework

from start_cloudsql import start_cloud_sql

# pylint:disable=unused-argument
@functions_framework.http
def main(request):
    """
    Entry point for GCP.
    """
    # maybe use start and stop in request - then adjust cron-jobs as needed!
    start_cloud_sql()

    # Return results as string
    return 'Done.', 200
