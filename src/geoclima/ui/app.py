import queue
import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter

from geoclima.settings import OUTPUT_DIR
from geoclima.ui.frames.action_frame import ActionFrame
from geoclima.ui.frames.history_frame import HistoryFrame
from geoclima.ui.frames.input_frame import InputFrame
from geoclima.ui.frames.log_frame import LogFrame
from geoclima.ui.frames.progress_frame import ProgressFrame
from geoclima.ui.messages import MessageType, WorkerMessage
from geoclima.ui.widgets.exceptions import InputValidationError
from geoclima.ui.worker import run_collection

QUEUE_POLL_MS = 100


class WeatherApp(customtkinter.CTk):
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        super().__init__()
        self.output_dir = output_dir

        self.title("Geoclima - Coletor de Dados Meteorológicos")
        self.geometry("800x600")
        self.minsize(770, 550)

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

        # Tk widgets are not thread-safe: the worker only enqueues messages,
        # and the main loop applies them in process_queue.
        self.comm_queue: queue.Queue[WorkerMessage] = queue.Queue()
        self.create_widgets()
        self.after(QUEUE_POLL_MS, self.process_queue)

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        tab_view = customtkinter.CTkTabview(self, corner_radius=6)
        tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        collector_tab = tab_view.add("Coleta de Dados")
        history_tab = tab_view.add("Histórico")

        collector_tab.grid_columnconfigure(0, weight=1)
        collector_tab.grid_rowconfigure(3, weight=1)

        history_tab.grid_columnconfigure(0, weight=1)
        history_tab.grid_rowconfigure(0, weight=1)

        self.input_frame = InputFrame(collector_tab)
        self.input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.action_frame = ActionFrame(collector_tab, start_command=self.start_task)
        self.action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.progress_frame = ProgressFrame(collector_tab)
        self.progress_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.log_frame = LogFrame(collector_tab)
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self.history_frame = HistoryFrame(history_tab, output_dir=self.output_dir)
        self.history_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def process_queue(self):
        try:
            while True:
                self.handle_message(self.comm_queue.get_nowait())
        except queue.Empty:
            pass
        finally:
            self.after(QUEUE_POLL_MS, self.process_queue)

    def handle_message(self, message: WorkerMessage):
        match message.type:
            case MessageType.LOG:
                self.log_frame.log_message(message.payload)
            case MessageType.PROGRESS_START:
                self.progress_frame.set_maximum(message.payload)
            case MessageType.PROGRESS_STEP:
                self.progress_frame.step(message.payload)
            case MessageType.TASK_DONE:
                self.log_frame.show_success(message.payload)
                self.history_frame.populate_history()
            case MessageType.TASK_ERROR:
                self.log_frame.show_error(message.payload)
            case MessageType.TASK_FINISHED:
                self.action_frame.set_button_state("normal")

    def start_task(self):
        try:
            token, initial_date, final_date = self.input_frame.get_values()
        except InputValidationError as e:
            messagebox.showwarning("Entrada Inválida", e.message)
            return

        self.action_frame.set_button_state("disabled")
        self.progress_frame.reset()
        self.log_frame.reset()

        if final_date is None:
            self.log_frame.log_message(f"Iniciando coleta para a data: {initial_date}")
        else:
            self.log_frame.log_message(f"Iniciando coleta entre as datas: {initial_date} e {final_date}")

        threading.Thread(
            target=run_collection,
            args=(token, self.comm_queue, initial_date, final_date, self.output_dir),
            daemon=True,
        ).start()
