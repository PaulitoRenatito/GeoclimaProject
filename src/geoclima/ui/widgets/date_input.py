from datetime import date

import customtkinter

from geoclima.ui.validation import DATE_FORMAT, parse_date, parse_optional_date
from geoclima.ui.widgets.calendar_popup import CalendarPopup
from geoclima.ui.widgets.exceptions import InputValidationError
from geoclima.ui.widgets.labeled_input import LabeledInput


class DateInput(LabeledInput):
    """
    A LabeledInput holding a YYYY-MM-DD date: typed directly or picked from a calendar.
    Rules live in geoclima.ui.validation.
    """

    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent, label_text, **kwargs)
        self.calendar_button = customtkinter.CTkButton(self, text="📅", width=32, command=self.open_calendar)
        self.calendar_button.grid(row=0, column=2, padx=(5, 0))
        if self.can_be_empty:
            self.clear_button = customtkinter.CTkButton(
                self, text="✕", width=32, fg_color="gray30", hover_color="gray40", command=lambda: self.set(None)
            )
            self.clear_button.grid(row=0, column=3, padx=(5, 0))

    def validate(self) -> date | None:
        """Returns the date, or None when the field is optional and empty."""
        if self.can_be_empty:
            return parse_optional_date(self.get())
        return parse_date(self.get())

    def set(self, day: date | None) -> None:
        self.entry.delete(0, "end")
        if day is not None:
            self.entry.insert(0, day.strftime(DATE_FORMAT))

    def open_calendar(self) -> CalendarPopup:
        try:
            current = parse_optional_date(self.get())
        except InputValidationError:
            current = None
        return CalendarPopup(self, current, on_select=self.set)
