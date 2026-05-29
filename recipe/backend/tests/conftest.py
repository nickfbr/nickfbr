import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.rate_limit import parse_rate_limiter


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_engine):
    TestingSession = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Reset the rate limiter between tests.
    parse_rate_limiter.reset()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """A TestClient with a registered user's bearer token attached."""
    resp = client.post(
        "/api/auth/register",
        json={"email": "cook@example.com", "password": "supersecret"},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["accessToken"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
