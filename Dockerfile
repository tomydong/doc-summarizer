FROM python:3.12-slim

# Cài đặt các gói phụ thuộc hệ thống
RUN apt-get update && apt-get install -y \
    pandoc \
    curl \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép requirements.txt trước để tận dụng caching của Docker
COPY requirements.txt .

# Cài đặt các gói phụ thuộc Python
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép tất cả các file khác
COPY . .

# Tạo script khởi động cho Gunicorn với số workers tự động
RUN echo '#!/bin/bash \n\
WORKERS=$(( 2 * $(nproc) + 1 )) \n\
echo "Starting with $WORKERS workers" \n\
exec gunicorn --workers=$WORKERS --threads=2 --worker-class=gthread --bind 0.0.0.0:5000 --timeout=120 --keep-alive=5 --max-requests=1000 --max-requests-jitter=50 app:app \
' > /app/start.sh && chmod +x /app/start.sh

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Port mà ứng dụng sẽ chạy 
EXPOSE 5000

# Khởi động ứng dụng với nhiều workers
CMD ["/app/start.sh"]