import customtkinter
import os
from tkinter import messagebox

class HistoryFrame(customtkinter.CTkFrame):
    """
    Um frame que exibe uma lista de arquivos CSV de um diretório
    e permite abri-los.
    """
    def __init__(self, parent, output_dir="output", **kwargs):
        super().__init__(parent, **kwargs)
        self.output_dir = output_dir

        # Garante que o diretório de saída exista
        os.makedirs(self.output_dir, exist_ok=True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title_label = customtkinter.CTkLabel(self, text="Histórico de Downloads")
        title_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.scrollable_frame = customtkinter.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.populate_history()

    def populate_history(self):
        """Lê o diretório de saída e preenche a lista de arquivos."""
        # Limpa entradas antigas
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            files = [f for f in os.listdir(self.output_dir) if f.endswith('.csv')]
            # Ordena os arquivos por data de modificação (mais novos primeiro)
            files.sort(key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)), reverse=True)

            if not files:
                no_files_label = customtkinter.CTkLabel(
                    self.scrollable_frame,
                    text="Nenhum arquivo encontrado.",
                )
                no_files_label.pack(pady=10)
            else:
                for filename in files:
                    self.add_file_entry(os.path.join(self.output_dir, filename), add_at_top=False)
        except FileNotFoundError:
            pass  # O diretório é criado no __init__, então isso não deve ocorrer

    def add_file_entry(self, filepath, add_at_top=True):
        """Adiciona uma nova entrada de arquivo à lista."""
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, customtkinter.CTkLabel):
                widget.destroy()

        filename = os.path.basename(filepath)
        button = customtkinter.CTkButton(
            self.scrollable_frame,
            text=filename,
            anchor="w",
            fg_color="transparent",
            command=lambda p=filepath: self.open_file(p)
        )
        if add_at_top:
            button.pack(
                fill="x",
                padx=5,
                pady=2,
                before=self.scrollable_frame.winfo_children()[0] if self.scrollable_frame.winfo_children() else None
            )
        else:
            button.pack(fill="x", padx=5, pady=2)

    def open_file(self, filepath):
        """Abre o arquivo especificado com o programa padrão do sistema."""
        try:
            os.startfile(filepath)
        except Exception as e:
            messagebox.showerror("Erro ao Abrir", f"Não foi possível abrir o arquivo '{filepath}'.\n\nErro: {e}")