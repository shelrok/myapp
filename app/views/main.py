from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import Genre, Artist, Playlist, Song
import os
import json
import time
from werkzeug.utils import secure_filename
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from __init__ import db 
import feedparser  # Библиотека для парсинга RSS
main_bp = Blueprint('main', __name__, template_folder='templates')

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ

def get_audio_files_by_genre():
    """Возвращает словарь жанров и соответствующих файлов песен с кэшированием в Redis."""
    cache_key = "genres_audio_files"
    start_time_redis = time.time()
    cached_data = current_app.redis.get(cache_key)
    redis_time = time.time() - start_time_redis

    if cached_data:
        current_app.logger.info(f"Returning genres from Redis cache, took {redis_time:.4f} seconds")
        return json.loads(cached_data)

    start_time_db = time.time()
    genres = {}
    genres_in_db = Genre.query.all()
    for genre in genres_in_db:
        audio_files = [song.file_name for song in genre.songs]
        genres[genre.name] = audio_files
    db_time = time.time() - start_time_db

    current_app.redis.setex(cache_key, 3600, json.dumps(genres))
    current_app.logger.info(f"Fetched genres from DB (took {db_time:.4f} seconds), cached in Redis")
    return genres

def get_artists():
    """Возвращает список артистов с кэшированием в Redis."""
    cache_key = "artists_list"
    start_time_redis = time.time()
    cached_data = current_app.redis.get(cache_key)
    redis_time = time.time() - start_time_redis

    if cached_data:
        current_app.logger.info(f"Returning artists from Redis cache, took {redis_time:.4f} seconds")
        return json.loads(cached_data)

    start_time_db = time.time()
    artists = Artist.query.all()
    artists_data = [
        {"id": artist.id, "name": artist.name, "genre_id": artist.genre_id, "bio": artist.bio, "image_filename": artist.image_filename, "genre_name": artist.genre.name}
        for artist in artists
    ]
    db_time = time.time() - start_time_db

    current_app.redis.setex(cache_key, 3600, json.dumps(artists_data))
    current_app.logger.info(f"Fetched artists from DB (took {db_time:.4f} seconds), cached in Redis")
    return artists_data

def get_playlists():
    """Возвращает список плейлистов с кэшированием в Redis."""
    cache_key = "playlists_list"
    start_time_redis = time.time()
    cached_data = current_app.redis.get(cache_key)
    redis_time = time.time() - start_time_redis

    if cached_data:
        current_app.logger.info(f"Returning playlists from Redis cache, took {redis_time:.4f} seconds")
        return json.loads(cached_data)

    start_time_db = time.time()
    playlists = Playlist.query.all()
    playlists_data = [
        {"id": playlist.id, "name": playlist.name, "description": playlist.description, "image_filename": playlist.image_filename}
        for playlist in playlists
    ]
    db_time = time.time() - start_time_db

    current_app.redis.setex(cache_key, 3600, json.dumps(playlists_data))
    current_app.logger.info(f"Fetched playlists from DB (took {db_time:.4f} seconds), cached in Redis")
    return playlists_data

def get_genres_with_songs():
    """Возвращает список жанров с песнями для страницы жанров."""
    cache_key = "genres_with)with_songs"
    start_time_redis = time.time()
    cached_data = current_app.redis.get(cache_key)
    redis_time = time.time() - start_time_redis

    if cached_data:
        current_app.logger.info(f"Returning genres with songs from Redis cache, took {redis_time:.4f} seconds")
        return json.loads(cached_data)

    start_time_db = time.time()
    genres = Genre.query.all()
    genres_data = [
        {"id": genre.id, "name": genre.name, "songs": [{"id": song.id, "name": song.name, "file_name": song.file_name} for song in genre.songs]}
        for genre in genres
    ]
    db_time = time.time() - start_time_db

    current_app.redis.setex(cache_key, 3600, json.dumps(genres_data))
    current_app.logger.info(f"Fetched genres with songs from DB (took {db_time:.4f} seconds), cached in Redis")
    return genres_data

def get_songs():
    """Возвращает список всех песен с кэшированием в Redis."""
    cache_key = "songs_list"
    start_time_redis = time.time()
    cached_data = current_app.redis.get(cache_key)
    redis_time = time.time() - start_time_redis

    if cached_data:
        current_app.logger.info(f"Returning songs from Redis cache, took {redis_time:.4f} seconds")
        return json.loads(cached_data)

    start_time_db = time.time()
    songs = Song.query.all()
    songs_data = [
        {"id": song.id, "name": song.name, "file_name": song.file_name, "genre_name": song.genre.name, "artist": {"id": song.artist.id, "name": song.artist.name, "image_filename": song.artist.image_filename}}
        for song in songs
    ]
    db_time = time.time() - start_time_db

    current_app.redis.setex(cache_key, 3600, json.dumps(songs_data))
    current_app.logger.info(f"Fetched songs from DB (took {db_time:.4f} seconds), cached in Redis")
    return songs_data

