"""
tests/test_api.py

Tests for all public REST API endpoints.

Covers response status codes, envelope shape, and data correctness.
"""

import json


def test_api_projects_returns_200(client, seeded_db):
    response = client.get('/api/v1/projects')
    assert response.status_code == 200


def test_api_projects_envelope_shape(client, seeded_db):
    response = client.get('/api/v1/projects')
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data
    assert 'count' in data
    assert isinstance(data['data'], list)


def test_api_projects_count_matches_data(client, seeded_db):
    response = client.get('/api/v1/projects')
    data = json.loads(response.data)
    assert data['count'] == len(data['data'])


def test_api_single_project_returns_200(client, seeded_db):
    response = client.get('/api/v1/projects/test-project')
    assert response.status_code == 200


def test_api_single_project_returns_correct_slug(client, seeded_db):
    response = client.get('/api/v1/projects/test-project')
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['data']['slug'] == 'test-project'


def test_api_nonexistent_project_returns_404(client):
    response = client.get('/api/v1/projects/does-not-exist')
    assert response.status_code == 404


def test_api_404_returns_json_not_html(client):
    response = client.get('/api/v1/projects/does-not-exist')
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data


def test_api_featured_filter(client, seeded_db):
    response = client.get('/api/v1/projects?featured=true')
    data = json.loads(response.data)
    assert data['success'] is True
    assert all(p['featured'] for p in data['data'])


def test_api_category_filter(client, seeded_db):
    response = client.get('/api/v1/projects?category=web')
    data = json.loads(response.data)
    assert data['success'] is True
    assert all(p['category'] == 'web' for p in data['data'])


def test_api_categories_returns_200(client):
    response = client.get('/api/v1/categories')
    assert response.status_code == 200


def test_api_categories_envelope_shape(client):
    response = client.get('/api/v1/categories')
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data
    assert 'count' in data


def test_api_tags_returns_200(client):
    response = client.get('/api/v1/tags')
    assert response.status_code == 200


def test_api_tags_envelope_shape(client):
    response = client.get('/api/v1/tags')
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data
    assert 'count' in data
