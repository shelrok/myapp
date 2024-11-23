from flask import Flask, render_template, send_from_directory, jsonify, redirect, url_for
import os

TEMPLATES_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'templates')
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'static')
AUDIO_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'static', 'audio')

app = Flask(__name__, template_folder=TEMPLATES_FOLDER, static_folder=STATIC_FOLDER, static_url_path='/musicservice/static')
app.config['APPLICATION_ROOT'] = '/musicservice'  # Устанавливаем путь корня приложения


# Получение всех жанров (папок) и аудиофайлов внутри них
def get_audio_files_by_genre():
    genres = {}
    # Получаем все папки в директории audio
    for genre in os.listdir(AUDIO_FOLDER):
        genre_path = os.path.join(AUDIO_FOLDER, genre)
        if os.path.isdir(genre_path):
            # Получаем список аудиофайлов для каждого жанра
            audio_files = [f for f in os.listdir(genre_path) if f.endswith('.mp3')]
            genres[genre] = audio_files
    return genres

# Главная страница с жанрами и аудиофайлами
@app.route('/musicservice/')
def index():
    genres = get_audio_files_by_genre()  # Получаем жанры и файлы
    return render_template('index.html', genres=genres)

# Эндпоинт для проигрывания аудио
@app.route('/musicservice/audio/<genre>/<filename>')
def get_audio(genre, filename):
    genre_folder = os.path.join(AUDIO_FOLDER, genre)
    file_path = os.path.join(genre_folder, filename)
    print(f"Serving file: {file_path}")  # Логируем путь к файлу
    return send_from_directory(genre_folder, filename)

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
