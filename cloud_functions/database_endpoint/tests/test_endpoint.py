"""
Test.
"""
import sys
import os
import datetime
from unittest.mock import patch, Mock

import pytest

from sqlalchemy import MetaData, Table, insert, update

# Get parent directory to import modules to test
curdir = os.path.dirname(__file__)
sys.path.append(os.path.dirname(curdir))

# pylint:disable=wrong-import-position
from database_endpoint import post_to_db

def test_post_to_db(mocker):
    """
    Tests the for-loop part of post_to_db.
    """
    # Mock the connect engine
    mock_pool = Mock(name='MockPool')
    mock_pool.connect.return_value.__enter__ = mock_pool
    mock_pool.connect.return_value.__enter__.return_value.execute.return_value = None
    mock_pool.connect.return_value.__exit__ = mock_pool

    # Mock the connection pool
    mocker.patch('database_endpoint.init_connection_pool', return_value=mock_pool)

    # Mock MetaData and Table
    mock_table = Mock()
    mock_table.insert.result_value = 42
    mocker.patch('database_endpoint.Table', return_value=mock_table)

    # Mock insert function
    mock_insert = Mock()
    mock_insert.values.return_value = datetime.datetime.now()
    mocker.patch('database_endpoint.insert', return_value=mock_insert)

    # Mock update function
    mock_update = Mock()
    def return_input(value):
        return value
    # Make the insert statement return the value from the input dictionary
    mock_update.where.return_value.values.side_effect = return_input
    mocker.patch('database_endpoint.update', return_value=mock_update)

    # 5. Prepare test data
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

    # 6. Call the function
    post_to_db(test_data)

    # Check that the execution is called the correct number of times
    assert (mock_pool
            .connect
            .return_value
            .__enter__
            .return_value
            .execute
            # Call count should be 1 (cur. date) + number of entries in test_data
            # minus the two first keys that are skipped
            .call_count) == 1+len(test_data)-2
