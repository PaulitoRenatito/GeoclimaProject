from dados.domain.dados import Dados


def export(data: list[Dados], filename: str) -> None:
    """
    Exports a list of Dados objects to a CSV file.

    :param data: List of Dados objects to export.
    :param filename: Name of the output CSV file.
    """
    import csv

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=Dados.model_fields.keys())
        writer.writeheader()
        for dado in data:
            writer.writerow(dado.model_dump())