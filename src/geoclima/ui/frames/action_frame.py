import customtkinter

START_TEXT = "Iniciar Coleta de Dados"
CANCEL_TEXT = "Cancelar Coleta"


class ActionFrame(customtkinter.CTkFrame):
    """One button that starts a collection, then turns into "cancel" while it runs."""

    def __init__(self, parent, start_command, cancel_command, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.start_command = start_command
        self.cancel_command = cancel_command
        self.running = False

        self.grid_columnconfigure(0, weight=1)

        self.start_button = customtkinter.CTkButton(self, text=START_TEXT, command=self.on_click, height=40)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.default_colors = (self.start_button.cget("fg_color"), self.start_button.cget("hover_color"))

    def on_click(self) -> None:
        if self.running:
            self.start_button.configure(state="disabled", text="Cancelando...")
            self.cancel_command()
        else:
            self.start_command()

    def set_running(self, running: bool) -> None:
        self.running = running
        if running:
            self.start_button.configure(text=CANCEL_TEXT, fg_color="#A33A3A", hover_color="#7F2D2D", state="normal")
        else:
            fg_color, hover_color = self.default_colors
            self.start_button.configure(text=START_TEXT, fg_color=fg_color, hover_color=hover_color, state="normal")
