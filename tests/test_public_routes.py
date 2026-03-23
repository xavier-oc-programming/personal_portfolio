"""
tests/test_public_routes.py

Tests for all public-facing routes.
"""


def test_home_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200


def test_projects_listing_returns_200(client):
    response = client.get('/projects')
    assert response.status_code == 200


def test_project_detail_returns_200(client, seeded_db):
    response = client.get('/projects/test-project')
    assert response.status_code == 200


def test_nonexistent_project_returns_404(client):
    response = client.get('/projects/does-not-exist')
    assert response.status_code == 404


def test_about_returns_200(client):
    response = client.get('/about')
    assert response.status_code == 200


def test_contact_returns_200(client):
    response = client.get('/contact')
    assert response.status_code == 200


def test_api_docs_returns_200(client):
    response = client.get('/api')
    assert response.status_code == 200
