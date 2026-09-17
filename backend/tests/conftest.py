import os
import tempfile

os.environ["VANGUARD_USE_SQLITE"] = "true"
os.environ["VANGUARD_SQLITE_PATH"] = os.path.join(tempfile.gettempdir(), "vanguard_test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def auth_headers(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "lifter@example.com", "username": "lifter", "password": "Str0ngPass!"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
