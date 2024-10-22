from flask import Flask, Response, request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import time

app = Flask(__name__)

# Определение метрик
REQUEST_COUNT = Counter('request_count', 'Total Request Count')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency in seconds')

@app.before_request
def before_request():
    # Сохраняем время начала запроса
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # Вычисляем латентность запроса
    if hasattr(request, 'start_time'):
        latency = time.time() - request.start_time
        REQUEST_LATENCY.observe(latency)
    return response

@app.route('/')
def hello():
    REQUEST_COUNT.inc()
    return "Hello, World!"

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

