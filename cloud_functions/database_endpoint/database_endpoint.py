"""
API Endpoint to connect to Cloud SQL database
"""
import os
import warnings
import traceback

# pylint:disable=import-error
import sqlalchemy

# Note! import will cause authentication-attempt with GCP
# pylint:disable=no-name-in-module
from google.cloud import secretmanager
from google.cloud.sql.connector import Connector

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


def init_connection_pool(connector: Connector) -> sqlalchemy.engine.Engine:
    """
    Helper function to return SQLAlchemy connection pool
    """
    def getconn():
        """
        Function used to generate database connection
        """
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
    # Return an sqlalchemy engine
    return pool

def post_to_arbeitsagentur(sql_post_data,db_conn):
    """
    Function to write data to schema "ArbeitsagenturMining"
    """
    # Get separate dict that only contains key-value pairs
    # that get actually written into a table
    items = sql_post_data.copy()
    del items['schema_name']
    del items['table_name']
    del items['timestamp']
    del items['bundesland']
    del items['dict_key']

    for dict_key_val,value in items.items():
        # Say dict_key is "branche", then dict_key_val is
        # a corresponding industry, like "gesundheit_soziales"
        print(f"Updating {sql_post_data['dict_key']}: {dict_key_val}...") 
        insert_stmt = sqlalchemy.text(f"""
            INSERT INTO "{sql_post_data['schema_name']}"."{sql_post_data['table_name']}"
                (timestamp, bundesland, {sql_post_data['dict_key']}, stellen)
                VALUES (:timestamp, :bundesland, :{sql_post_data['dict_key']}, :stellen)
            """)

        db_conn.execute(insert_stmt,
                        parameters={'timestamp':sql_post_data['timestamp'],
                                    'bundesland':sql_post_data['bundesland'],
                                    sql_post_data['dict_key']:dict_key_val,
                                    'stellen':value})

    db_conn.commit()
    print("Database update complete!")

    return


def post_to_db(sql_post_data:dict):
    """
    Takes dictionary and posts to specified table.
    """
    try:
        # Initialize Cloud SQL Python Connector as context manager
        # (removes need to close the connection)
        # This is where GCP tries to authenticate!:
        with Connector(refresh_strategy="lazy") as connector:
            # Initialize connection pool
            pool = init_connection_pool(connector)
            print("Connection to database successful!")

            # Connect to and interact with Cloud SQL database using connection pool
            with pool.connect() as db_conn:
                if sql_post_data['schema_name'] == 'ArbeitsagenturMining':
                    post_to_arbeitsagentur(sql_post_data,db_conn)

                if sql_post_data['schema_name'] == 'AusbildungMining':
                    raise RuntimeError("AusbildungMining is not setup for posting yet!")

    # pylint:disable=broad-exception-caught
    except Exception as e:
        # Get the traceback information
        tb = traceback.extract_tb(e.__traceback__)
        _, line_number, func_name, text = tb[-1]
        warnings.warn(f"""Connection to database failed.
                      Error: {e}
                      Line: {line_number}
                      Function: {func_name}
                      Text: {text}""")
