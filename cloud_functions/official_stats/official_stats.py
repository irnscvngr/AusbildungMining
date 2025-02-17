"""
This file connects to Ausbildung.de and get's "official" numbers of companies
and vacancies. Ausbildung.de list 7 types of vacancies, as well as the total count.
This make 9 values to return in total.
The keys are:
- company_count
- integrated_degree_programs
- educational_trainings
- qualifications
- regular_apprenticeships
- inhouse_trainings
- educational_trainings_and_regular_apprenticeships
- training_progams
- total_count
"""
import warnings
import re
import os
import datetime

# Note! import will cause authentication-attempt with GCP
# pylint:disable=no-name-in-module
from google.cloud import secretmanager
# pylint:disable=import-error
from google.cloud.sql.connector import Connector

import requests
from bs4 import BeautifulSoup
import sqlalchemy

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
    response = requests.get(url,timeout=20)
    print(response.content)
    soup = BeautifulSoup(response.content,'html.parser')
    try:
        print("Processing: company_count")
        # Company count can be found in static HTML
        cl = soup.find(class_="corporations-listing")
        company_count = cl.find(class_="blob").text
        # The result is of format "5.258 Unternehmen"
        # ->Extract digits and remove dot
        company_count = ''.join(re.findall(r'\d+',company_count))
    # pylint:disable=broad-exception-caught
    except Exception as e:
        # In case of failure just store nan
        print(f"Failed to get company count. Storing empty string instead. Error: {e}")
        company_count = ""

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
            response = requests.get(url, params=params,timeout=20)
            soup = BeautifulSoup(response.content,'html.parser')
            # Extract count-element
            res = soup.find(class_="title title--size-md title--left").text
            # Extract actual number
            res = re.search(r"\d+",res)[0]
            # Store value to results dictionary
            res_dict[key_clean] = res
            # Reset API parameter
            params[key] = 0
        # pylint:disable=broad-exception-caught
        except Exception as e:
            # In case of failure just store nan
            warnings.warn(f"API call failed for {key_clean}! Storing empty string instead. {e}")
            res_dict[key_clean] = ""

    # Set all API parameters to 1 so that the search returns a total count
    for key in list(params.keys())[3:]:
        params[key] = 1
    # Perform API call for overall vacancy count
    try:
        print("Processing: total_count")
        # Perform API call
        response = requests.get(url, params=params, timeout=20)
        soup = BeautifulSoup(response.content,'html.parser')
        # Extract count-element
        res = soup.find(class_="title title--size-md title--left").text
        # Extract actual number
        res = re.search(r"\d+",res)[0]
        # Store value to results dictionary
        res_dict['total_count'] = res
    # pylint:disable=broad-exception-caught
    except Exception as e:
        # In case of failure just store nan
        warnings.warn(f"Failed to get total count. Storing empty string instead. Error: {e}")
        res_dict['total_count'] = ""

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
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": name})
    # Return secret value
    return response.payload.data.decode("UTF-8")

def write_to_sql(res_dict):
    """
    Writes scraping results to Cloud SQL using google.cloud.sql.connectors.
    """
    # helper function to return SQLAlchemy connection pool
    def init_connection_pool(connector: Connector) -> sqlalchemy.engine.Engine:
        # function used to generate database connection
        def getconn():
            instance_connection_name = get_secret("DB_CONNECTION_NAME")
            db_user = get_secret("SERVICE_ACCOUNT_USER_NAME")
            db_name = get_secret("DATABASE_NAME")

            conn = connector.connect(
                instance_connection_name,
                "pg8000",
                user=db_user,
                db=db_name,
                enable_iam_auth=True, # important! enables IAM authentication
            )
            return conn

        # create connection pool
        pool = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn, # only pass the function, don't call it!
        )
        return pool

    try:
        # initialize Cloud SQL Python Connector as context manager
        # (removes need to close the connection)
        with Connector(refresh_strategy="lazy") as connector:
            # Initialize connection pool
            pool = init_connection_pool(connector)
            print("Connection to database successful!")

            # interact with Cloud SQL database using connection pool
            with pool.connect() as db_conn:
                # Take current time as timestamp
                current_date = datetime.datetime.now()

                # 1. Insert the date (parameterized)
                print("Adding current date...")
                # pylint:disable=line-too-long
                insert_stmt = sqlalchemy.text("""INSERT INTO "AusbildungMining".official_stats (date) VALUES (:date)""")
                db_conn.execute(insert_stmt, parameters={"date":current_date})

                # 2. Update other columns (parameterized)
                for key, value in res_dict.items():  # Iterate through official stats
                    print(f"Updating value for {key}...")

                    insert_stmt = sqlalchemy.text(f"""UPDATE "AusbildungMining".official_stats SET {key} = (:value) WHERE date = (:date)""")
                    db_conn.execute(insert_stmt, parameters={'value':value, 'date':current_date})
                    # Commit statements
                    db_conn.commit()

                print("Database update complete!")
    # pylint:disable=broad-exception-caught
    except Exception as e:
        warnings.warn(f"Connection to database failed. {e}")
