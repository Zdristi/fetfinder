from PIL import Image
import io

def detect_faces_in_image(image_path_or_bytes):
    """
    Проверяет наличие человеческого лица на изображении.
    Использует простой метод, основанный на анализе пропорций и цвета.
    Этот метод не требует сложных библиотек и совместим с Render.
    
    Args:
        image_path_or_bytes: Путь к изображению или байтовый объект изображения
        
    Returns:
        bool: True если обнаружены признаки лица, False в противном случае
    """
    try:
        # Открываем изображение
        if isinstance(image_path_or_bytes, str):
            # Если это путь к файлу
            img = Image.open(image_path_or_bytes)
        else:
            # Если это байтовый объект или файл
            if hasattr(image_path_or_bytes, 'read'):
                # Это объект файла
                img = Image.open(image_path_or_bytes)
                # Возвращаем указатель в начало
                image_path_or_bytes.seek(0)
            elif isinstance(image_path_or_bytes, bytes):
                # Это байтовый объект
                img = Image.open(io.BytesIO(image_path_or_bytes))
            else:
                # Это уже PIL.Image
                img = image_path_or_bytes

        # Преобразуем в RGB, если изображение не в этом формате
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Получаем размеры изображения
        width, height = img.size
        
        # Если изображение слишком маленькое, не проверяем
        if width < 50 or height < 50:
            return False
        
        # Получаем пиксели
        pixels = list(img.getdata())
        
        # Подсчитываем пиксели, соответствующие цвету кожи
        skin_pixels = 0
        total_pixels = len(pixels)
        
        # Определяем диапазон цветов кожи в RGB
        for pixel in pixels:
            if isinstance(pixel, (tuple, list)) and len(pixel) >= 3:
                r, g, b = pixel[0], pixel[1], pixel[2]
                
                # Проверяем, находится ли пиксель в диапазоне, характерном для кожи
                # Это приблизительная проверка кожного тона
                if (r > 95 and g > 40 and b > 20 and 
                    max(r, g, b) - min(r, g, b) > 15 and 
                    abs(r - g) > 15 and r > g and g > b):
                    skin_pixels += 1
        
        # Если доля пикселей кожи в разумных пределах, это может быть лицо
        skin_ratio = skin_pixels / total_pixels if total_pixels > 0 else 0
        
        # Проверим, что изображение не является сплошным цветом
        unique_colors = len(set(pixels))
        
        # Оценка вероятности лица на основе:
        # 1. Наличия кожных тонов
        # 2. Разнообразия цветов
        # 3. Аспектного соотношения изображения (лица обычно близки к квадратным)
        aspect_ratio = width / height if height > 0 else 1
        is_reasonable_aspect = 0.5 <= aspect_ratio <= 2.0
        
        has_skin_tones = skin_ratio > 0.05  # Более 5% пикселей соответствуют тону кожи
        has_color_diversity = unique_colors > 50  # Разнообразие цветов
        
        return has_skin_tones and has_color_diversity and is_reasonable_aspect
    
    except Exception as e:
        print(f"Ошибка при проверке изображения: {e}")
        return False


def validate_avatar_image(image_file):
    """
    Проверяет изображение аватара на наличие признаков лица.
    
    Args:
        image_file: Объект файла изображения из Flask request
        
    Returns:
        dict: {'valid': bool, 'message': str, 'face_count': int}
    """
    try:
        # Проверяем, что файл существует
        if image_file is None or not hasattr(image_file, 'read'):
            return {'valid': False, 'message': 'Файл изображения не предоставлен', 'face_count': 0}
        
        # Проверяем тип файла
        allowed_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
        if not any(image_file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return {'valid': False, 'message': 'Неподдерживаемый формат изображения', 'face_count': 0}
        
        # Проверяем содержимое файла
        image_file.seek(0)  # Перемещаем указатель в начало файла
        image_bytes = image_file.read()
        image_file.seek(0)  # Возвращаем указатель в начало для последующего использования
        
        # Проверяем, что файл не пустой
        if len(image_bytes) == 0:
            return {'valid': False, 'message': 'Файл изображения пуст', 'face_count': 0}
        
        # Проверяем, что файл действительно является изображением
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            pil_image.verify()
        except Exception:
            return {'valid': False, 'message': 'Файл не является корректным изображением', 'face_count': 0}

        # Возвращаем указатель в начало файла для дальнейшей обработки
        image_file.seek(0)
        
        # Проверяем наличие признаков лица
        has_face_like_features = detect_faces_in_image(image_file)
        
        if has_face_like_features:
            return {'valid': True, 'message': 'Изображение прошло проверку', 'face_count': 1}
        else:
            return {'valid': False, 'message': 'Изображение не содержит признаков лица', 'face_count': 0}
    
    except Exception as e:
        print(f"Ошибка при проверке аватара: {e}")
        return {'valid': False, 'message': f'Ошибка при проверке изображения: {str(e)}', 'face_count': 0}