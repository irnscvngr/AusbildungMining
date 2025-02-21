"""
Blabla...
"""
import requests
from bs4 import BeautifulSoup

def get_raw_data(wtype=1):
    """
    Basic function that calls Arbeitsagentur and returns the raw data
    for the specified type of work.
    """
    url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v5/jobs"

    params = {
        "angebotsart": str(wtype),
        "page": "1",
        "size": "25",
        "pav": False,
        "facetten": "veroeffentlichtseit,arbeitszeit,arbeitsort,externestellenboersen,branche,arbeitgeber,beruf,befristung"
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,de-DE;q=0.8,de;q=0.7,en-DE;q=0.6",
        "cookie": "marketing_consent=denied; cookie_consent=denied; personalization_consent=denied",
        "correlation-id": "a5996a0b-379e-b423-d4a8-35aa0b02097b",
        "dnt": "1",
        "origin": "https://www.arbeitsagentur.de",
        "priority": "u=1, i",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',  # Corrected quotes
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',  # Corrected quotes
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "x-api-key": "jobboerse-jobsuche"
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    data = response.json()
    
    return data

import json

def ba_official_stats():
    """
    Blabla...
    """
    # data = get_raw_data(wtype=1)
    # with open('ba_example_data.json', 'w') as f:  # 'w' for write mode (overwrites if file exists)
    #         json.dump(data, f, indent=4, ensure_ascii=False)
    
    with open('ba_example_data.json', 'r') as f:  # 'r' for read mode
            data = json.load(f)

    # print(data['maxErgebnisse']) # total count
    
    # Get counts per industry and add proper naming
    with open('cloud_functions/ba_official_stats/industry_keys.json', 'r') as f:  # 'r' for read mode
            industry_keys = json.load(f)
    industry_counts = {}
    for key,value in data['facetten']['branche']['counts'].items():
        industry_counts[industry_keys[key]] = value
    
    print(data['facetten']['arbeitsort'])
    

        
ba_official_stats()
