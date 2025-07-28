import customtkinter

class ProgressFrame(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.progress_bar = customtkinter.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.maximum = 100

    def configure(self, maximum):
        self.maximum = maximum
        self.progress_bar.set(0)

    def step(self, amount):
        current_value = self.progress_bar.get()
        new_value = (current_value * self.maximum + amount) / self.maximum
        self.progress_bar.set(min(new_value, 1.0))

    def reset(self):
        self.progress_bar.set(0)