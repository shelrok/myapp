# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install -r /app/requirements.txt

# Копируем все файлы приложения
COPY . /app

# Указываем команду для запуска Flask-приложения
CMD ["python", "app.py"]
