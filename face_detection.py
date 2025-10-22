import cv2
import numpy as np
from PIL import Image
import io

def detect_faces_in_image(image_path_or_bytes, min_face_size=(30, 30), face_cascade_path=None):
    """
    Проверяет наличие человеческого лица на изображении.
    
    Args:
        image_path_or_bytes: Путь к изображению или байтовый объект изображения
        min_face_size: Минимальный размер лица для обнаружения (ширина, высота)
        face_cascade_path: Путь к каскаду Хаара (если не указан, используется стандартный)
        
    Returns:
        bool: True если лицо обнаружено, False в противном случае
    """
    try:
        # Загружаем каскад Хаара для обнаружения лиц
        if face_cascade_path is None:
            # Используем встроенный каскад Хаара для обнаружения лиц
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        else:
            face_cascade = cv2.CascadeClassifier(face_cascade_path)

        # Открываем изображение
        if isinstance(image_path_or_bytes, str):
            # Если это путь к файлу
            image = cv2.imread(image_path_or_bytes)
        else:
            # Если это байтовый объект (например, из Flask request)
            if isinstance(image_path_or_bytes, bytes):
                image_array = np.frombuffer(image_path_or_bytes, dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            elif isinstance(image_path_or_bytes, (bytes, io.IOBase)):
                # Если это поток байтов
                pil_image = Image.open(image_path_or_bytes)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            else:
                # Если это уже PIL Image
                image = cv2.cvtColor(np.array(image_path_or_bytes), cv2.COLOR_RGB2BGR)

        if image is None:
            return False

        # Преобразуем в оттенки серого для лучшего обнаружения лиц
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Обнаруживаем лица
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=min_face_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Возвращаем True если обнаружено хотя бы одно лицо
        return len(faces) > 0
    
    except Exception as e:
        print(f"Ошибка при обнаружении лиц: {e}")
        return False


def validate_avatar_image(image_file, min_face_size=(30, 30)):
    """
    Проверяет изображение аватара на наличие лица.
    
    Args:
        image_file: Объект файла изображения из Flask request
        min_face_size: Минимальный размер лица для обнаружения (ширина, высота)
        
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
        has_face = detect_faces_in_image(io.BytesIO(image_bytes), min_face_size)
        
        # Проверяем изображение снова, чтобы получить количество лиц
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=min_face_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        face_count = len(faces)
        
        if has_face:
            return {'valid': True, 'message': 'Изображение прошло проверку', 'face_count': face_count}
        else:
            return {'valid': False, 'message': f'Не найдено ни одного лица на изображении. Обнаружено объектов: {face_count}', 'face_count': face_count}
    
    except Exception as e:
        print(f"Ошибка при проверке аватара: {e}")
        return {'valid': False, 'message': f'Ошибка при проверке изображения: {str(e)}', 'face_count': 0}