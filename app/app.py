from flask import Flask, render_template, send_from_directory, jsonify, redirect, url_for, request
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from prometheus_flask_exporter import PrometheusMetrics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
TEMPLATES_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'templates')
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'static')
AUDIO_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'static', 'audio')

# Инициализация приложения Flask
app = Flask(__name__, template_folder=TEMPLATES_FOLDER, static_folder=STATIC_FOLDER, static_url_path='/musicservice/static')
metrics = PrometheusMetrics(app)
app.config['STATIC_FOLDER'] = STATIC_FOLDER  # Убедитесь, что добавляете STATIC_FOLDER в конфигурацию
ARTIST_IMAGES_FOLDER = os.path.join(app.config['STATIC_FOLDER'], 'artists')
PLAYLIST_IMAGES_FOLDER = os.path.join(app.config['STATIC_FOLDER'], 'playlists')

# Конфигурация подключения к PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL  # Используем строку подключения из .env
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключаем отслеживание изменений для экономии памяти

# Инициализация SQLAlchemy
db = SQLAlchemy(app)

try:
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    connection = engine.connect()
    print("Connected to the database!")
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Модели базы данных для жанров и песен
class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    songs = db.relationship('Song', backref='genre', lazy=True)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(100), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)  # Добавлен внешний ключ для артиста
    file_path = db.Column(db.String(255), nullable=False)  # Путь к файлу

    # Добавляем отношение к таблице Artist
    artist = db.relationship('Artist', backref=db.backref('songs_list', lazy=True))


class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)
    genre = db.relationship('Genre', backref=db.backref('artists', lazy=True))
    image_filename = db.Column(db.String(100), nullable=True)  # Добавлено поле для изображения


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)  # Описание плейлиста
    image_filename = db.Column(db.String(100), nullable=True)  # Изображение плейлиста
    songs = db.relationship('Song', secondary='playlist_song', backref='playlists', lazy='dynamic')

# Связующая таблица для плейлистов и песен (многие ко многим)
class PlaylistSong(db.Model):
    __tablename__ = 'playlist_song'
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True)

# Создание базы данных при первом запуске приложения
@app.before_first_request
def create_tables():
    db.create_all()
    logger.info("Tables created!")

# Функция для добавления жанров и песен из папок
def populate_db_from_audio():
    genres = os.listdir(AUDIO_FOLDER)  # Список всех жанров (папок)
    
    for genre_name in genres:
        genre_path = os.path.join(AUDIO_FOLDER, genre_name)
        if os.path.isdir(genre_path):
            # Проверяем, есть ли уже такой жанр в базе данных
            genre = Genre.query.filter_by(name=genre_name).first()
            if not genre:
                genre = Genre(name=genre_name)
                db.session.add(genre)
                db.session.commit()

            # Добавляем песни из этой папки в базу данных
            for filename in os.listdir(genre_path):
                if filename.endswith(".mp3"):  # Только MP3 файлы
                    song_name = filename.split('.')[0]  # Убираем расширение
                    file_path = os.path.join(genre_path, filename)

                    # Проверяем, существует ли такая песня уже
                    existing_song = Song.query.filter_by(file_name=filename).first()
                    if not existing_song:
                        # Проверяем наличие артиста
                        artist_name = song_name.split('-')[0]  # Пример логики извлечения имени артиста из названия
                        artist = Artist.query.filter_by(name=artist_name).first()
                        if not artist:
                            # Если артист не найден, создаем его
                            artist = Artist(name=artist_name, genre_id=genre.id)
                            db.session.add(artist)
                            db.session.commit()
                        
                        # Теперь создаем песню, связываем её с жанром и артистом
                        song = Song(name=song_name, file_name=filename, genre_id=genre.id, artist_id=artist.id, file_path=file_path)
                        db.session.add(song)

            db.session.commit()  # Сохраняем все изменения в базе данных
    
    # Загружаем изображения для артистов и плейлистов
    load_artist_images()
    load_playlist_images()

def load_artist_images():
    # Получаем список всех изображений в папке с изображениями артистов
    for image_filename in os.listdir(ARTIST_IMAGES_FOLDER):
        if image_filename.endswith(('.png', '.jpg', '.jpeg')):  # Обрабатываем только изображения
            try:
                # Попытка получить ID артиста из имени файла
                artist_id_str = image_filename.split('_')[0]  # Получаем часть имени до _
                
                # Проверяем, что это действительно число
                artist_id = int(artist_id_str)
                
                artist = Artist.query.get(artist_id)
                if artist:
                    artist.image_filename = f"artists/{image_filename}"
                    db.session.commit()
            except ValueError:
                # Обработка случая, когда ID не является числом (например, если это изображение без _ в имени)
                print(f"Warning: Skipping image '{image_filename}' because the artist ID is invalid.")

