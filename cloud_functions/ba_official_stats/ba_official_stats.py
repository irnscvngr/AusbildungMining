"""
Retrieve data from Bundesagentur für Arbeit (Arbeitsagentur)
"""
import json
import time
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

def call_api(wtype=0,state='Brandenburg (Bundesland)'):
    """
    Make API call to Arbeitsagentur dependent on requested type of work
    """
    url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v5/jobs"

    params = {
        "angebotsart": str(wtype),
        "wo": state,
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

def get_state_data(wtype=0,state_id=1):
    """
    Basic function that calls Arbeitsagentur and returns the raw data
    for one Bundesland for the specified type of work.
    """
    # Map worktype to actual indexing from Arbeitsagentur
    wtype_dict = {0:1, # Arbeit
                  1:4, # Ausbildung/Duales Studium
                  2:34, # Praktikum/Trainee/Werkstudent
                  3:2 # Selbstständigkeit
                  }
    wtype = wtype_dict[wtype]

    # Map state_id to actual statename string
    with open('data/ars-to-state2.json','r',encoding='utf-8') as f:
        ars_to_state = json.load(f)

    # Store statename
    state = ars_to_state[str(state_id)]

    # Call Arbeitsagentur API
    try:
        data = call_api(wtype,state)
    except Exception as e:
        warnings.warn(f'Connection to Arbeitsagentur failed! {e}')
        return None

    # Get all keys from "facetten" (there's where the actual info is)
    facetten_keys = set(data['facetten'].keys())

    # Store total number of results
    jobs_total = data['maxErgebnisse']

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

    # Add scrape info
    data['gesamtanzahl'] = jobs_total
    data['bundesland'] = state

    return data

def get_full_data(wtype=0):
    """
    Employs get_state_data to get dataset for selected worktype per state.
    Goes through all states to get data for whole country sectioned by state.
    Returns dict with state-names as keys and dataset-dicts as values.
    """
    # Initialize new dict to store data for all states
    full_data = {}

    for state_id in range(1,16+1):
        # Wait to limit scrape-rate
        time.sleep(0.2)
        # Get dataset for current state
        state_data =get_state_data(wtype=wtype, state_id=state_id)
        # Take statename and isolate it (e.g. "Hamburg (Bundesland)"->"Hamburg")
        # then add dataset to dict
        full_data[state_data['bundesland'][:-13]] = state_data

    return full_data

# For tests:
# full_data = get_full_data()
# state = 'Hamburg'
# select_state_data = full_data[state]['branche']
# select_state_data['bundesland'] = state
# select_state_data['timestamp'] = 'jetzt!'
# select_state_data['schema_name'] = 'SchemaName'
# select_state_data['table_name'] = 'TableName'

# items = select_state_data.copy()
# del items['schema_name']
# del items['table_name']

# values = [str(val) for val in items.values()]

# print(', '.join(values))
