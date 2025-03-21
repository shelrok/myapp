import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import Config
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
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
    from views.main import main_bp
    from views.api import api_bp
    app.register_blueprint(main_bp, url_prefix='/musicservice')
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
    import os
    from models import Genre, Song, Artist, Playlist

    audio_folder = app.config['AUDIO_FOLDER']
    genres = os.listdir(audio_folder)

    for genre_name in genres:
        genre_path = os.path.join(audio_folder, genre_name)
        if os.path.isdir(genre_path):
            genre = Genre.query.filter_by(name=genre_name).first()
            if not genre:
                genre = Genre(name=genre_name)
                db.session.add(genre)
                db.session.commit()

            for filename in os.listdir(genre_path):
                if filename.endswith(".mp3"):
                    file_path = os.path.join(genre_path, filename)
                    try:
                        # Здесь добавляем работу с mutagen
                        audio = MP3(file_path, ID3=ID3)
                        artist_name = audio.get('TPE1', [filename.split('-')[0]])[0]  # TPE1 - тег для имени артиста
                        song_name = audio.get('TIT2', [filename.split('.')[0]])[0]   # TIT2 - тег для названия песни
                    except Exception as e:
                        app.logger.error(f"Ошибка при чтении метаданных из {filename}: {e}")
                        # Fallback: если метаданные не удалось извлечь, используем имя файла
                        artist_name = filename.split('-')[0] if '-' in filename else filename.split('.')[0]
                        song_name = filename.split('.')[0]

                    artist = Artist.query.filter_by(name=artist_name).first()
                    if not artist:
                        artist = Artist(name=artist_name, genre_id=genre.id)
                        db.session.add(artist)
                        db.session.commit()

                    existing_song = Song.query.filter_by(file_name=filename).first()
                    if not existing_song:
                        song = Song(name=song_name,
                                    file_name=filename,
                                    genre_id=genre.id,
                                    artist_id=artist.id,
                                    file_path=file_path)
                        db.session.add(song)
            db.session.commit()
    if not Playlist.query.first():  # Проверяем, есть ли уже плейлисты
            playlist1 = Playlist(name="Лучшее за 2025")
            playlist2 = Playlist(name="Рок-классика")
            playlist3 = Playlist(name="Техно-микс")
            db.session.add_all([playlist1, playlist2, playlist3])
            db.session.commit()

            # Связываем песни с плейлистами (например, первые 3 песни)
            songs = Song.query.limit(3).all()
            for i, playlist in enumerate([playlist1, playlist2, playlist3]):
                if i < len(songs):
                    playlist.songs.append(songs[i])
            db.session.commit()
    # Загружаем изображения для артистов и плейлистов
    load_artist_images(app)
    load_playlist_images(app)

def load_artist_images(app):
    from models import Artist
    folder = app.config['ARTIST_IMAGES_FOLDER']
    for image_filename in os.listdir(folder):
        if image_filename.endswith(('.png', '.jpg', '.jpeg')):
            try:
                # Проверяем, начинается ли имя файла с числа
                artist_id_str = image_filename.split('_')[0]
                if artist_id_str.isdigit():
                    artist_id = int(artist_id_str)
                    artist = Artist.query.get(artist_id)
                    if artist:
                        artist.image_filename = image_filename
                        db.session.commit()
                else:
                    app.logger.info(f"Skipping image '{image_filename}': not assigned to any artist.")
            except ValueError:
                app.logger.warning(f"Skipping image '{image_filename}': invalid artist ID.")

def load_playlist_images(app):
    from models import Playlist
    folder = app.config['PLAYLIST_IMAGES_FOLDER']
    for image_filename in os.listdir(folder):
        if image_filename.endswith(('.png', '.jpg', '.jpeg')):
            try:
                # Проверяем, является ли имя файла (без расширения) числом
                playlist_id_str = os.path.splitext(image_filename)[0]
                if playlist_id_str.isdigit():
                    playlist_id = int(playlist_id_str)
                    playlist = Playlist.query.get(playlist_id)
                    if playlist:
                        playlist.image_filename = image_filename
                        db.session.commit()
                else:
                    app.logger.info(f"Skipping image '{image_filename}': not assigned to any playlist.")
            except ValueError:
                app.logger.warning(f"Skipping image '{image_filename}': invalid playlist ID.")
