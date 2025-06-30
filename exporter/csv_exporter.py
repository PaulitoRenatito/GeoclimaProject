from typing import Collection, Any
import csv


def export(filename: str, data: list[Any], fieldnames: Collection[Any]) -> None:
    """
    Exports a list of data to a CSV file.

    :param filename: Name of the output CSV file.
    :param data: List of data to export.
    :param fieldnames: Collection of field names for the CSV header.
    """

    dict_data = [dado.model_dump() for dado in data]

    with open(filename, 'w+', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dict_data)