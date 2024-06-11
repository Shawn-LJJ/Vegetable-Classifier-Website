import pytest
from application import create_app, db
from application.models import User

@pytest.fixture
def client():
    test_app = create_app('TEST')   # get the app with the testing configuration
    # get both the app context as well as the test client
    with test_app.app_context(), test_app.test_client() as client:

        # add a test user account into the user model
        test_user = User(
            email = 'test@test.com',
            password = 'Test12345$'
        )
        db.session.add(test_user)
        db.session.commit()

        yield client

# we need a fixture that has an authenticated user
@pytest.fixture
def authenticated_client(client):
    # test user credential
    data = {
        'email' : 'test@test.com',
        'password' : 'Test12345$'
    }
    client.post('/signin', data=data, follow_redirects=True)    # enable redirect as we first go back to home page
    return client