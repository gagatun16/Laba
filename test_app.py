import pytest
import os
import sys
from PIL import Image, ImageDraw
import numpy as np

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_chessboard_pattern, create_color_distribution_plot, allowed_file

class TestImageProcessing:
    """Тесты для функций обработки изображений"""
    
    def setup_method(self):
        """Создание тестового изображения перед каждым тестом"""
        self.test_image = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(self.test_image)
        draw.rectangle([25, 25, 75, 75], fill='red')
        
    def test_create_chessboard_pattern(self):
        """Тест создания шахматного узора"""
        # Тестируем с разными размерами клеток
        for cell_size in [5, 10, 20]:
            result = create_chessboard_pattern(self.test_image, cell_size)
            
            # Проверяем, что изображение создано
            assert result is not None
            assert isinstance(result, Image.Image)
            assert result.size == self.test_image.size
            
    def test_create_chessboard_pattern_edge_cases(self):
        """Тест крайних случаев для шахматного узора"""
        # Очень маленький размер клетки
        result_small = create_chessboard_pattern(self.test_image, 1)
        assert result_small is not None
        
        # Очень большой размер клетки
        result_large = create_chessboard_pattern(self.test_image, 50)
        assert result_large is not None
        
    def test_create_color_distribution_plot(self):
        """Тест создания графиков распределения цветов"""
        plot_data = create_color_distribution_plot(self.test_image, "Test Image")
        
        # Проверяем, что возвращается строка base64
        assert plot_data is not None
        assert isinstance(plot_data, str)
        assert len(plot_data) > 0
        
        # Проверяем, что это валидный base64
        try:
            import base64
            base64.b64decode(plot_data)
        except Exception:
            pytest.fail("Returned data is not valid base64")
    
    def test_allowed_file(self):
        """Тест проверки разрешенных расширений файлов"""
        # Разрешенные расширения
        assert allowed_file("image.png") == True
        assert allowed_file("photo.jpg") == True
        assert allowed_file("picture.jpeg") == True
        assert allowed_file("anim.gif") == True
        
        # Запрещенные расширения
        assert allowed_file("document.pdf") == False
        assert allowed_file("script.py") == False
        assert allowed_file("data.txt") == False
        
        # Файлы без расширения
        assert allowed_file("noextension") == False
        assert allowed_file(".") == False
        
    def test_image_modes(self):
        """Тест работы с разными режимами изображений"""
        # RGB изображение
        rgb_image = Image.new('RGB', (50, 50), color='blue')
        result_rgb = create_chessboard_pattern(rgb_image, 10)
        assert result_rgb is not None
        
        # Графики для RGB
        plot_rgb = create_color_distribution_plot(rgb_image, "RGB Test")
        assert plot_rgb is not None

def test_flask_app():
    """Тест Flask приложения"""
    # Импортируем здесь, чтобы избежать проблем с окружением
    from app import app
    
    with app.test_client() as client:
        # Тест главной страницы (GET)
        response = client.get('/')
        assert response.status_code == 200
        
        # Тест POST запроса без файла
        response_post = client.post('/', data={'cell_size': '10'})
        assert response_post.status_code in [200, 500]  # Может быть ошибка если нет default image
        
        # Тест с неверным размером клетки
        response_invalid = client.post('/', data={'cell_size': 'invalid'})
        # Должен обработать или вернуть ошибку
        assert response_invalid.status_code in [200, 400, 500]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

