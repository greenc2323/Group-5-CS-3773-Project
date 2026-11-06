import pytest
from moto import mock_aws
from shop import create_app
from shop.db import setup


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    with mock_aws():
        app = create_app({'TESTING': True, 'SECRET_KEY': 'x' * 40,
                          'TABLE_PREFIX': 'test', 'DYNAMODB_ENDPOINT_URL': None})
        setup(app.extensions['db'], 'test')
        result = app.test_cli_runner().invoke(args=['seed'])
        assert result.exit_code == 0, result.exception
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, path, **data):
    client.get('/')
    with client.session_transaction() as session:
        data['csrf'] = session['csrf']
    return client.post(path, data=data, follow_redirects=True)


def sign_in(client, email='student@example.com'):
    post(client, '/register', name='Student', email=email, password='safe-password-123')
    return post(client, '/login', email=email, password='safe-password-123')
