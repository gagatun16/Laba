import pytest
import os
from app import app, allowed_file

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_get(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200

def test_allowed_file():
    """Тест проверки расширений файлов"""
    assert allowed_file('test.jpg') == True
    assert allowed_file('test.png') == True
    assert allowed_file('test.txt') == False

def test_app_creation():
    """Тест создания приложения"""
    assert app is not None