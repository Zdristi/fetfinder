import face_recognition
from PIL import Image
import io

def detect_faces_in_image(image_path_or_bytes):
    """
    Проверяет наличие человеческого лица на изображении с использованием face_recognition.
    
    Args:
        image_path_or_bytes: Путь к изображению или байтовый объект изображения
        
    Returns:
        bool: True если лицо обнаружено, False в противном случае
    """
    try:
        # Открываем изображение
        if isinstance(image_path_or_bytes, str):
            # Если это путь к файлу
            image = face_recognition.load_image_file(image_path_or_bytes)
        else:
            # Если это байтовый объект или файл
            if hasattr(image_path_or_bytes, 'read'):
                # Это объект файла, сохраняем указатель
                image_bytes = image_path_or_bytes.read()
                image = face_recognition.load_image_file(io.BytesIO(image_bytes))
                # Восстанавливаем указатель в начало
                image_path_or_bytes.seek(0)
            elif isinstance(image_path_or_bytes, bytes):
                # Это байтовый объект
                image = face_recognition.load_image_file(io.BytesIO(image_path_or_bytes))
            else:
                # Это PIL.Image, сохраняем во временный буфер
                buffer = io.BytesIO()
                image_path_or_bytes.save(buffer, format=image_path_or_bytes.format or 'JPEG')
                buffer.seek(0)
                image = face_recognition.load_image_file(buffer)

        # Обнаруживаем лица на изображении
        face_locations = face_recognition.face_locations(image)
        
        # Возвращаем True если обнаружено хотя бы одно лицо
        return len(face_locations) > 0
    
    except Exception as e:
        print(f"Ошибка при обнаружении лиц: {e}")
        return False


def validate_avatar_image(image_file):
    """
    Проверяет изображение аватара на наличие лица.
    
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
        
        # Проверяем наличие лиц
        has_face = detect_faces_in_image(image_file)
        
        # Получаем точное количество лиц
        try:
            # Загружаем изображение и получаем количество лиц
            image_file.seek(0)
            image_bytes = image_file.read()
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            face_locations = face_recognition.face_locations(image)
            face_count = len(face_locations)
            
            # Восстанавливаем указатель в начало для последующего использования
            image_file.seek(0)
        except:
            # Если не получается получить точное количество, устанавливаем 0 или 1
            face_count = 1 if has_face else 0

        if has_face:
            return {'valid': True, 'message': 'Изображение прошло проверку', 'face_count': face_count}
        else:
            return {'valid': False, 'message': f'Не найдено ни одного лица на изображении. Обнаружено объектов: {face_count}', 'face_count': face_count}
    
    except Exception as e:
        print(f"Ошибка при проверке аватара: {e}")
        return {'valid': False, 'message': f'Ошибка при проверке изображения: {str(e)}', 'face_count': 0}