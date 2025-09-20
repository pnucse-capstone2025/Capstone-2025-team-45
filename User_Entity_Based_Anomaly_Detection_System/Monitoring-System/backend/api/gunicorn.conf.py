import multiprocessing
import os
from pathlib import Path

bind = "0.0.0.0:8001"# Worker processes

workers = 1
worker_class = "uvicorn.workers.UvicornWorker"

# Application configuration
wsgi_app = "app:app"

# Reload configuration
reload = True
reload_extra_files = []

# Recursively add all files under the api directory for reload monitoring
api_dir = Path("api")
if api_dir.exists() and api_dir.is_dir():
    for root, dirs, files in os.walk(api_dir):
        for file in files:
            file_path = os.path.join(root, file)
            reload_extra_files.append(file_path)
# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "fastapi_app"

# Timeout configuration
timeout = 3000  # 요청 처리 타임아웃 (초 단위)
graceful_timeout = 5  # 워커 재시작 시 graceful shutdown 시간 (초 단위)
keepalive = 5  # 연결 유지 시간 (초 단위)

# SSL configuration (uncomment if using HTTPS)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
