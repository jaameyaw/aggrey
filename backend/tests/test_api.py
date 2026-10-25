import json
import logging

import pytest
from fastapi.testclient import TestClient

import aggrey
from aggrey.logging import JsonFormatter


def test_health_returns_status_and_version_only(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": aggrey.__version__}


def test_each_request_gets_its_own_request_id(client: TestClient) -> None:
    first = client.get("/health").headers["X-Request-ID"]
    second = client.get("/health").headers["X-Request-ID"]

    assert len(first) == 32
    assert first != second


def test_sendblue_webhook_is_a_stub(client: TestClient) -> None:
    response = client.post("/webhooks/sendblue", json={"content": "What's for dinner?"})

    assert response.status_code == 501


def test_api_docs_are_not_exposed(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_access_log_has_request_fields_and_no_body(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="aggrey.request"):
        response = client.post("/webhooks/sendblue", json={"from_number": "+15555550123"})

    [record] = [r for r in caplog.records if r.name == "aggrey.request"]
    line = json.loads(JsonFormatter().format(record))
    assert line["request_id"] == response.headers["X-Request-ID"]
    assert line["method"] == "POST"
    assert line["path"] == "/webhooks/sendblue"
    assert line["status"] == 501
    assert "+15555550123" not in json.dumps(line)


def test_formatter_drops_fields_not_on_the_allow_list() -> None:
    record = logging.LogRecord("aggrey.test", logging.INFO, __file__, 1, "hello", None, None)
    record.intent = "menu_lookup"
    record.phone = "+15555550123"

    line = json.loads(JsonFormatter().format(record))

    assert line["msg"] == "hello"
    assert line["intent"] == "menu_lookup"
    assert "phone" not in line
