from flask import Flask
from config import Config
from models import db, Genre, Song, Artist, Playlist
from views.main import main_bp
from views.api import api_bp
import logging
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

def configure_logging(app):
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # Handler для stdout
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Handler для файла
    log_file = app.config['LOG_FILE']  # /app/logs/app.log
    os.makedirs(os.path.dirname(log_file), exist_ok=True)  # Создаём директорию, если её нет
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Очищаем обработчики, чтобы избежать дублирования
    logging.getLogger('').handlers = []  # Очищаем корневой логгер

    # Настраиваем логгер приложения
    app.logger.handlers = []
    app.logger.addHandler(stream_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Настраиваем логгер Werkzeug
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = []
    werkzeug_logger.addHandler(stream_handler)
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.setLevel(logging.INFO)

def load_playlist_images(app):
    folder = app.config['PLAYLIST_IMAGES_FOLDER']
    for image_filename in os.listdir(folder):
        if image_filename.endswith(('.png', '.jpg', '.jpeg')):
            try:
                base_name = image_filename.split('.')[0]
                playlist_id_str = base_name.split('_')[0]
                if playlist_id_str.isdigit():
                    playlist_id = int(playlist_id_str)
                    playlist = Playlist.query.get(playlist_id)
                    if playlist:
                        playlist.image_filename = image_filename
                        db.session.commit()
                        app.logger.info(f"Assigned image '{image_filename}' to playlist ID {playlist_id}.")
                    else:
                        app.logger.info(f"Skipping image '{image_filename}': no playlist with ID {playlist_id} found.")
                else:
                    app.logger.info(f"Skipping image '{image_filename}': not assigned to any playlist.")
            except Exception as e:
                app.logger.warning(f"Error processing image '{image_filename}': {e}")

def load_artist_images(app):
    folder = app.config['ARTIST_IMAGES_FOLDER']
    for image_filename in os.listdir(folder):
        if image_filename.endswith(('.png', '.jpg', '.jpeg')):
            try:
                # Извлекаем ID из имени файла (до точки или подчёркивания)
                base_name = image_filename.split('.')[0]  # Убираем расширение
                artist_id_str = base_name.split('_')[0]  # Берём часть до подчёркивания (или всё, если его нет)
                if artist_id_str.isdigit():
                    artist_id = int(artist_id_str)
                    artist = Artist.query.get(artist_id)
                    if artist:
                        artist.image_filename = image_filename
                        db.session.commit()
                        app.logger.info(f"Assigned image '{image_filename}' to artist ID {artist_id}.")
                    else:
                        app.logger.info(f"Skipping image '{image_filename}': no artist with ID {artist_id} found.")
                else:
                    app.logger.info(f"Skipping image '{image_filename}': not assigned to any artist.")
            except Exception as e:
                app.logger.warning(f"Error processing image '{image_filename}': {e}")

def populate_db_from_audio(app):
    with app.app_context():  # Гарантируем, что контекст активен
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
                            audio = MP3(file_path, ID3=ID3)
                            artist_name = audio.get('TPE1', [filename.split('-')[0]])[0]
                            song_name = audio.get('TIT2', [filename.split('.')[0]])[0]
                        except Exception as e:
                            app.logger.error(f"Ошибка при чтении метаданных из {filename}: {e}")
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

        songs = Song.query.all()
        for song in songs:
            if not song.file_path.startswith('/'):
                song.file_path = f"/{song.file_path}"
                db.session.commit()
                app.logger.info(f"Updated file path for song {song.name}: {song.file_path}")

        artists = Artist.query.all()
        app.logger.info(f"Created artists: {[(artist.id, artist.name) for artist in artists]}")

        db.session.commit()

        if not Playlist.query.first():
            playlist1 = Playlist(name="Лучшее за 2025")
            playlist2 = Playlist(name="Рок-классика")
            playlist3 = Playlist(name="Техно-микс")
            db.session.add_all([playlist1, playlist2, playlist3])
            db.session.commit()

            songs = Song.query.limit(3).all()
            for i, playlist in enumerate([playlist1, playlist2, playlist3]):
                if i < len(songs):
                    playlist.songs.append(songs[i])
            db.session.commit()

        load_artist_images(app)
        load_playlist_images(app)

def create_app():
    app = Flask(__name__,
                template_folder=Config.TEMPLATES_FOLDER,
                static_folder=Config.STATIC_FOLDER)
    app.config.from_object(Config)

    db.init_app(app)

    from prometheus_flask_exporter import PrometheusMetrics
    metrics = PrometheusMetrics(app, path='/metrics')

    configure_logging(app)

    # Инициализация базы данных сразу после создания приложения
    with app.app_context():
        db.create_all()
        app.logger.info("Tables created!")
        populate_db_from_audio(app)

    @app.after_request
    def after_request(response):
        return response

    app.register_blueprint(main_bp, url_prefix='/musicservice')
    app.register_blueprint(api_bp, url_prefix='/musicservice/api')

    return app