import customtkinter

class ActionFrame(customtkinter.CTkFrame):
    def __init__(self, parent, start_command, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)

        self.start_button = customtkinter.CTkButton(
            self,
            text="Iniciar Coleta de Dados",
            command=start_command,
            height=40,
        )
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    def set_button_state(self, state):
        """Controla o estado do botão (normal/disabled)."""
        self.start_button.configure(state=state)