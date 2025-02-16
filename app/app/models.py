from app import db

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
