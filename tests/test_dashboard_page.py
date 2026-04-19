import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL no configurado — se omiten tests de integración",
)


def test_dashboard_page_renders():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Dashboard de comparacion" in response.text


def test_dashboard_page_serves_comparison_assets():
    client = TestClient(create_app())

    response = client.get("/")

    assert "styles.css" in response.text
    assert "comparison.css" in response.text
    assert "comparison.js" in response.text
