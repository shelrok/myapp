# Используем официальный образ Python
FROM python:3.11-slim
# Устанавливаем рабочую директорию
WORKDIR /app
# Копируем файл зависимостей в контейне
# Устанавливаем зависимости и копируем файлы в один слой
# Указываем переменную окружения для Flask
ENV FLASK_APP=run.py
ENV FLASK_ENV=development
# Открываем порт 5000 для Flask
EXPOSE 5000
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
# Указываем команду для запуска Flask-приложения
CMD ["python", "run.py"]
