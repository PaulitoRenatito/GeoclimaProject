import queue
import threading
import customtkinter
import tkinter as tk
from tkinter import ttk, messagebox

from geoclima_ui.frame.action_frame import ActionFrame
from geoclima_ui.frame.input_frame import InputFrame
from geoclima_ui.frame.log_frame import LogFrame
from geoclima_ui.frame.progress_frame import ProgressFrame
from geoclima_ui.frame.history_frame import HistoryFrame
from geoclima_ui.input.exceptions import InputValidationError
from geoclima_ui.task.get_export_data import get_export_data


class WeatherApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Geoclima - Coletor de Dados Meteorológicos")
        self.geometry("800x600")
        self.minsize(770, 550)

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

        self.comm_queue = queue.Queue()
        self.create_widgets()
        self.after(100, self.process_queue)

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- Seções da UI ---
        # --- Cria o sistema de abas ---
        tab_view = customtkinter.CTkTabview(self, corner_radius=6)
        tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        collector_tab = tab_view.add("Coleta de Dados")
        history_tab = tab_view.add("Histórico")

        # --- Configura o layout das abas ---
        collector_tab.grid_columnconfigure(0, weight=1)
        collector_tab.grid_rowconfigure(3, weight=1)

        history_tab.grid_columnconfigure(0, weight=1)
        history_tab.grid_rowconfigure(0, weight=1)

        # --- Adiciona widgets à aba de Coleta ---
        self.input_frame = InputFrame(collector_tab)
        self.input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.action_frame = ActionFrame(collector_tab, start_command=self.start_task)
        self.action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.progress_frame = ProgressFrame(collector_tab)
        self.progress_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.log_frame = LogFrame(collector_tab)
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(5, 10))

        # --- Adiciona widgets à aba de Histórico ---
        self.history_frame = HistoryFrame(history_tab)
        self.history_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.comm_queue.get_nowait()

                if msg_type == 'log':
                    self.log_frame.log_message(data)
                elif msg_type == 'config_progress':
                    self.progress_frame.configure(data)
                elif msg_type == 'progress_step':
                    self.progress_frame.step(data)
                elif msg_type == 'task_done':
                    self.log_frame.show_success(data)
                    self.history_frame.add_file_entry(data)
                elif msg_type == 'task_error':
                    self.log_frame.show_error(data)
                elif msg_type == 'enable_button':
                    self.action_frame.set_button_state('normal')
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def start_task(self):
        try:
            token, initial_date_str, final_date_str = self.input_frame.get_values()
        except InputValidationError as e:
            messagebox.showwarning("Entrada Inválida", e.message)
            return

        # Reseta a GUI para uma nova execução
        self.action_frame.set_button_state('disabled')
        self.progress_frame.reset()
        self.log_frame.reset()

        if not final_date_str:
            self.log_frame.log_message(f"Iniciando coleta para a data: {initial_date_str}")
        else:
            self.log_frame.log_message(f"Iniciando coleta entre as datas: {initial_date_str} e {final_date_str}")

        # Inicia a thread de trabalho
        threading.Thread(
            target=get_export_data,
            args=(token, self.comm_queue, initial_date_str, final_date_str),
            daemon=True
        ).start()


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()