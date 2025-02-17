"""
Super basic test function to get started on GCP.
"""
import functions_framework

@functions_framework.http
def hello_world():
    """
    Just return a message.
    """
    return "Hello World! This is a test-run pushed from GitHub.", 200
