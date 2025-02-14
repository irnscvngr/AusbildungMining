import warnings
import re
import os

import requests
from bs4 import BeautifulSoup
import psycopg2

from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()

def get_official_stats():
    """
    This function connects to Ausbildung.de and retrieves their "official" counts
    for number of companies and vacancies.
    It goes to the company overview page and takes the number that's listed there as
    well as performing an "empty" search to just take the overall results.
    These values are good reference to evaluate other scraping results.
    """
    # Progress:
    print("\n--Receiving official stats--\n")
    # --- GET COMPANY COUNT
    url = "https://www.ausbildung.de/unternehmen/alle/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content,'html.parser')
    try:
        print("Processing: company_count")
        # Company count can be found in static HTML
        cl = soup.find(class_="corporations-listing")
        company_count = cl.find(class_="blob").text
        # The result is of format "5.258 Unternehmen"
        # ->Extract digits and remove dot
        company_count = ''.join(re.findall(r'\d+',company_count))
    except:
        # In case of failure just store nan
        warnings.warn("Company count not found in HTML! Storing nan instead.")
        company_count = "nan"

    # Initialize results dictionary and add company count to it
    res_dict = {"company_count":company_count}

    # --- GET VACANCY COUNTS
    url = "https://www.ausbildung.de/ajax/main_search/"

    # Setup API search parameters
    params = {
        "form_main_search[rlon]": 6.9078,
        "form_main_search[rlat]": 51.222,
        "form_main_search[radius]": 1000,
        "form_main_search[show_integrated_degree_programs]": 0,
        "form_main_search[show_educational_trainings]": 0,
        "form_main_search[show_qualifications]": 0,
        "form_main_search[show_regular_apprenticeships]": 0,
        "form_main_search[show_inhouse_trainings]": 0,
        "form_main_search[show_educational_trainings_and_regular_apprenticeships]": 0,
        "form_main_search[show_training_programs]": 0,
    }

    # Perform an API call for every search-variant
    for key in list(params.keys())[3:]:
        # Take API-parameter and extract "clean" version of it
        # e.g.: "form_main_search[show_inhouse_trainings]" -> "inhouse_trainings"
        key_clean = re.search(r"\[([^\]]+)\]",key)[1].replace('show_','').strip()
        # Progress:
        print(f"Processing: {key_clean}")
        try:
            # Select a parameter
            params[key] = 1
            # Perform API-call:
            response = requests.get(url, params=params)
            soup = BeautifulSoup(response.content,'html.parser')
            # Extract count-element
            res = soup.find(class_="title title--size-md title--left").text
            # Extract actual number
            res = re.search(r"\d+",res)[0]
            # Store value to results dictionary
            res_dict[key_clean] = res
            # Reset API parameter
            params[key] = 0
        except:
            # In case of failure just store nan
            warnings.warn(f"API call failed for {key_clean}! Storing nan instead.")
            res_dict[key_clean] = "nan"
    
    # Set all API parameters to 1 so that the search returns a total count
    for key in list(params.keys())[3:]:
        params[key] = 1
    # Perform API call for overall vacancy count
    try:
        print("Processing: total_count")
        # Perform API call
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.content,'html.parser')
        # Extract count-element
        res = soup.find(class_="title title--size-md title--left").text
        # Extract actual number
        res = re.search(r"\d+",res)[0]
        # Store value to results dictionary
        res_dict['total_count'] = res
    except:
        # In case of failure just store nan
        warnings.warn(f"API call failed for total_count! Storing nan instead.")
        res_dict['total_count'] = "nan"

    # Progress and return:
    print("\n--Official stats received!--\n")
    return res_dict

def get_secret(secret_name):
    """
    Retrieves a secret from Secret Manager
    to setup database connection later.
    """
    # Get project ID from environment variables
    project_id = os.environ.get('GCP_PROJECT_ID')
    # Setup connection to GCP secret manager
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    # Return secret value
    return response.payload.data.decode("UTF-8")

def write_to_sql(res_dict={}):
    """
    Takes the results-dictionary from a previous scrape
    and writes it to the PostgreSQL database on GCP.
    """
    try:
        conn = psycopg2.connect(
            user=get_secret("SERVICE_ACCOUNT_USER_NAME"),
            # password=get_secret("DATABASE_PASSWORD"), # no PW for service account
            database=get_secret("DATABASE_NAME"),
            host=get_secret("DB_CONNECTION_NAME"),
            port=get_secret("DATABASE_PORT"),
            sslmode='require', # To authenticate with database
        )
        print("Connection succesful!")
        conn.close()
        return None
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None