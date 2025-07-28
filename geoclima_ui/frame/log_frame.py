import customtkinter


class LogFrame(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.log_text = customtkinter.CTkTextbox(self, state="disabled", wrap="word", font=("", 18))
        self.log_text.grid(row=0, column=0, sticky="nsew")

        self.log_text.tag_config("success", foreground="lightgreen")
        self.log_text.tag_config("error", foreground="#FF5555")

    def _log(self, message, tags=None):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n", tags)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def log_message(self, message):
        self._log(f"INFO: {message}")

    def show_success(self, message):
        self._log(f"SUCESSO: {message}", "success")

    def show_error(self, message):
        self._log(f"ERRO: {message}", "error")

    def reset(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")