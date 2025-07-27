import pandas as pd
from .exporter import Exporter


class ExcelExporter(Exporter):
    def export(self) -> None:
        """
        Export weather geoclima-weather to an Excel file.
        """

        if not self.data:
            print("Nenhum dado para exportar.")
            return

        filename = self.get_file_name()

        dict_data = [d.model_dump() for d in self.data]

        df = pd.DataFrame(dict_data)

        colunas_numericas = [
            'TEMP_MIN',
            'TEMP_MAX',
            'TEMP_MED',
            'UMID_MIN',
            'UMID_MED',
            'CHUVA',
            'VEL_VENTO_MED',
        ]
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        mapeamento_colunas = {
            'DC_NOME': 'Nome da Estação',
            'TEMP_MIN': 'Temp. Mínima (°C)',
            'TEMP_MAX': 'Temp. Máxima (°C)',
            'TEMP_MED': 'Temp. Média (°C)',
            'UMID_MIN': 'Umidade Minima (%)',
            'UMID_MED': 'Umidade Média (%)',
            'CHUVA': 'Precipitação (mm)',
            'VEL_VENTO_MED': 'Vento (m/s)',
        }

        df_final = df[mapeamento_colunas.keys()]

        df_final = df_final.rename(columns=mapeamento_colunas)

        df_final.to_excel(filename, index=False, sheet_name=self.date)

        print(f"Sucesso! Dados exportados para a planilha '{filename}'")


    def get_file_name(self) -> str:
        """
        Generate a normalized file name based on station name and date range.
        """
        folder_name = 'excel'
        return f"{folder_name}/{self.date.replace('-', '_')}.xlsx"