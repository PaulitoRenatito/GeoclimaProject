import os
import pandas as pd
from .exporter import Exporter


class CsvExporter(Exporter):
    """
    Exporta dados para um arquivo CSV.
    """

    def export(self) -> None:
        """
        Exporta os dados meteorológicos para um arquivo CSV.
        """
        if not self.data:
            print("Nenhum dado para exportar.")
            return

        filename = self.get_file_name()
        folder_name = os.path.dirname(filename)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

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

        colunas_existentes = [col for col in mapeamento_colunas.keys() if col in df.columns]
        df_final = df[colunas_existentes]

        df_final = df_final.rename(columns=mapeamento_colunas)

        df_final.to_csv(filename, index=False, sep=';', encoding='utf-8-sig')

        print(f"Sucesso! Dados exportados para o arquivo CSV '{filename}'")

    def get_file_name(self) -> str:
        """
        Gera um nome de arquivo normalizado com base na data.
        """
        if not os.path.exists('csv'):
            os.makedirs('csv')

        folder_name = 'csv'
        return f"{folder_name}/{self.date.replace('-', '_')}.csv"