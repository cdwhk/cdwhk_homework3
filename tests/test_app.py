import pytest
from cdwhk_homework3.app import app, db, User


@pytest.fixture(scope="module")
def test_client():
    # Konfigurieren Sie die Flask-Test-App
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False  # Deaktivieren Sie CSRF für die Tests

    # Erstellen Sie die SQLite In-Memory-Datenbank
    with app.app_context():
        db.create_all()
        # Hier könnten Sie Testdaten einfügen
        test_user = User(user_name="testuser", password="testpassword")
        db.session.add(test_user)
        db.session.commit()

    # Erstellen Sie einen Test-Client
    testing_client = app.test_client()

    # Kontextbereich, innerhalb dessen der Test-Client verwendet werden kann
    with app.app_context():
        yield testing_client  # Dies ist, wo die Tests passieren!

    # Aufräumen / Teardown
    with app.app_context():
        db.drop_all()


def test_home_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get("/")
    assert (
        response.status_code == 302
    )  # Erwarten Sie eine Umleitung auf /login, wenn kein Benutzer eingeloggt ist


def test_login_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/login' page is posted to (POST)
    THEN check the response is valid
    """
    response = test_client.post(
        "/login",
        data=dict(username="testuser", password="testpassword"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password" not in response.data
