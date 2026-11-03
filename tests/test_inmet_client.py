import json
from datetime import date

import pytest
import requests
import responses

from geoclima.weather.infrastructure import inmet_client
from geoclima.weather.infrastructure.exceptions import StationDataError

TOKEN = "SECRET-TOKEN"
DAY = date(2025, 8, 28)
URL = inmet_client.build_daily_url(DAY, DAY, "A565", TOKEN)


def fetch():
    return inmet_client.fetch_daily_data(DAY, DAY, "A565", TOKEN)


def test_builds_daily_url():
    url = inmet_client.build_daily_url(DAY, date(2025, 8, 30), "A565", TOKEN)

    assert url == f"https://apitempo.inmet.gov.br/token/estacao/diaria/2025-08-28/2025-08-30/A565/{TOKEN}"


@responses.activate
def test_returns_parsed_records(raw_record):
    responses.get(URL, body=json.dumps([raw_record]))

    records = fetch()

    assert [r.station_name for r in records] == ["BAMBUI"]


@responses.activate
@pytest.mark.parametrize(("status", "body"), [(204, ""), (200, ""), (200, "  ")])
def test_no_content_means_no_data(status, body):
    responses.get(URL, status=status, body=body)

    assert fetch() == []


@responses.activate
def test_http_error_raises_without_leaking_token():
    responses.get(URL, status=401, body=f"invalid token {TOKEN}")

    with pytest.raises(StationDataError) as exc_info:
        fetch()

    assert "HTTP 401" in str(exc_info.value)
    assert TOKEN not in str(exc_info.value)


@responses.activate
def test_connection_error_raises_without_leaking_token():
    # requests embeds the full URL (and so the token) in connection error messages.
    responses.get(URL, body=requests.ConnectionError(f"Max retries exceeded with url: {URL}"))

    with pytest.raises(StationDataError) as exc_info:
        fetch()

    assert TOKEN not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__


@responses.activate
def test_retries_transient_server_errors(raw_record):
    responses.get(URL, status=503)
    responses.get(URL, body=json.dumps([raw_record]))

    assert len(fetch()) == 1
    assert len(responses.calls) == 2


def test_requests_use_a_timeout(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        response = requests.Response()
        response.status_code = 204
        return response

    monkeypatch.setattr(inmet_client._session, "get", fake_get)
    fetch()

    assert captured["timeout"] == inmet_client.REQUEST_TIMEOUT
