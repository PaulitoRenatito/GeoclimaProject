import unicodedata

def get_file_name(station_name: str, data_inicial: str, data_final: str) -> str:
    """
    Generate a normalized file name based on station name and date range.
    """
    folder_name = 'csv'
    normalized_name = normalize_str(station_name.replace(' ', '_'))
    return f"{folder_name}/{normalized_name}_{data_inicial.replace('-', '_')}_ate_{data_final.replace('-', '_')}.csv"

def normalize_str(string: str) -> str:
    """
    Normalize a string by removing accents and converting to lowercase.
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', string.lower())
        if unicodedata.category(c) != 'Mn'
    )