"""
Main function that acts as entry point for Google Cloud Run Functions
"""

# pylint: disable=import-error
import functions_framework

from official_stats import get_official_stats, write_to_sql

@functions_framework.http
def main():
    """
    Entry point for GCP.
    """
    # Get official values as dictionary
    off_stats_dict = get_official_stats()

    # Write results to database
    write_to_sql(off_stats_dict)

    # Initialize empty string and add all results to it
    res_string = ""
    for key,value in off_stats_dict.items():
        res_string += f"{key} : {value}\n"

    # Return results as string
    return res_string, 200
