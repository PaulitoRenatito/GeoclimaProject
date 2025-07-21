import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading
import queue
import os
import webbrowser

# Importa a lógica principal e os componentes do seu projeto
from data.application import weather_data_service
from data.domain.weather_data_request import WeatherDataRequest
from exporter.excel_exporter import ExcelExporter
from utils.constants import mg_stations_dict
from config import INTERVALO_ENTRE_REQUISICOES


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Geoclima - Coletor de Dados Meteorológicos v2.0")
        self.root.geometry("750x550")
        self.root.minsize(600, 450)

        # Fila para comunicação segura entre a thread de trabalho e a GUI
        self.comm_queue = queue.Queue()

        self.create_widgets()

        # Inicia o loop para verificar a fila de comunicação
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Seção de Entradas do Usuário ---
        input_frame = ttk.LabelFrame(main_frame, text="1. Insira os Dados", padding="10")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Token INMET:").grid(row=0, column=0, sticky="w", pady=5)
        self.token_entry = ttk.Entry(input_frame, width=60, show="*")
        self.token_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(input_frame, text="Data (AAAA-MM-DD):").grid(row=1, column=0, sticky="w", pady=5)
        self.date_entry = ttk.Entry(input_frame, width=20)
        self.date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.date_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # --- Seção de Ação ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=15)
        self.start_button = ttk.Button(action_frame, text="Iniciar Coleta de Dados", command=self.start_task)
        self.start_button.pack()

        # --- Seção de Progresso ---
        progress_frame = ttk.LabelFrame(main_frame, text="2. Progresso", padding="10")
        progress_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, expand=True)

        # --- Seção de Logs e Resultados ---
        log_frame = ttk.LabelFrame(main_frame, text="3. Status e Resultado", padding="10")
        log_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)  # Faz o frame de log expandir verticalmente

        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD, height=10)
        self.log_area.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.result_label = ttk.Label(log_frame, text="Aguardando resultado...", anchor="w")
        self.result_label.grid(row=1, column=0, sticky="ew")

    def log_message(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_area.config(state='disabled')
        self.log_area.see(tk.END)

    def process_queue(self):
        try:
            while True:  # Processa todas as mensagens na fila
                msg_type, data = self.comm_queue.get_nowait()

                if msg_type == 'log':
                    self.log_message(data)
                elif msg_type == 'config_progress':
                    self.progress_bar.config(maximum=data, value=0)
                elif msg_type == 'progress_step':
                    self.progress_bar.step(data)
                elif msg_type == 'task_done':
                    self.show_success_path(data)
                elif msg_type == 'task_error':
                    messagebox.showerror("Erro na Execução", data)
                    self.result_label.config(text=f"Falha: {data}", foreground="red")
                elif msg_type == 'enable_button':
                    self.start_button.config(state='normal')
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def show_success_path(self, file_path):
        full_path = os.path.abspath(file_path)
        self.result_label.config(text=f"Sucesso! Planilha salva em: {full_path}", foreground="blue", cursor="hand2")
        # A função lambda é usada para passar o argumento 'full_path' para o callback
        self.result_label.bind("<Button-1>", lambda e: webbrowser.open(f"file:///{full_path}"))
        self.log_message("Processo concluído com sucesso!")
        messagebox.showinfo("Concluído", f"A planilha foi gerada com sucesso!\n\nLocal: {full_path}")

    def start_task(self):
        token = self.token_entry.get()
        date_str = self.date_entry.get()

        # Validações
        if not token:
            messagebox.showwarning("Entrada Inválida", "Por favor, insira o token do INMET.")
            return
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showwarning("Entrada Inválida", "Por favor, use o formato de data AAAA-MM-DD.")
            return

        # Reseta a GUI para uma nova execução
        self.start_button.config(state='disabled')
        self.progress_bar['value'] = 0
        self.log_area.config(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.config(state='disabled')
        self.result_label.config(text="Processando...", foreground="black", cursor="")
        self.result_label.unbind("<Button-1>")

        self.log_message(f"Iniciando coleta para a data: {date_str}")

        # Cria e inicia a thread de trabalho para não congelar a interface
        threading.Thread(
            target=self.run_task_logic,
            args=(token, date_str),
            daemon=True
        ).start()

    def run_task_logic(self, token, date_str):
        try:
            requests = [
                WeatherDataRequest(date=date_str, station_code=code)
                for name, code in mg_stations_dict.items()
            ]

            dados_coletados = weather_data_service.get_weather_data_intermittently(
                requests,
                token,
                INTERVALO_ENTRE_REQUISICOES,
                progress_queue=self.comm_queue  # Passa a fila para o serviço
            )

            if dados_coletados:
                self.comm_queue.put(('log', "Coleta finalizada. Exportando para Excel..."))

                if not os.path.exists('excel'):
                    os.makedirs('excel')

                exporter = ExcelExporter(date=date_str, data=dados_coletados)
                exporter.export()
                file_path = exporter.get_file_name()
                self.comm_queue.put(('task_done', file_path))
            else:
                self.comm_queue.put(('task_error', "Nenhum dado foi retornado pela API. Verifique a data."))

        except Exception as e:
            self.comm_queue.put(('task_error', f"Ocorreu um erro crítico: {e}"))
        finally:
            self.comm_queue.put(('enable_button', None))


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()