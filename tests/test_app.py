import pytest
from cdwhk_homework3.app import app, db, User, LeaveRequest
from datetime import datetime, timedelta


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_register(client):
    """Test user registration."""
    response = client.post(
        "/register",
        data=dict(username="testuser", password="testpassword"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert User.query.filter_by(user_name="testuser").first() is not None


def test_login(client):
    """Test user login."""
    client.post("/register", data=dict(username="testuser", password="testpassword"))
    response = client.post(
        "/login",
        data=dict(username="testuser", password="testpassword"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert session["logged_in"] is True


def test_leave_request_submission(client):
    """Test leave request submission."""
    client.post("/register", data=dict(username="testuser", password="testpassword"))
    client.post("/login", data=dict(username="testuser", password="testpassword"))
    date_start = datetime.today() + timedelta(days=10)
    date_end = datetime.today() + timedelta(days=15)
    response = client.post(
        "/",
        data=dict(
            reason="Vacation",
            date_start=date_start.strftime("%Y-%m-%d"),
            date_end=date_end.strftime("%Y-%m-%d"),
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert LeaveRequest.query.filter_by(reason="Vacation").first() is not None
