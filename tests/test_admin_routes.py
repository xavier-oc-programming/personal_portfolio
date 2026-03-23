"""
tests/test_admin_routes.py

Tests for admin authentication and protected routes.
"""


def test_admin_dashboard_redirects_when_logged_out(client):
    response = client.get('/admin/')
    assert response.status_code == 302
    assert '/admin/login' in response.headers['Location']


def test_admin_login_page_returns_200(client):
    response = client.get('/admin/login')
    assert response.status_code == 200


def test_admin_login_with_correct_password(client):
    response = client.post('/admin/login', data={'password': 'test-password'})
    assert response.status_code == 302


def test_admin_login_with_wrong_password(client):
    response = client.post('/admin/login', data={'password': 'wrong-password'})
    assert response.status_code == 200


def test_admin_projects_list_requires_auth(client):
    response = client.get('/admin/projects')
    assert response.status_code == 302
    assert '/admin/login' in response.headers['Location']


def test_admin_messages_requires_auth(client):
    response = client.get('/admin/messages')
    assert response.status_code == 302
    assert '/admin/login' in response.headers['Location']
