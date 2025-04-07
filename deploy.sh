#!/bin/bash

# Script triển khai Document Summarizer App lên Ubuntu Server với Supervisor
# Tạo bởi GitHub Copilot, ngày 07/04/2025

# Màu sắc cho terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Thông tin triển khai
APP_NAME="doc-summarizer"
APP_DIR="/opt/$APP_NAME"
USER="$USER"
GROUP="$USER"
PORT=5000 # Port mà ứng dụng sẽ chạy

echo -e "${BLUE}=== BẮT ĐẦU TRIỂN KHAI $APP_NAME ===${NC}"

# 1. Cài đặt các gói phụ thuộc hệ thống
echo -e "${YELLOW}[1/6] Cài đặt các gói phụ thuộc hệ thống...${NC}"
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv pandoc supervisor

# 2. Tạo thư mục ứng dụng
echo -e "${YELLOW}[2/6] Tạo thư mục ứng dụng...${NC}"
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$GROUP $APP_DIR

# 3. Sao chép mã nguồn
echo -e "${YELLOW}[3/6] Sao chép mã nguồn...${NC}"
rsync -av --exclude='venv' --exclude='.git' --exclude='__pycache__' ./ $APP_DIR/

# 4. Thiết lập môi trường ảo và cài đặt gói phụ thuộc
echo -e "${YELLOW}[4/6] Thiết lập môi trường ảo và cài đặt gói phụ thuộc...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 5. Tạo file .env nếu cần
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}Tạo file .env...${NC}"
    cat > $APP_DIR/.env << EOF
GEMINI_API_KEY=your_api_key_here
MODEL_VERSION=gemini-pro
EOF
    echo -e "${RED}QUAN TRỌNG: Cập nhật API key trong file $APP_DIR/.env${NC}"
fi

# 6. Tạo cấu hình Supervisor
echo -e "${YELLOW}[5/6] Tạo cấu hình Supervisor...${NC}"
sudo bash -c "cat > /etc/supervisor/conf.d/$APP_NAME.conf" << EOF
[program:$APP_NAME]
directory=$APP_DIR
command=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:$PORT app:app
user=$USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/$APP_NAME/gunicorn.err.log
stdout_logfile=/var/log/$APP_NAME/gunicorn.out.log
environment=PATH="$APP_DIR/venv/bin"
EOF

# Tạo thư mục logs
echo -e "${YELLOW}[6/6] Tạo thư mục logs...${NC}"
sudo mkdir -p /var/log/$APP_NAME
sudo chown -R $USER:$GROUP /var/log/$APP_NAME

# 7. Khởi động dịch vụ Supervisor
echo -e "${YELLOW}Khởi động lại Supervisor...${NC}"
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start $APP_NAME

echo -e "${GREEN}=== TRIỂN KHAI HOÀN TẤT ===${NC}"
echo -e "${BLUE}Ứng dụng đã được triển khai và đang chạy tại: http://YOUR_SERVER_IP:$PORT${NC}"
echo -e "${YELLOW}Kiểm tra trạng thái: sudo supervisorctl status $APP_NAME${NC}"
echo -e "${YELLOW}Xem log: sudo supervisorctl tail -f $APP_NAME${NC}"
echo ""
echo -e "${RED}QUAN TRỌNG: Nhớ cập nhật GEMINI_API_KEY trong file $APP_DIR/.env${NC}"
echo -e "${GREEN}Lưu ý: Nếu bạn muốn truy cập từ bên ngoài, đảm bảo mở port $PORT trong tường lửa:${NC}"
echo -e "${YELLOW}sudo ufw allow $PORT/tcp${NC}"