# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей в контейнер
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем все файлы приложения в контейнер
COPY . /app

# Указываем переменную окружения для Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Открываем порт 5000 для Flask
EXPOSE 5000

# Указываем команду для запуска Flask-приложения
CMD ["python", "app.py"]
