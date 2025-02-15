import functions_framework

@functions_framework.http
def main(request):
    # Import function
    from official_stats import get_official_stats, write_to_sql
    # Get official values as dictionary
    off_stats_dict = get_official_stats()
    
    # Write results to database
    write_to_sql(off_stats_dict)
    
    # Initialize empty string and add all results to it
    res_string = ""
    for key in off_stats_dict.keys():
        res_string += f"{key} : {off_stats_dict[key]}\n"
    # Return results as string
    return res_string, 200
    
    # write_to_sql()
    # return 'Done.', 200