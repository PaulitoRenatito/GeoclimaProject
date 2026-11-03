"""Messages sent from the worker thread to the Tk main loop through a queue."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class MessageType(Enum):
    LOG = auto()
    PROGRESS_START = auto()  # payload: total number of steps
    PROGRESS_STEP = auto()  # payload: number of steps done
    TASK_DONE = auto()  # payload: success message
    TASK_ERROR = auto()  # payload: error message
    TASK_FINISHED = auto()  # always sent last, success or not


@dataclass(frozen=True)
class WorkerMessage:
    type: MessageType
    payload: Any = None
