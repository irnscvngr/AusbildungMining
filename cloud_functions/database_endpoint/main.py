"""
Initial test to later setup API endpoint for database connection
"""
# pylint:disable=import-error
from database_endpoint import post_to_db

import functions_framework

# pylint:disable=unused-argument
@functions_framework.http
def main(request):
    """
    Test...
    """
    test_data = {
        "schema_name":"AusbildungMining",
        "table_name":"mock_official_stats",
        "company_count": "5533",
        "integrated_degree_programs": "26540",
        "educational_trainings": "7238",
        "qualifications": "6735",
        "regular_apprenticeships": "104718",
        "inhouse_trainings": "899",
        "educational_trainings_and_regular_apprenticeships": "4298",
        "training_programs": "9785",
        "total_count": "150047"
        }
    post_to_db(test_data)
    
    print('database-endpoint function ran until the end!!')
    return 'Hello, this is a response coming from database-endpoint!',200
