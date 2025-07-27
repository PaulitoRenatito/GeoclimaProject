from tkinter import ttk

class ActionFrame(ttk.Frame):
    def __init__(self, parent, start_command, **kwargs):
        super().__init__(parent, **kwargs)
        self.start_button = ttk.Button(
            self,
            text="Iniciar Coleta de Dados",
            command=start_command
        )
        self.start_button.pack()

    def set_button_state(self, state):
        """Controla o estado do botão (normal/disabled)."""
        self.start_button.config(state=state)