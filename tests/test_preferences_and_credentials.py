import json

import pytest

from geoclima.credentials import SERVICE_NAME, TOKEN_KEY, TokenStore
from geoclima.exporter.service import ExportFormat, ExportMode
from geoclima.preferences import Preferences
from geoclima.ui.progress import format_eta
from tests.conftest import FakeKeyring


def test_token_store_round_trip():
    backend = FakeKeyring()
    store = TokenStore(backend)

    store.save("secret")
    assert backend.passwords == {(SERVICE_NAME, TOKEN_KEY): "secret"}
    assert store.load() == "secret"

    store.clear()
    assert store.load() is None
    store.clear()  # clearing twice is harmless


def test_token_store_survives_an_unavailable_vault():
    store = TokenStore(FakeKeyring(fail=True))

    store.save("secret")
    assert store.load() is None


def test_preferences_default_when_missing(tmp_path):
    prefs = Preferences.load(tmp_path / "missing.json")

    assert (prefs.state, prefs.format, prefs.mode, prefs.remember_token) == (
        "MG",
        ExportFormat.CSV,
        ExportMode.PER_DAY,
        False,
    )


def test_preferences_round_trip(tmp_path):
    path = tmp_path / "nested" / "preferences.json"

    Preferences(state="BA", export_format="EXCEL", export_mode="SINGLE_FILE", remember_token=True).save(path)
    prefs = Preferences.load(path)

    assert (prefs.state, prefs.format, prefs.mode, prefs.remember_token) == (
        "BA",
        ExportFormat.EXCEL,
        ExportMode.SINGLE_FILE,
        True,
    )
    assert "token" not in json.loads(path.read_text()).get("state", "")


@pytest.mark.parametrize("content", ["not json", "[1, 2]", '{"export_format": "PDF", "unknown": 1}'])
def test_broken_or_unknown_preferences_fall_back_to_defaults(tmp_path, content):
    path = tmp_path / "preferences.json"
    path.write_text(content)

    prefs = Preferences.load(path)

    assert prefs.format is ExportFormat.CSV


@pytest.mark.parametrize(
    ("seconds", "text"),
    [(0, "~0 s restantes"), (44.6, "~45 s restantes"), (60, "~1 min 00 s restantes"), (125, "~2 min 05 s restantes")],
)
def test_format_eta(seconds, text):
    assert format_eta(seconds) == text
