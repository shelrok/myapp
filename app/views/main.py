from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import Genre, Artist, Playlist, Song
import os
from werkzeug.utils import secure_filename
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from __init__ import db 
main_bp = Blueprint('main', __name__, template_folder='templates')

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ

def get_audio_files_by_genre():
    """Возвращает словарь жанров и соответствующих файлов песен."""
    genres = {}
    genres_in_db = Genre.query.all()
    for genre in genres_in_db:
        audio_files = [song.file_name for song in genre.songs]
        genres[genre.name] = audio_files
    return genres

@main_bp.route('/')
def index():
    genres = get_audio_files_by_genre()
    artists = Artist.query.all()
    playlists = Playlist.query.all()
    return render_template('index.html', genres=genres, artists=artists, playlists=playlists)
    
@main_bp.route('/albums')
def albums_page():
    artists = Artist.query.all()
    return render_template('albums.html', artists=artists)

@main_bp.route('/playlists')
def playlists_page():
    playlists = Playlist.query.all()
    return render_template('playlists.html', playlists=playlists)

@main_bp.route('/genres')
def genres_page():
    genres = Genre.query.all()
    return render_template('genres.html', genres=genres)

@main_bp.route('/artists')
def artists_page():
    artists = Artist.query.all()
    return render_template('artists.html', artists=artists)

@main_bp.route('/artist/<int:artist_id>')
def artist_page(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    songs = Song.query.filter_by(artist_id=artist_id).all()
    return render_template('artist.html', artist=artist, songs=songs)

@main_bp.route('/songs')
def songs_page():
    songs = Song.query.all()
    return render_template('songs.html', songs=songs)

def get_unique_filename(base_path, filename):
    """Возвращает уникальное имя файла, добавляя суффикс, если файл уже существует."""
    if not os.path.exists(os.path.join(base_path, filename)):
        return filename

    base_name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = f"{base_name}_{counter}{ext}"
        if not os.path.exists(os.path.join(base_path, new_filename)):
            return new_filename
        counter += 1

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings_page():
    from __init__ import load_artist_images
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не выбран!', 'error')
            return redirect(url_for('main.settings_page'))

        files = request.files.getlist('file')
        if not files:
            flash('Файлы не выбраны!', 'error')
            return redirect(url_for('main.settings_page'))

        genre_name = request.form.get('genre', 'unknown')
        genre = Genre.query.filter_by(name=genre_name).first()
        if not genre:
            genre = Genre(name=genre_name)
            db.session.add(genre)
            db.session.commit()

        for file in files:
            if file and file.filename.endswith('.mp3'):
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                if file_size > MAX_FILE_SIZE:
                    flash(f'Файл "{file.filename}" слишком большой! Максимальный размер: {MAX_FILE_SIZE // (1024 * 1024)} МБ.', 'error')
                    file.seek(0)  # Сбрасываем указатель
                    continue
                file.seek(0)
                filename = secure_filename(file.filename)
                file_path = os.path.join('/app/backend/static/audio', genre_name, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                existing_song = Song.query.filter_by(file_name=filename).first()

                if existing_song:
                    flash(f'Песня с именем файла "{filename}" уже существует!', 'error')
                    continue

                # Проверяем, существует ли песня с таким file_name в базе данных
                existing_song = Song.query.filter_by(file_name=filename).first()
                if existing_song:
                    flash(f'Песня с именем файла "{filename}" уже существует в базе данных!', 'error')
                    continue

                try:
                    file.save(file_path)
                    if not os.path.exists(file_path):
                        current_app.logger.error(f"Не удалось сохранить файл {filename} по пути {file_path}")
                        flash(f'Ошибка при сохранении файла "{filename}"!', 'error')
                        continue
                except Exception as e:
                    current_app.logger.error(f"Ошибка при сохранении файла {filename}: {e}")
                    flash(f'Ошибка при сохранении файла "{filename}"!', 'error')
                    continue

                try:
                    audio = MP3(file_path, ID3=ID3)
                    artist_name = audio.get('TPE1', [filename.split('-')[0]])[0]
                    song_name = audio.get('TIT2', [filename.split('.')[0]])[0]
                except Exception as e:
                    current_app.logger.error(f"Ошибка при чтении метаданных из {filename}: {e}")
                    artist_name = filename.split('-')[0] if '-' in filename else filename.split('.')[0]
                    song_name = filename.split('.')[0]

                artist = Artist.query.filter_by(name=artist_name).first()
                if not artist:
                    artist = Artist(name=artist_name, genre_id=genre.id)
                    db.session.add(artist)
                    db.session.commit()

                    # Вызываем load_artist_images для нового артиста
                    load_artist_images(current_app)

                song = Song(name=song_name,
                            file_name=filename,
                            genre_id=genre.id,
                            artist_id=artist.id,
                            file_path=f"/app/backend/static/audio/{genre_name}/{filename}")
                db.session.add(song)
                db.session.commit()

                flash(f'Песня "{song_name}" успешно загружена!', 'success')
            else:
                flash(f'Файл "{file.filename}" не является MP3!', 'error')

        return redirect(url_for('main.settings_page'))

    genres = Genre.query.all()
    return render_template('settings.html', genres=genres)