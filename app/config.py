import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Настройки базы данных
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Секретный ключ (если требуется)
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_secret_key')

    # Определяем базовые пути
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')  # Добавляем REDIS_URL
    # Пути к шаблонам и статическим файлам
    TEMPLATES_FOLDER = os.path.join(BACKEND_DIR, 'templates')
    STATIC_FOLDER = os.path.join(BACKEND_DIR, 'static')

    # Пути к подкаталогам со звуком и изображениями
    AUDIO_FOLDER = os.path.join(STATIC_FOLDER, 'audio')
    ARTIST_IMAGES_FOLDER = os.path.join(STATIC_FOLDER, 'artists')
    PLAYLIST_IMAGES_FOLDER = os.path.join(STATIC_FOLDER, 'playlists')

    # Путь для логов
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
