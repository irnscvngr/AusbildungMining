"""
Super basic test function to get started on GCP.
"""
# pylint:disable=import-error
import functions_framework

# pylint:disable=unused-argument
@functions_framework.http
def hello_world(request):
    """
    Just return a message.
    """
    return "Hello World! This is a test-run pushed from GitHub.", 200
