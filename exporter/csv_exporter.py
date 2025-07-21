import csv

from exporter.exporter import Exporter


class CSVExporter(Exporter):
    def export(self) -> None:
        """
        Export data to a CSV file with the specified fieldnames.
        """
        filename = self.get_file_name()

        dict_data = [dado.model_dump() for dado in self.data]

        with open(filename, 'w+', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(dict_data)


    def get_file_name(self) -> str:
        """
        Generate a normalized file name based on station name and date range.
        """
        folder_name = 'csv'
        return f"{folder_name}/{self.date.replace('-', '_')}.csv"