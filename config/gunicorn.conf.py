wsgi_app = "config.asgi:app"
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
threads = 2
preload_app = False
keepalive = 100

accesslog = "-"
