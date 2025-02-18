"""
Initial test to later setup API endpoint for database connection
"""
# pylint:disable=import-error
import functions_framework

@functions_framework.http
def main(request):
    """
    Just return a message.
    """
    return "Hello World! This will be the database API endpoint.", 200