def get_artist_with_songs(artist_id):
    """Возвращает данные об артисте и его песнях с кэшированием в Redis."""
    cache_key = f"artist_{artist_id}_with_songs"
    start_time_redis = time.time()
    cached_data = current_app.redis.get(cache_key)
    redis_time = time.time() - start_time_redis

    if cached_data:
        current_app.logger.info(f"Returning artist {artist_id} with songs from Redis cache, took {redis_time:.4f} seconds")
        return json.loads(cached_data)

    start_time_db = time.time()
    artist = Artist.query.get_or_404(artist_id)
    songs = Song.query.filter_by(artist_id=artist_id).all()
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "bio": artist.bio,
        "image_filename": artist.image_filename,
        "songs": [{"id": song.id, "name": song.name, "file_name": song.file_name, "genre_name": song.genre.name} for song in songs]
    }
    db_time = time.time() - start_time_db

    current_app.redis.setex(cache_key, 3600, json.dumps(artist_data))
    current_app.logger.info(f"Fetched artist {artist_id} with songs from DB (took {db_time:.4f} seconds), cached in Redis")
    return artist_data

@main_bp.route('/')
def index():
    start_time = time.time()
    genres = get_audio_files_by_genre()
    artists = get_artists()
    playlists = get_playlists()
    total_time = time.time() - start_time
    current_app.logger.info(f"Index page loaded in {total_time:.4f} seconds")
    return render_template('index.html', genres=genres, artists=artists, playlists=playlists)

@main_bp.route('/albums')
def albums_page():
    artists = get_artists()
    # Для страницы альбомов добавляем список песен для каждого артиста
    for artist in artists:
        artist_songs = get_artist_with_songs(artist["id"])["songs"]
        artist["songs_list"] = artist_songs  # Добавляем песни в данные артиста
    return render_template('albums.html', artists=artists)

@main_bp.route('/playlists')
def playlists_page():
    playlists = get_playlists()
    # Добавляем песни для каждого плейлиста
    for playlist in playlists:
        playlist_obj = Playlist.query.get(playlist["id"])
        playlist["songs"] = [
            {"id": song.id, "name": song.name, "file_name": song.file_name, "genre_name": song.genre.name}
            for song in playlist_obj.songs
        ]
    return render_template('playlists.html', playlists=playlists)

@main_bp.route('/genres')
def genres_page():
    genres = get_genres_with_songs()
    return render_template('genres.html', genres=genres)

@main_bp.route('/artists')
def artists_page():
    artists = get_artists()
    return render_template('artists.html', artists=artists)

@main_bp.route('/artist/<int:artist_id>')
def artist_page(artist_id):
    artist_data = get_artist_with_songs(artist_id)
    return render_template('artist.html', artist=artist_data, songs=artist_data["songs"])

@main_bp.route('/songs')
def songs_page():
    songs = get_songs()
    return render_template('songs.html', songs=songs)

@main_bp.route('/news')
def news_page():
    start_time = time.time()
    # Парсим RSS-ленту Billboard
    rss_url = "https://www.billboard.com/feed/"
    feed = feedparser.parse(rss_url)
    
    # Извлекаем новости
    news_items = [
        {
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary,
            "published": entry.published if "published" in entry else "N/A"
        }
        for entry in feed.entries[:10]  # Ограничиваем 10 новостями
    ]
    
    fetch_time = time.time() - start_time
    current_app.logger.info(f"News fetched from RSS in {fetch_time:.4f} seconds")
    
    return render_template('news.html', news_items=news_items, fetch_time=f"{fetch_time:.4f}")

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
                    file.seek(0)
                    continue
                file.seek(0)
                filename = secure_filename(file.filename)
                file_path = os.path.join('/app/backend/static/audio', genre_name, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                existing_song = Song.query.filter_by(file_name=filename).first()

                if existing_song:
                    flash(f'Песня с именем файла "{filename}" уже существует!', 'error')
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
                    load_artist_images(current_app)

                song = Song(name=song_name,
                            file_name=filename,
                            genre_id=genre.id,
                            artist_id=artist.id,
                            file_path=f"/app/backend/static/audio/{genre_name}/{filename}")
                db.session.add(song)
                db.session.commit()

                # Очищаем кэш после добавления новых данных
                current_app.redis.delete("genres_audio_files")
                current_app.redis.delete("artists_list")
                current_app.redis.delete("playlists_list")
                current_app.redis.delete("genres_with_songs")
                current_app.redis.delete("songs_list")
                current_app.redis.delete(f"artist_{artist.id}_with_songs")

                flash(f'Песня "{song_name}" успешно загружена!', 'success')
            else:
                flash(f'Файл "{file.filename}" не является MP3!', 'error')

        return redirect(url_for('main.settings_page'))

    genres = get_genres_with_songs()
    return render_template('settings.html', genres=[{"name": genre["name"]} for genre in genres])