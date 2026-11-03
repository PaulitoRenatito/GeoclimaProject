import customtkinter


class ProgressFrame(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.progress_bar = customtkinter.CTkProgressBar(self, height=10, corner_radius=4)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.maximum = 100
        self.current = 0

    # Not named `configure`: that would shadow the tkinter/CTk method CustomTkinter calls internally.
    def set_maximum(self, maximum):
        self.maximum = max(maximum, 1)
        self.reset()

    def step(self, amount):
        self.current = min(self.current + amount, self.maximum)
        self.progress_bar.set(self.current / self.maximum)

    def reset(self):
        self.current = 0
        self.progress_bar.set(0)
