"""
Initial test to later setup API endpoint for database connection
"""
import warnings

# pylint:disable=import-error
from database_endpoint import post_to_db

import functions_framework

def insert_to_db(input_data):
    """
    Insert data into database
    """
    try:
        post_to_db(input_data)
    except Exception as e:
        warnings.warn(f'Connection to database failed. {e}')

# pylint:disable=unused-argument
@functions_framework.http
def main(request):
    """
    Test...
    """
    # Check input
    input_type = request.method
    input_data = request.args.to_dict()

    # Insert data to database
    if input_type == 'POST':
        insert_to_db(input_data)

    # Receive data from database
    if input_type == 'GET':
        print('Input type is GET')

    print('database-endpoint function ran until the end!!')
    return 'Hello, this is a response coming from database-endpoint!',200
