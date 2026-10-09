import sys
from pathlib import Path

# Ajouter backend au PYTHONPATH
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
import app.database as app_db
from app.main import app, init_db_data
from app.config import settings

# Base de données de test SQLite en mémoire avec StaticPool
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Remplacer engine et SessionLocal dans app_db
app_db.engine = engine_test
app_db.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    init_db_data(custom_engine=engine_test, custom_session_cls=TestingSessionLocal)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
