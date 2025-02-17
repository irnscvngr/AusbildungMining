"""
Test.
"""
import sys
import os
from unittest.mock import patch, Mock

import pytest

# Get parent directory to import modules to test
curdir = os.path.dirname(__file__)
sys.path.append(os.path.dirname(curdir))

from official_stats import get_official_stats

expected_keys = ['company_count',
                     'integrated_degree_programs',
                     'educational_trainings',
                     'qualifications',
                     'regular_apprenticeships',
                     'inhouse_trainings',
                     'educational_trainings_and_regular_apprenticeships',
                     'training_programs',
                     'total_count']

# Replace actual scraping result with mockup
@patch("official_stats.requests.get")
 # Because of mockup, this test will return lots of warnings. Surpress them:
@pytest.mark.filterwarnings("ignore::UserWarning")
def testscrape_response_200(mockup_request):
    """
    Execute scrape-function with mockup response to check if
    results-dictionary is returned correctly.
    """
    # Mock the successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"<html><title>Test Title</title></html>"  # Example HTML
    mockup_request.return_value = mock_response

    # Execute scraper
    scrape_result = get_official_stats()

    # Check if expected keys are generated
    assert list(scrape_result.keys()) == expected_keys

# Replace actual scraping result with mockup
@patch("official_stats.requests.get")
 # Because of mockup, this test will return lots of warnings. Surpress them:
@pytest.mark.filterwarnings("ignore::UserWarning")
def testscrape_response_404(mockup_request):
    """
    Execute scrape-function with mockup response to check if
    results-dictionary is returned correctly.
    """
    # Mock the successful response
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.content = b"<html><title>Test Title</title></html>"  # Example HTML
    mockup_request.return_value = mock_response

    # Execute scraper
    scrape_result = get_official_stats()

    # Check if expected keys are generated
    assert list(scrape_result.keys()) == expected_keys
    # Go through dict and check if all values are empty strings
    for _,value in scrape_result.items():
        assert value == ''