# Функция для загрузки изображений плейлистов
def load_playlist_images():
    # Получаем список всех изображений в папке с изображениями плейлистов
    for image_filename in os.listdir(PLAYLIST_IMAGES_FOLDER):
        if image_filename.endswith(('.png', '.jpg', '.jpeg')):  # Обрабатываем только изображения
            try:
                # Убираем расширение файла
                image_name_without_extension = os.path.splitext(image_filename)[0]
                
                # Пробуем извлечь ID из имени файла
                playlist_id = int(image_name_without_extension)
                
                playlist = Playlist.query.get(playlist_id)
                if playlist:
                    playlist.image_filename = f"playlists/{image_filename}"
                    db.session.commit()
            except ValueError:
                # Обработка случая, когда ID не является числом
                print(f"Warning: Skipping image '{image_filename}' because the playlist ID is invalid.")

@app.before_first_request
def populate_database():
    # Заполняем базу данных с музыкальными файлами
    populate_db_from_audio()
    print("Database populated with genres and songs from audio folders.")

# Получение всех жанров и песен из базы данных
def get_audio_files_by_genre():
    genres = {}
    genres_in_db = Genre.query.all()  # Получаем все жанры из базы данных PostgreSQL
    for genre in genres_in_db:
        # Получаем файлы для каждого жанра из таблицы Song
        audio_files = [song.file_name for song in genre.songs]
        genres[genre.name] = audio_files
    return genres

@app.route('/musicservice/')
def index():
    genres = get_audio_files_by_genre()  # Ваши жанры
    artists = Artist.query.all()  # Все артисты из базы данных
    playlists = Playlist.query.all()  # Все плейлисты из базы данных
    return render_template('index.html', genres=genres, artists=artists, playlists=playlists)

# Получение всех артистов из базы данных
@app.route('/musicservice/api/artists', methods=['GET'])
def get_artists_api():
    artists = Artist.query.all()
    artists_data = [
        {'id': artist.id, 'name': artist.name, 'bio': artist.bio, 'image': artist.image_filename}
        for artist in artists
    ]
    return jsonify(artists_data)

# Получение информации об артисте по id
@app.route('/musicservice/api/artist/<int:artist_id>', methods=['GET'])
def get_artist_api(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    artist_data = {
        'id': artist.id,
        'name': artist.name,
        'bio': artist.bio,
        'image': artist.image_filename
    }
    return jsonify(artist_data)

@app.route('/musicservice/api/playlists', methods=['GET'])
def get_playlists_api():
    playlists = Playlist.query.all()
    playlists_data = [
        {'id': playlist.id, 'name': playlist.name, 'description': playlist.description, 'image': playlist.image_filename}
        for playlist in playlists
    ]
    return jsonify(playlists_data)

# Получение плейлиста по id
@app.route('/musicservice/api/playlist/<int:playlist_id>', methods=['GET'])
def get_playlist_api(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    playlist_data = {
        'id': playlist.id,
        'name': playlist.name,
        'description': playlist.description,
        'image': playlist.image_filename,
        'songs': [song.file_name for song in playlist.songs]
    }
    return jsonify(playlist_data)

# Эндпоинт для загрузки изображения артиста
@app.route('/musicservice/upload/artist_image/<int:artist_id>', methods=['POST'])
def upload_artist_image(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    image_file = request.files['image']
    image_filename = f"{artist_id}_{image_file.filename}"
    
    if not os.path.exists(ARTIST_IMAGES_FOLDER):
        os.makedirs(ARTIST_IMAGES_FOLDER)

    image_path = os.path.join(app.config['STATIC_FOLDER'], 'artists', image_filename)
    image_file.save(image_path)
    artist.image_filename = f"artists/{image_filename}"
    db.session.commit()
    return jsonify({"message": "Image uploaded successfully", "image_path": artist.image_filename})

# Эндпоинт для загрузки изображения плейлиста
@app.route('/musicservice/upload/playlist_image/<int:playlist_id>', methods=['POST'])
def upload_playlist_image(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    image_file = request.files['image']
    image_filename = f"{playlist_id}_{image_file.filename}"
    
    if not os.path.exists(PLAYLIST_IMAGES_FOLDER):
        os.makedirs(PLAYLIST_IMAGES_FOLDER)

    image_path = os.path.join(app.config['STATIC_FOLDER'], 'playlists', image_filename)
    image_file.save(image_path)
    playlist.image_filename = f"playlists/{image_filename}"
    db.session.commit()
    return jsonify({"message": "Image uploaded successfully", "image_path": playlist.image_filename})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
