import os
from flask import Flask, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Используем non-interactive backend
import matplotlib.pyplot as plt
import base64
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Проверка разрешенных расширений файлов"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_chessboard_pattern(image, cell_size_percent):
    """
    Создает шахматный узор на изображении
    
    Args:
        image: PIL Image объект
        cell_size_percent: размер клетки в процентах от размера изображения
    
    Returns:
        PIL Image объект с шахматным узором
    """
    # Конвертируем изображение в RGB если нужно
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Преобразуем в numpy array
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # Вычисляем размер клетки в пикселях
    cell_size = int(min(width, height) * cell_size_percent / 100.0)
    if cell_size < 1:
        cell_size = 1
    
    # Создаем шахматный узор
    result_array = img_array.copy()
    
    for y in range(0, height, cell_size):
        for x in range(0, width, cell_size):
            # Определяем, должна ли клетка быть черной (инвертированной)
            cell_y = y // cell_size
            cell_x = x // cell_size
            is_black = (cell_x + cell_y) % 2 == 1
            
            if is_black:
                # Делаем клетку черной
                y_end = min(y + cell_size, height)
                x_end = min(x + cell_size, width)
                result_array[y:y_end, x:x_end] = [0, 0, 0]  # Черный цвет RGB
    
    # Преобразуем обратно в PIL Image
    result_image = Image.fromarray(result_array.astype(np.uint8))
    return result_image

def create_color_distribution_plot(image, title):
    """
    Создает график распределения цветов RGB
    
    Args:
        image: PIL Image объект
        title: заголовок графика
    
    Returns:
        base64 строка с изображением графика
    """
    # Конвертируем в RGB если нужно
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Преобразуем в numpy array
    img_array = np.array(image)
    
    # Получаем каналы RGB
    r_channel = img_array[:, :, 0].flatten()
    g_channel = img_array[:, :, 1].flatten()
    b_channel = img_array[:, :, 2].flatten()
    
    # Создаем гистограммы
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(r_channel, bins=256, color='red', alpha=0.5, label='Red', density=True)
    ax.hist(g_channel, bins=256, color='green', alpha=0.5, label='Green', density=True)
    ax.hist(b_channel, bins=256, color='blue', alpha=0.5, label='Blue', density=True)
    
    ax.set_xlabel('Интенсивность')
    ax.set_ylabel('Плотность')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Сохраняем в base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    plt.close()
    
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return image_base64

@app.route('/')
def index():
    """Главная страница"""
    cell_size = request.args.get('cell_size', 10.0, type=float)
    return render_template('index.html', cell_size=cell_size)

@app.route('/', methods=['POST'])
def upload_file():
    """Обработка загрузки и обработки изображения"""
    cell_size_percent = request.form.get('cell_size', 10.0, type=float)
    
    # Проверяем наличие файла
    if 'image' not in request.files:
        # Используем изображение по умолчанию
        default_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'default.jpg')
        if os.path.exists(default_image_path):
            filename = 'default.jpg'
        else:
            return render_template('index.html', 
                                 error='Нет файла и нет изображения по умолчанию',
                                 cell_size=cell_size_percent)
    else:
        file = request.files['image']
        if file.filename == '':
            # Используем изображение по умолчанию
            default_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'default.jpg')
            if os.path.exists(default_image_path):
                filename = 'default.jpg'
            else:
                return render_template('index.html', 
                                     error='Файл не выбран и нет изображения по умолчанию',
                                     cell_size=cell_size_percent)
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
        else:
            return render_template('index.html', 
                                 error='Недопустимый тип файла',
                                 cell_size=cell_size_percent)
    
    try:
        # Открываем изображение
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image = Image.open(image_path)
        
        # Создаем шахматный узор
        processed_image = create_chessboard_pattern(image, cell_size_percent)
        
        # Сохраняем обработанное изображение
        processed_filename = 'processed.jpg'
        processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        processed_image.save(processed_path)
        
        # Создаем графики распределения цветов
        original_plot = create_color_distribution_plot(image, 'Исходное изображение')
        processed_plot = create_color_distribution_plot(processed_image, 'Обработанное изображение')
        
        # URL для изображений
        original_image_url = url_for('uploaded_file', filename=filename)
        processed_image_url = url_for('uploaded_file', filename=processed_filename)
        
        return render_template('index.html',
                             original_image=original_image_url,
                             processed_image=processed_image_url,
                             original_plot=original_plot,
                             processed_plot=processed_plot,
                             cell_size=cell_size_percent)
    
    except Exception as e:
        return render_template('index.html', 
                             error=f'Ошибка обработки изображения: {str(e)}',
                             cell_size=cell_size_percent)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Отдача загруженных файлов"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Создаем директорию для загрузок если её нет
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
