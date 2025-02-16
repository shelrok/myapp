from flask import Blueprint, jsonify
from app.models import Artist, Playlist

api_bp = Blueprint('api', __name__)

@api_bp.route('/artists', methods=['GET'])
def get_artists_api():
    artists = Artist.query.all()
    artists_data = [
        {
            'id': artist.id, 
            'name': artist.name, 
            'bio': artist.bio if artist.bio else "",
            'image': artist.image_filename
        }
        for artist in artists
    ]
    return jsonify(artists_data)

@api_bp.route('/artist/<int:artist_id>', methods=['GET'])
def get_artist_api(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    artist_data = {
        'id': artist.id,
        'name': artist.name,
        'bio': artist.bio if artist.bio else "",
        'image': artist.image_filename
    }
    return jsonify(artist_data)

@api_bp.route('/playlists', methods=['GET'])
def get_playlists_api():
    playlists = Playlist.query.all()
    playlists_data = [
        {
            'id': playlist.id, 
            'name': playlist.name, 
            'description': playlist.description, 
            'image': playlist.image_filename
        }
        for playlist in playlists
    ]
    return jsonify(playlists_data)

@api_bp.route('/playlist/<int:playlist_id>', methods=['GET'])
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
