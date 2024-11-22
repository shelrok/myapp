import os
from flask import Flask, render_template, send_from_directory

# Путь к папке шаблонов и статических файлов
TEMPLATES_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'templates')
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'static')

app = Flask(__name__, template_folder=TEMPLATES_FOLDER, static_folder=STATIC_FOLDER)

# Папка, где будут храниться аудиофайлы
AUDIO_FOLDER = os.path.join(STATIC_FOLDER, 'audio')

# Главная страница с аудиофайлами
@app.route('/')
def index():
    audio_files = os.listdir(AUDIO_FOLDER)
    return render_template('index.html', audio_files=audio_files)

# Эндпоинт для проигрывания аудио
@app.route('/audio/<filename>')
def get_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
