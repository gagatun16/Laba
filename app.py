from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import os

app = Flask(__name__)

# Конфигурация
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DEFAULT_IMAGE = 'default.jpg'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_chessboard_pattern(image, cell_size_percent):
    """Создает шахматный узор на изображении"""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Размер клетки в пикселях
    cell_size = int(min(width, height) * (cell_size_percent / 100))
    
    # Создаем шахматный узор
    for y in range(0, height, cell_size):
        for x in range(0, width, cell_size):
            # Определяем цвет клетки (черный или белый)
            if (x // cell_size + y // cell_size) % 2 == 0:
                # Черная клетка
                draw.rectangle([x, y, x + cell_size, y + cell_size], fill='black')
    
    return img

def create_color_distribution_plot(image, title):
    """Создает график распределения цветов"""
    # Конвертируем изображение в numpy array
    img_array = np.array(image)
    
    # Создаем график
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Распределение цветов по каналам
    colors = ['red', 'green', 'blue']
    color_names = ['Red', 'Green', 'Blue']
    
    for i, color in enumerate(colors):
        if len(img_array.shape) == 3:  # RGB изображение
            channel_data = img_array[:, :, i].flatten()
        else:  # Grayscale
            channel_data = img_array.flatten()
        
        ax1.hist(channel_data, bins=50, alpha=0.7, color=color, label=color_names[i])
    
    ax1.set_title(f'{title} - Color Distribution')
    ax1.set_xlabel('Color Value')
    ax1.set_ylabel('Frequency')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Средние значения цветов
    if len(img_array.shape) == 3:
        avg_colors = [np.mean(img_array[:, :, i]) for i in range(3)]
        ax2.bar(color_names, avg_colors, color=colors, alpha=0.7)
        ax2.set_ylim(0, 255)
    else:
        avg_color = np.mean(img_array)
        ax2.bar(['Gray'], [avg_color], color='gray', alpha=0.7)
        ax2.set_ylim(0, 255)
    
    ax2.set_title(f'{title} - Average Colors')
    ax2.set_ylabel('Average Value')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Конвертируем график в base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    original_image_path = None
    processed_image = None
    original_plot = None
    processed_plot = None
    cell_size = 10  # значение по умолчанию
    
    # Путь к изображению по умолчанию
    default_image_path = os.path.join(app.config['UPLOAD_FOLDER'], DEFAULT_IMAGE)
    
    if request.method == 'POST':
        # Получаем размер клетки от пользователя
        cell_size = float(request.form.get('cell_size', 10))
        
        # Проверяем, загрузил ли пользователь новое изображение
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = DEFAULT_IMAGE
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                original_image_path = filepath
            else:
                original_image_path = default_image_path
        else:
            original_image_path = default_image_path
        
        # Обрабатываем изображение
        try:
            with Image.open(original_image_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Создаем шахматный узор
                processed_image = create_chessboard_pattern(img, cell_size)
                
                # Создаем графики распределения цветов
                original_plot = create_color_distribution_plot(img, "Original Image")
                processed_plot = create_color_distribution_plot(processed_image, "Processed Image")
                
                # Сохраняем обработанное изображение
                processed_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed.jpg')
                processed_image.save(processed_path)
                
        except Exception as e:
            return f"Error processing image: {str(e)}"
    
    else:
        # GET запрос - используем изображение по умолчанию
        original_image_path = default_image_path
    
    return render_template('index.html',
                         original_image=original_image_path,
                         processed_image='static/uploads/processed.jpg' if processed_image else None,
                         original_plot=original_plot,
                         processed_plot=processed_plot,
                         cell_size=cell_size)

if __name__ == '__main__':
    # Создаем папку для загрузок если её нет
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)