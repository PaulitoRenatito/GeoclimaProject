import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from geoclima_ui.frame.action_frame import ActionFrame
from geoclima_ui.frame.input_frame import InputFrame
from geoclima_ui.frame.log_frame import LogFrame
from geoclima_ui.frame.progress_frame import ProgressFrame
from geoclima_ui.input.exceptions import InputValidationError
from geoclima_ui.task.get_export_data import get_export_data


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Geoclima - Coletor de Dados Meteorológicos")
        photo = tk.PhotoImage(file="res/geoclima_only_icon.png")
        root.iconphoto(False, photo)
        self.root.geometry("770x550")
        self.root.minsize(770, 550)

        # Fila para comunicação segura entre a thread de trabalho e a GUI
        self.comm_queue = queue.Queue()

        self.create_widgets()

        # Inicia o loop para verificar a fila de comunicação
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)

        # --- Seções da UI ---
        self.input_frame = InputFrame(main_frame)
        self.input_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=5,
            pady=5,
        )

        self.action_frame = ActionFrame(main_frame, start_command=self.start_task)
        self.action_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=5,
            pady=15,
        )

        self.progress_frame = ProgressFrame(main_frame)
        self.progress_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=5,
            pady=5,
        )

        self.log_frame = LogFrame(main_frame)
        self.log_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=5,
            pady=5,
        )

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
                elif msg_type == 'task_error':
                    self.log_frame.show_error(data)
                elif msg_type == 'enable_button':
                    self.action_frame.set_button_state('normal')
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

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
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()