from collections.abc import Callable
from datetime import date, timedelta

import customtkinter
from tkcalendar import Calendar

# Dark palette matching the customtkinter "dark" + "blue" theme.
CALENDAR_STYLE = {
    "background": "#2B2B2B",
    "foreground": "#DCE4EE",
    "headersbackground": "#333333",
    "headersforeground": "#DCE4EE",
    "normalbackground": "#3A3A3A",
    "normalforeground": "#DCE4EE",
    "weekendbackground": "#343638",
    "weekendforeground": "#DCE4EE",
    "othermonthbackground": "#2B2B2B",
    "othermonthforeground": "#777777",
    "othermonthwebackground": "#2B2B2B",
    "othermonthweforeground": "#777777",
    "selectbackground": "#1F6AA5",
    "selectforeground": "#FFFFFF",
    "disabledbackground": "#2B2B2B",
    "disabledforeground": "#555555",
    # Future days (after maxdate) use these, not the "disabled*" options above.
    "disableddaybackground": "#2B2B2B",
    "disableddayforeground": "#5A5A5A",
    "bordercolor": "#2B2B2B",
}


class CalendarPopup(customtkinter.CTkToplevel):
    """Modal month calendar. Only past days can be picked: INMET has no complete data for today."""

    def __init__(self, parent, initial: date | None, on_select: Callable[[date], None]):
        super().__init__(parent)
        self.on_select = on_select
        self.title("Escolha a data")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())

        yesterday = date.today() - timedelta(days=1)
        self.calendar = Calendar(
            self,
            selectmode="day",
            locale="pt_BR",
            date_pattern="yyyy-mm-dd",
            maxdate=yesterday,
            showweeknumbers=False,
            font=("", 11),
            **CALENDAR_STYLE,
        )
        self.calendar.selection_set(initial if initial and initial <= yesterday else yesterday)
        self.calendar.pack(padx=10, pady=10)
        self.calendar.bind("<<CalendarSelected>>", lambda _: self.select(self.calendar.selection_get()))

        self.after(10, self.grab_set)  # grab only once the window is visible, or Tk raises on Windows

    def select(self, day: date) -> None:
        self.on_select(day)
        self.destroy()
