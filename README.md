# Document Summarizer

Ứng dụng tóm tắt tài liệu sử dụng Google Gemini API, cho phép tải lên tài liệu ở nhiều định dạng khác nhau (PDF, DOCX, TXT, MD) và tạo tóm tắt tự động.

## Tính năng

- Hỗ trợ nhiều định dạng tài liệu: DOCX, PDF, TXT, RTF, ODT, MD
- Sử dụng Google Gemini API để tạo tóm tắt thông minh
- Xuất tóm tắt sang file DOCX
- Giao diện người dùng thân thiện, dễ sử dụng

## Yêu cầu hệ thống

- Python 3.8+
- Pandoc (cho chức năng chuyển đổi định dạng)
- Poppler-utils (cho xử lý file PDF)
- MuPDF dependencies (cho xử lý và tạo file PDF)
- API key của Google Gemini

## Cách chạy trên môi trường local

### 1. Chuẩn bị môi trường

Clone repository về máy tính của bạn:
```bash
git clone https://github.com/your-username/doc-summarizer.git
cd doc-summarizer
```

### 2. Cài đặt các gói phụ thuộc

#### a. Tạo môi trường ảo Python:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc
.venv\Scripts\activate     # Windows
```

#### b. Cài đặt các dependencies của hệ thống:
- **Linux**: 
  ```bash
  sudo apt-get install pandoc poppler-utils libmupdf-dev mupdf-tools pkg-config gcc g++ libfreetype6-dev
  ```
- **MacOS**: 
  ```bash
  brew install pandoc poppler mupdf pkg-config freetype
  ```
- **Windows**: 
  - Pandoc: Tải từ https://pandoc.org/installing.html
  - Poppler: Tải từ https://github.com/oschwartz10612/poppler-windows/releases/
  - MuPDF: Tải từ https://mupdf.com/releases/index.html

#### c. Cài đặt các gói thư viện Python:
```bash
pip install -r requirements.txt
```

### 3. Cấu hình API key

Tạo file `.env` trong thư mục gốc của dự án:
```
GEMINI_API_KEY=your_api_key_here
MODEL_VERSION=gemini-2.0-flash-thinking-exp-01-21
```

### 4. Chạy ứng dụng

```bash
python app.py
```

Truy cập ứng dụng tại: http://localhost:5000

## Triển khai lên môi trường production

Có hai cách chính để triển khai ứng dụng document summarizer lên môi trường production:

### A. Sử dụng Docker (Đề xuất)

#### 1. Xây dựng và chạy với Docker Compose:

Đảm bảo bạn đã cài đặt Docker và Docker Compose, sau đó:

```bash
# Tạo file .env với API key của bạn
echo "GEMINI_API_KEY=your_api_key_here" > .env
echo "MODEL_VERSION=gemini-2.0-flash-thinking-exp-01-21" >> .env

# Build và chạy container
docker-compose up -d --build
```

Ứng dụng sẽ chạy tại: http://your-server-ip:5000

#### 2. Quản lý Docker container:

```bash
# Kiểm tra logs
docker-compose logs -f

# Khởi động lại container
docker-compose restart

# Dừng và xóa container
docker-compose down
```

### B. Triển khai trực tiếp trên Ubuntu với Supervisor

#### 1. Sử dụng script triển khai tự động:

```bash
# Cấp quyền thực thi cho script
chmod +x deploy.sh

# Chạy script triển khai
./deploy.sh
```

Script sẽ tự động:
- Cài đặt các gói phụ thuộc (Python, Pandoc, Supervisor)
- Thiết lập môi trường ảo và cài đặt các gói Python
- Cấu hình Supervisor để quản lý ứng dụng
- Khởi động ứng dụng trên port 5000

#### 2. Các lệnh quản lý với Supervisor:

```bash
# Kiểm tra trạng thái
sudo supervisorctl status doc-summarizer

# Khởi động lại ứng dụng
sudo supervisorctl restart doc-summarizer

# Xem log theo thời gian thực
sudo supervisorctl tail -f doc-summarizer

# Dừng ứng dụng
sudo supervisorctl stop doc-summarizer
```

#### 3. Sau khi triển khai:

- Đảm bảo đã cập nhật API key trong file `/opt/doc-summarizer/.env`
- Mở port 5000 nếu cần truy cập từ bên ngoài: `sudo ufw allow 5000/tcp`

## Tích hợp với Nginx (Tùy chọn)

Nếu bạn muốn sử dụng Nginx làm reverse proxy, bạn có thể tham khảo file cấu hình mẫu `nginx-config.conf` trong dự án.

## Lưu ý bảo mật

- Không commit file `.env` chứa API key lên repository
- Hạn chế quyền truy cập vào thư mục chứa ứng dụng
- Cân nhắc việc bật xác thực HTTP Basic nếu triển khai công khai

## Hỗ trợ

Nếu bạn gặp vấn đề hoặc có câu hỏi, vui lòng tạo issue trên repository của dự án.

## Giấy phép

[MIT](LICENSE)


