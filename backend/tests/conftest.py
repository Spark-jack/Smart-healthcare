import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing app
os.environ["SECRET_KEY"] = "super-secret-test-key-which-is-at-least-32-chars-long-for-security"
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./test_healthcare.db"

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.core.security import get_password_hash

TEST_DB_FILE = "./test_healthcare.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_healthcare.db"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create all tables in test database
    Base.metadata.create_all(bind=test_engine)
    yield
    # Teardown
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def create_user(db_session):
    def _create_user(email: str, password: str, full_name: str, role: UserRole, is_active: bool = True):
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=is_active
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user
