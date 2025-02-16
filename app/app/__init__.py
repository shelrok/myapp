import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Инициализация SQLAlchemy
db = SQLAlchemy()

def create_app():
    # Создаем экземпляр приложения с указанием путей к шаблонам и статике из конфига
    app = Flask(__name__,
                template_folder=Config.TEMPLATES_FOLDER,
                static_folder=Config.STATIC_FOLDER)
    app.config.from_object(Config)

    # Инициализация расширений
    db.init_app(app)
    
    # Создаем и инициализируем PrometheusMetrics с передачей app
    from prometheus_flask_exporter import PrometheusMetrics
    metrics = PrometheusMetrics(app, path='/metrics')
    
    # Настройка логирования
    configure_logging(app)

    # Регистрируем функцию создания таблиц и первичное заполнение базы данных
    @app.before_first_request
    def initialize_database():
        with app.app_context():
            db.create_all()
            app.logger.info("Tables created!")
            populate_db_from_audio(app)

    # Пример обработчика после каждого запроса (для подсчета запросов, метрик и т.п.)
    @app.after_request
    def after_request(response):
        # Можно добавить счетчики или другие действия после запроса
        return response

    # Импорт и регистрация Blueprints (если они разделены по функциональности)
    from app.views.main import main_bp
    from app.views.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/musicservice/api')

    return app

def configure_logging(app):
    """Настраивает логирование с использованием RotatingFileHandler."""
    log_file = app.config.get('LOG_FILE')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

def populate_db_from_audio(app):
    """
    Заполняет базу данных информацией из аудиофайлов,
    а также загружает изображения для артистов и плейлистов.
    """
    import os
    from app.models import Genre, Song, Artist, Playlist

    audio_folder = app.config['AUDIO_FOLDER']
    genres = os.listdir(audio_folder)  # Список всех жанров (папок)

    for genre_name in genres:
        genre_path = os.path.join(audio_folder, genre_name)
        if os.path.isdir(genre_path):
            # Проверяем, есть ли такой жанр в базе
            genre = Genre.query.filter_by(name=genre_name).first()
            if not genre:
                genre = Genre(name=genre_name)
                db.session.add(genre)
                db.session.commit()

            # Добавляем песни из папки жанра
            for filename in os.listdir(genre_path):
                if filename.endswith(".mp3"):
                    song_name = filename.split('.')[0]
                    file_path = os.path.join(genre_path, filename)
                    existing_song = Song.query.filter_by(file_name=filename).first()
                    if not existing_song:
                        # Извлекаем имя артиста (например, часть до дефиса)
                        artist_name = song_name.split('-')[0]
                        artist = Artist.query.filter_by(name=artist_name).first()
                        if not artist:
                            artist = Artist(name=artist_name, genre_id=genre.id)
                            db.session.add(artist)
                            db.session.commit()

                        song = Song(name=song_name,
                                    file_name=filename,
                                    genre_id=genre.id,
                                    artist_id=artist.id,
                                    file_path=file_path)
                        db.session.add(song)
            db.session.commit()

    # Загружаем изображения для артистов и плейлистов
    load_artist_images(app)
    load_playlist_images(app)

def load_artist_images(app):
    """Загружает изображения артистов из папки ARTIST_IMAGES_FOLDER."""
    from app.models import Artist
    folder = app.config['ARTIST_IMAGES_FOLDER']
    for image_filename in os.listdir(folder):
        if image_filename.endswith(('.png', '.jpg', '.jpeg')):
            try:
                artist_id_str = image_filename.split('_')[0]
                artist_id = int(artist_id_str)
                artist = Artist.query.get(artist_id)
                if artist:
                    artist.image_filename = os.path.join('artists', image_filename)
                    db.session.commit()
            except ValueError:
                app.logger.warning(f"Warning: Skipping image '{image_filename}' because the artist ID is invalid.")

def load_playlist_images(app):
    """Загружает изображения плейлистов из папки PLAYLIST_IMAGES_FOLDER."""
    from app.models import Playlist
    folder = app.config['PLAYLIST_IMAGES_FOLDER']
    for image_filename in os.listdir(folder):
        if image_filename.endswith(('.png', '.jpg', '.jpeg')):
            try:
                image_name_without_ext = os.path.splitext(image_filename)[0]
                playlist_id = int(image_name_without_ext)
                playlist = Playlist.query.get(playlist_id)
                if playlist:
                    playlist.image_filename = os.path.join('playlists', image_filename)
                    db.session.commit()
            except ValueError:
                app.logger.warning(f"Warning: Skipping image '{image_filename}' because the playlist ID is invalid.")
