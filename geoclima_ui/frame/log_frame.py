import os
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk, scrolledtext, messagebox


class LogFrame(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="3. Status e Resultado", padding="10", **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.log_area = scrolledtext.ScrolledText(self, state='disabled', wrap=tk.WORD, height=10)
        self.log_area.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.result_label = ttk.Label(self, text="Aguardando resultado...", anchor="w")
        self.result_label.grid(row=1, column=0, sticky="ew")

    def log_message(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_area.config(state='disabled')
        self.log_area.see(tk.END)

    def show_success(self, file_path):
        full_path = os.path.abspath(file_path)
        self.result_label.config(text=f"Sucesso! Planilha salva em: {full_path}", foreground="blue", cursor="hand2")
        self.result_label.bind("<Button-1>", lambda e: webbrowser.open(f"file:///{full_path}"))
        self.log_message("Processo concluído com sucesso!")
        messagebox.showinfo("Concluído", f"A planilha foi gerada com sucesso!\n\nLocal: {full_path}")

    def show_error(self, error_message):
        messagebox.showerror("Erro na Execução", error_message)
        self.result_label.config(text=f"Falha: {error_message}", foreground="red")

    def reset(self):
        self.log_area.config(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.config(state='disabled')
        self.result_label.config(text="Processando...", foreground="black", cursor="")
        self.result_label.unbind("<Button-1>")