"""
Retrieve data from Bundesagentur für Arbeit (Arbeitsagentur)
"""
import json
import requests
import warnings

from clean_keys import clean_dict_keys

def switch_keys(old_dict,newkeys):
    """
    Takes a dictionary and a dictionary containing mappings from old to new keys.
    Returns dictionary with new keys.
    """
    temp_dict = {}
    for key,value in old_dict.items():
        temp_dict[newkeys[key]] = value
    return temp_dict

def call_api(wtype=0):
    """
    Make API call to Arbeitsagentur dependent on requested type of work
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
    return response.json()

def get_data(wtype=1):
    """
    Basic function that calls Arbeitsagentur and returns the raw data
    for the specified type of work.
    """
    # Map worktype to actual indexing from Arbeitsagentur
    wtype_dict = {0:1, # Arbeit
                  1:4, # Ausbildung/Duales Studium
                  2:34, # Praktikum/Trainee/Werkstudent
                  3:2 # Selbstständigkeit
                  }
    wtype = wtype_dict[wtype]

    # Call Arbeitsagentur API
    try:
        data = call_api(wtype)
    except Exception as e:
        warnings.warn(f'Connection to Arbeitsagentur failed! {e}')
        return None

    # Get all keys from "facetten" (there's where the actual info is)
    facetten_keys = set(data['facetten'].keys())

    # Go through all "facetten" and get counts (that's our actual data)
    for key in facetten_keys:
        data[key] = data['facetten'][key]['counts']

    # Remove all other entries from data
    # ->data now only contains "facetten" and their count-values
    for key in set(data.keys()).difference(facetten_keys):
        del data[key]

    # Import int->str industry naming
    filepath = 'data/industry_keys.json'
    with open(filepath, 'r', encoding='utf-8') as f:
        temp_keys = json.load(f)
    data['branche'] = switch_keys(data['branche'],temp_keys)

    # Get actual naming for index of "befristung"
    temp_keys = {'1':'befristet',
                       '2':'unbefristet',
                       '3':'unbekannt'}
    data['befristung'] = switch_keys(data['befristung'],temp_keys)

    # Get actual naming for index of "arbeitszeit"
    temp_keys = {'ho':'Home Office',
                 'mj':'Mini Job',
                 'snw':'Schicht/Nacht/Wochenende',
                 'tz':'Teilzeit',
                 'vz':'Vollzeit'}
    data['arbeitszeit'] = switch_keys(data['arbeitszeit'],temp_keys)

    # Clean keys so they don't contain umlauts
    for key in data.keys():
        data[key] = clean_dict_keys(data[key])

    return data
