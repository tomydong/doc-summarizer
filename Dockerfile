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

# Sao chép script khởi động
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Sao chép tất cả các file khác
COPY . .

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Port mà ứng dụng sẽ chạy 
EXPOSE 5000

# Khởi động ứng dụng với nhiều workers
CMD ["/app/start.sh"]