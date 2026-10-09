import pytest
from fastapi.testclient import TestClient
from app import config, database, service
from app.main import app

@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path, output_dir = tmp_path / "test.db", tmp_path / "certificates"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(config, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(service, "OUTPUT_DIR", output_dir)
    with TestClient(app) as test_client:
        yield test_client
