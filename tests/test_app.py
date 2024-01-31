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
    response = client.post(
        "/register",
        data=dict(username="testuser", password="testpassword"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert User.query.filter_by(user_name="testuser").first() is not None


def test_login(client):
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


def test_invalid_login(client):
    response = client.post(
        "/login",
        data=dict(username="wronguser", password="wrongpassword"),
        follow_redirects=True,
    )
    assert b"Invalid username or password" in response.data
    assert response.status_code == 200


def test_logout(client):
    client.post("/register", data=dict(username="testuser", password="testpassword"))
    client.post("/login", data=dict(username="testuser", password="testpassword"))
    response = client.get("/logout", follow_redirects=True)
    with client.session_transaction() as session:
        assert "logged_in" not in session


def test_leave_request_on_weekend(client):
    client.post("/register", data=dict(username="testuser", password="testpassword"))
    client.post("/login", data=dict(username="testuser", password="testpassword"))
    saturday = datetime.today() + timedelta((5 - datetime.today().weekday()) % 7)
    sunday = saturday + timedelta(days=1)
    response = client.post(
        "/",
        data=dict(
            reason="Weekend Getaway",
            date_start=saturday.strftime("%Y-%m-%d"),
            date_end=sunday.strftime("%Y-%m-%d"),
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_delete_leave_request(client):
    client.post("/register", data=dict(username="testuser", password="testpassword"))
    client.post("/login", data=dict(username="testuser", password="testpassword"))
    leave_request = LeaveRequest(
        reason="Doctor Appointment",
        date_start=datetime.today() + timedelta(days=10),
        date_end=datetime.today() + timedelta(days=10),
        user_id=User.query.filter_by(user_name="testuser").first().user_id,
    )
    db.session.add(leave_request)
    db.session.commit()
    leave_request_id = leave_request.id
    response = client.get(f"/delete/{leave_request_id}", follow_redirects=True)
    assert response.status_code == 200
    assert LeaveRequest.query.get(leave_request_id) is None


def test_leave_request_max_days_exceeded(client):
    client.post("/register", data=dict(username="testuser", password="testpassword"))
    client.post("/login", data=dict(username="testuser", password="testpassword"))
    date_start = datetime.today() + timedelta(days=1)
    date_end = datetime.today() + timedelta(days=11)  # This exceeds the 10-day limit
    response = client.post(
        "/",
        data=dict(
            reason="Extended Vacation",
            date_start=date_start.strftime("%Y-%m-%d"),
            date_end=date_end.strftime("%Y-%m-%d"),
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"You cannot request leave for more than 10 days in a year." in response.data
