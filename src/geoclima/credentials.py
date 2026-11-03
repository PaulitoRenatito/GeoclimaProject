"""Stores the INMET token in the OS credential vault (Windows Credential Manager), never in plain text."""

import contextlib
import logging
from types import ModuleType

import keyring
from keyring.errors import KeyringError

logger = logging.getLogger(__name__)

SERVICE_NAME = "Geoclima"
TOKEN_KEY = "inmet-token"


class TokenStore:
    def __init__(self, backend: ModuleType = keyring) -> None:
        self.backend = backend

    def load(self) -> str | None:
        try:
            return self.backend.get_password(SERVICE_NAME, TOKEN_KEY)
        except KeyringError:
            logger.warning("Could not read the token from the credential vault", exc_info=True)
            return None

    def save(self, token: str) -> None:
        try:
            self.backend.set_password(SERVICE_NAME, TOKEN_KEY, token)
        except KeyringError:
            logger.warning("Could not save the token in the credential vault", exc_info=True)

    def clear(self) -> None:
        # Nothing stored, or the vault is unavailable: either way there is nothing to remove.
        with contextlib.suppress(KeyringError):
            self.backend.delete_password(SERVICE_NAME, TOKEN_KEY)
