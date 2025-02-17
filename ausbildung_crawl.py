"""
Basic connectivity-check.
"""
import requests

def checkserver() -> int:
    """
    Checks server-response.
    """
    url = "https://www.ausbildung.de"
    response = requests.get(url,timeout=10)
    return response

print("Hello World!")
