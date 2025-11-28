import pytest
import os
import tempfile
from PIL import Image
import numpy as np

from app import app, create_chessboard_pattern, create_color_distribution_plot

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    
    with app.test_client() as client:
        yield client

def test_index_get(client):
    """Тест GET запроса к главной странице"""
    response = client.get('/')
    assert response.status_code == 200
    # Проверяем наличие ключевых элементов на странице
    assert b'<!DOCTYPE html>' in response.data
    assert b'container' in response.data
    assert b'upload-form' in response.data

def test_chessboard_pattern():
    """Тест создания шахматного узора"""
    # Создаем тестовое изображение
    test_image = Image.new('RGB', (100, 100), color='white')
    processed = create_chessboard_pattern(test_image, 10)
    
    assert processed.size == test_image.size
    assert processed.mode == 'RGB'

def test_chessboard_pattern_different_sizes():
    """Тест создания шахматного узора с разными размерами клеток"""
    test_image = Image.new('RGB', (200, 200), color='white')
    
    # Тестируем разные проценты размера клеток
    for cell_size in [5, 10, 20]:
        processed = create_chessboard_pattern(test_image, cell_size)
        assert processed.size == test_image.size

def test_color_distribution_plot():
    """Тест создания графиков распределения цветов"""
    test_image = Image.new('RGB', (50, 50), color='red')
    plot_data = create_color_distribution_plot(test_image, "Test")
    
    assert isinstance(plot_data, str)
    assert len(plot_data) > 0

def test_color_distribution_plot_grayscale():
    """Тест создания графиков для grayscale изображения"""
    test_image = Image.new('L', (50, 50), color=128)  # Grayscale
    plot_data = create_color_distribution_plot(test_image, "Test Grayscale")
    
    assert isinstance(plot_data, str)
    assert len(plot_data) > 0

def test_allowed_file():
    """Тест проверки разрешенных расширений файлов"""
    from app import allowed_file
    
    assert allowed_file('test.jpg') == True
    assert allowed_file('test.png') == True
    assert allowed_file('test.jpeg') == True
    assert allowed_file('test.gif') == True
    assert allowed_file('test.txt') == False
    assert allowed_file('test') == False
    assert allowed_file('test.JPG') == True  # Проверка регистра
    assert allowed_file('test.PNG') == True

def test_index_post_no_file(client):
    """Тест POST запроса без файла (использует изображение по умолчанию)"""
    response = client.post('/', data={'cell_size': 10})
    assert response.status_code == 200

def test_index_post_with_invalid_file(client):
    """Тест POST запроса с невалидным файлом"""
    response = client.post('/', data={'cell_size': 10}, 
                          content_type='multipart/form-data',
                          data={'image': (b'test content', 'test.txt')})
    assert response.status_code == 200

def test_app_creation():
    """Тест создания Flask приложения"""
    assert app is not None
    assert app.name == 'app'
    assert 'UPLOAD_FOLDER' in app.config

def test_upload_folder_exists():
    """Тест существования папки для загрузок"""
    assert os.path.exists(app.config['UPLOAD_FOLDER'])

def test_image_processing_integration(client):
    """Интеграционный тест обработки изображения"""
    # Создаем тестовое изображение в памяти
    test_image = Image.new('RGB', (100, 100), color='blue')
    test_image_path = 'static/uploads/test_integration.jpg'
    test_image.save(test_image_path)
    
    try:
        # Тестируем обработку
        with open(test_image_path, 'rb') as img:
            response = client.post('/', 
                                 data={'cell_size': 15},
                                 content_type='multipart/form-data',
                                 data={'image': (img, 'test_integration.jpg')})
        
        assert response.status_code == 200
    finally:
        # Удаляем тестовый файл
        if os.path.exists(test_image_path):
            os.remove(test_image_path)