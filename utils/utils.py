def get_file_name(date: str) -> str:
    """
    Generate a normalized file name based on station name and date range.
    """
    folder_name = 'csv'
    return f"{folder_name}/{date.replace('-', '_')}.csv"
