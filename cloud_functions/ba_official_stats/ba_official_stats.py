"""
Blabla...
"""
import json

import requests
# from bs4 import BeautifulSoup

def get_raw_data(wtype=1):
    """
    Basic function that calls Arbeitsagentur and returns the raw data
    for the specified type of work.
    """
    url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v5/jobs"

    params = {
        "angebotsart": str(wtype),
        "page": "1",
        "size": "10",
        "pav": False,
        "facetten": "arbeitszeit,arbeitsort,externestellenboersen,branche,arbeitgeber,beruf,befristung"
    }

    headers = {
        "origin": "https://www.arbeitsagentur.de",
        "x-api-key": "jobboerse-jobsuche"
    }

    response = requests.get(url, params=params, headers=headers, timeout=20)

    data = response.json()

    return data

def ba_official_stats():
    """
    Blabla...
    """
    # data = get_raw_data(wtype=1)
    # with open('ba_example_data.json', 'w') as f:  # 'w' for write mode (overwrites if file exists)
    #         json.dump(data, f, indent=4, ensure_ascii=False)

    with open('ba_example_data.json', 'r', encoding='utf-8') as f:  # 'r' for read mode
        data = json.load(f)

    # Get counts per industry and add proper naming
    with open('cloud_functions/ba_official_stats/industry_keys.json', 'r', encoding='utf-8') as f:
        industry_keys = json.load(f)
    industry_counts = {}
    for key,value in data['facetten']['branche']['counts'].items():
        industry_counts[industry_keys[key]] = value

    # data['facetten']['beruf']

    # data['facetten']['arbeitgeber']

    # data['facetten']['arbeitsort']

    # data['facetten']['arbeitsort_plz']

    # data['facetten']['arbeitszeit']

    # data['facetten']['befristung']

    # print(data['facetten']['beruf'])


# ba_official_stats()
