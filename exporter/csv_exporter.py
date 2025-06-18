from typing import Collection, Any


def export(filename: str, data: list[Any], fieldnames: Collection[Any]) -> None:
    """
    Exports a list of data to a CSV file.

    :param filename: Name of the output CSV file.
    :param data: List of data to export.
    :param fieldnames: Collection of field names for the CSV header.
    """
    import csv

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for dado in data:
            writer.writerow(dado.model_dump())