from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    songs = db.relationship('Song', backref='genre', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Genre(id={self.id}, name={self.name})>"

class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False, index=True)
    image_filename = db.Column(db.String(100), nullable=False, default='default_artist_image.jpg')
    bio = db.Column(db.Text)  # Новое поле для биографии
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    genre = db.relationship('Genre', backref='artists', lazy='select')  # Изменили lazy на 'select'
    songs = db.relationship('Song', backref='artist', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Artist(id={self.id}, name={self.name}, genre_id={self.genre_id})>"

class Song(db.Model):
    __tablename__ = 'song'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False, index=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False, index=True)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Song(id={self.id}, name={self.name}, artist_id={self.artist_id}, genre_id={self.genre_id})>"

class Playlist(db.Model):
    __tablename__ = 'playlist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(100), nullable=False, default='default_playlist_image.jpg')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    songs = db.relationship('Song', secondary='playlist_song', backref='playlists', lazy='dynamic', cascade='all, delete')

    def __repr__(self):
        return f"<Playlist(id={self.id}, name={self.name})>"

class PlaylistSong(db.Model):
    __tablename__ = 'playlist_song'
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True, index=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True, index=True)

    def __repr__(self):
        return f"<PlaylistSong(playlist_id={self.playlist_id}, song_id={self.song_id})>"