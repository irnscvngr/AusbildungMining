import requests

def checkserver():
    url = "https://www.ausbildung.de"
    response = requests.get(url)
    return response