from flask import Blueprint, render_template
from models import Genre, Artist, Playlist

main_bp = Blueprint('main', __name__, template_folder='templates')

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
