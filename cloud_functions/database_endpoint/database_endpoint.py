"""
Blablabla...
"""
import os
import datetime
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
                # Get separate dict that only contains key-value pairs
                # that get actually written into a table
                items = sql_post_data.copy()
                del items['schema_name']
                del items['table_name']

                keys = list(items.keys())

                # Store all column names
                columns = ", ".join(keys)

                # Insert empty string at beginning of keys
                keys.insert(0,'')
                # Join keys together as one string
                values_colon = ", :".join(keys)
                # Remove ", " at the beginning
                values_colon = values_colon[2:]

                # values = ", ".join([str(val) for val in items.values()])

                print("Writing to database...")
                # Insert all values to all columns
                insert_stmt = sqlalchemy.text(f"""
                INSERT INTO "{sql_post_data['schema_name']}".{sql_post_data['table_name']}
                ({columns}) VALUES ({values_colon});
                """)

                db_conn.execute(insert_stmt, parameters=items)

                db_conn.commit()
                print("Database update complete!")

    # # pylint:disable=broad-exception-caught
    except Exception as e:
        # Get the traceback information
        tb = traceback.extract_tb(e.__traceback__)
        _, line_number, func_name, text = tb[-1]
        warnings.warn(f"""Connection to database failed.
                      Error: {e}
                      Line: {line_number}
                      Function: {func_name}
                      Text: {text}""")
