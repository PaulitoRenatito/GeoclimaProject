import tkinter as tk
from tkinter import ttk

class ProgressFrame(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="2. Progresso", padding="10", **kwargs)
        self.progress_bar = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, expand=True)

    def configure(self, max_value):
        self.progress_bar.config(maximum=max_value, value=0)

    def step(self, amount):
        self.progress_bar.step(amount)

    def reset(self):
        self.progress_bar['value'] = 0