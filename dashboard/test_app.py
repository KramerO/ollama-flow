import pytest
from unittest.mock import patch
from app import app
import requests

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Ollama Flow Dashboard" in response.data

@patch('requests.post')
def test_run_prompt_success(mock_post, client):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'result': 'Test Ollama Response'}

    response = client.post('/run_prompt', data={'prompt': 'Hello Ollama'})
    assert response.status_code == 200
    assert b"Test Ollama Response" in response.data
    mock_post.assert_called_once_with('http://localhost:3000/run', json={'prompt': 'Hello Ollama'})

@patch('requests.post')
def test_run_prompt_connection_error(mock_post, client):
    mock_post.side_effect = requests.exceptions.ConnectionError

    response = client.post('/run_prompt', data={'prompt': 'Hello Ollama'})
    assert response.status_code == 200
    assert b"Error: Could not connect to Ollama Flow server. Is it running?" in response.data

@patch('requests.post')
def test_run_prompt_http_error(mock_post, client):
    mock_post.return_value.status_code = 400
    mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError

    response = client.post('/run_prompt', data={'prompt': 'Hello Ollama'})
    assert response.status_code == 200
    assert b"Error: " in response.data # Generic error message for HTTPError

@patch('requests.post')
def test_configure_architecture_success(mock_post, client):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'message': 'Agent architecture reconfigured successfully'}

    response = client.post('/configure_architecture', json={'architectureType': 'HIERARCHICAL', 'workerCount': 5})
    assert response.status_code == 200
    assert b"Agent architecture reconfigured successfully" in response.data
    mock_post.assert_called_once_with('http://localhost:3000/configure_architecture', json={'architectureType': 'HIERARCHICAL', 'workerCount': 5})

@patch('requests.post')
def test_configure_architecture_backend_error(mock_post, client):
    mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error: Internal Server Error for url: http://localhost:3000/configure_architecture")

    response = client.post('/configure_architecture', json={'architectureType': 'HIERARCHICAL', 'workerCount': 5})
    assert response.status_code == 200 # Flask still returns 200 for template rendering
    assert b"Error reconfiguring architecture: 500 Server Error: Internal Server Error for url: http://localhost:3000/configure_architecture" in response.data

@patch('requests.post')
def test_configure_architecture_missing_params(mock_post, client):
    response = client.post('/configure_architecture', json={'architectureType': 'HIERARCHICAL'})
    assert response.status_code == 400 # Flask should return 400 for missing params
    assert response.json == {'error': 'architectureType and workerCount are required'}

