"""
Main function that acts as entry point for Google Cloud Run Functions
"""
# pylint:disable=import-error
import functions_framework

from toggle_cloudsql import toggle_cloudsql

# pylint:disable=unused-argument
@functions_framework.http
def main(request):
    """
    Entry point for GCP.
    """
    request_type = request.args.get('type')  # Get the 'type' parameter
    # maybe use start and stop in request - then adjust cron-jobs as needed!
    # toggle_cloudsql()

    # Return results as string
    return request_type, 200
