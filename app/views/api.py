from flask import Blueprint, jsonify
from models import Artist, Playlist

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
# @api_bp.route('/upload/artist_image/<int:artist_id>', methods=['POST'])
# def upload_artist_image(artist_id):
#     artist = Artist.query.get_or_404(artist_id)
#     image_file = request.files['image']
#     image_filename = f"{artist_id}_{secure_filename(image_file.filename)}"
#     image_path = os.path.join(Config.ARTIST_IMAGES_FOLDER, image_filename)
#     image_file.save(image_path)
#     artist.image_filename = image_filename  # Сохраняем только имя файла
#     db.session.commit()
#     return jsonify({"message": "Image uploaded successfully", "image_path": f"artists/{image_filename}"})

# @api_bp.route('/upload/playlist_image/<int:playlist_id>', methods=['POST'])
# def upload_playlist_image(playlist_id):
#     playlist = Playlist.query.get_or_404(playlist_id)
#     image_file = request.files['image']
#     image_filename = f"{playlist_id}_{secure_filename(image_file.filename)}"
#     image_path = os.path.join(Config.PLAYLIST_IMAGES_FOLDER, image_filename)
#     image_file.save(image_path)
#     playlist.image_filename = image_filename  # Сохраняем только имя файла
#     db.session.commit()
#     return jsonify({"message": "Image uploaded successfully", "image_path": f"playlists/{image_filename}"})