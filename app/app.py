from flask import Flask, render_template, send_from_directory, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Загружаем переменные окружения
load_dotenv()

# Пути к папкам для хранения шаблонов и статических файлов
TEMPLATES_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'templates')
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'static')
AUDIO_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'static', 'audio')

# Инициализация приложения Flask
app = Flask(__name__, template_folder=TEMPLATES_FOLDER, static_folder=STATIC_FOLDER, static_url_path='/musicservice/static')

# Конфигурация подключения к PostgreSQL
app.config.update(
    {
        "SQLALCHEMY_DATABASE_URI": "postgresql://postgres:password@db:5432/musicdb",  # Замените на вашу строку подключения
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,  # Отключаем отслеживание изменений для экономии памяти
    }
)

# Инициализация SQLAlchemy
db = SQLAlchemy(app)
from sqlalchemy import create_engine

try:
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    connection = engine.connect()
    print("Connected to the database!")
except Exception as e:
    print(f"Error: {e}")

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
    file_path = db.Column(db.String(255), nullable=False)  # Путь к файлу

# Создание базы данных при первом запуске приложения
@app.before_first_request
def create_tables():
    db.create_all()

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
                        song = Song(name=song_name, file_name=filename, genre_id=genre.id, file_path=file_path)
                        db.session.add(song)

            db.session.commit()  # Сохраняем все изменения в базе данных

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

# Главная страница с жанрами и аудиофайлами
@app.route('/musicservice/')
def index():
    genres = get_audio_files_by_genre()  # Получаем жанры и файлы из базы данных
    return render_template('index.html', genres=genres)

# Эндпоинт для проигрывания аудио
@app.route('/musicservice/audio/<genre>/<filename>')
def get_audio(genre, filename):
    genre_folder = os.path.join(AUDIO_FOLDER, genre)  # Папка с музыкой
    file_path = os.path.join(genre_folder, filename)
    print(f"Serving file: {file_path}")  # Логируем путь к файлу
    return send_from_directory(genre_folder, filename)

# Эндпоинт для получения списка жанров и песен в формате JSON
@app.route('/musicservice/api/genres', methods=['GET'])
def get_genres_api():
    genres = get_audio_files_by_genre()
    return jsonify(genres)

# Запуск приложения
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
