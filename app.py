import os
import tempfile
import datetime
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import markdown
import re
import io
import pypandoc
import fitz
from flask_cors import CORS
import google.generativeai as genai
import shutil
from tika import parser

try:
    pypandoc.get_pandoc_path()
except OSError:
    pypandoc.download_pandoc()

# Khởi tạo các biến môi trường
load_dotenv()

# Cấu hình Flask app
app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Giới hạn kích thước file 16MB
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()  # Thư mục tạm để lưu file upload

# Định nghĩa các loại file được chấp nhận
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "doc", "rtf", "odt", "md"}


# Hàm kiểm tra phần mở rộng của file
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Hàm đọc nội dung từ các loại file khác nhau
def extract_text_from_file(file_path, file_ext):
    try:
        if file_ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif file_ext in ["docx", "rtf", "odt"]:
            try:
                # Sử dụng pypandoc để chuyển đổi các định dạng văn bản phổ biến sang text
                return pypandoc.convert_file(file_path, "plain", format=file_ext)
            except Exception as e:
                return f"Lỗi khi đọc file {file_ext}: {str(e)}"
        elif file_ext == "doc":
            try:
                # Thử với tika
                parsed = parser.from_file(file_path)
                if parsed["content"]:
                    return parsed["content"]
            except Exception as e:
                return f"Lỗi khi đọc file {file_ext}: {str(e)}"
        elif file_ext == "pdf":
            try:
                #                import pdftotext
                #                with open(file_path, "rb") as f:
                #                    pdf = pdftotext.PDF(f)
                #                # Trả về toàn bộ văn bản, các trang được phân tách bằng dấu xuống dòng kép
                #                return "\n\n".join(pdf)
                doc = fitz.open(file_path)
                return "\n\n".join(page.get_text() for page in doc)
            except ImportError:
                return "Lỗi: Thư viện 'pdftotext' không được cài đặt. Vui lòng cài đặt bằng lệnh: pip install pdftotext"
            except Exception as e:
                print(f"Lỗi khi đọc file PDF bằng pdftotext: {str(e)}")
                return f"Lỗi khi đọc file PDF bằng pdftotext: {str(e)}"
        elif file_ext == "md":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return "Định dạng file không được hỗ trợ."
    except Exception as e:
        print(f"Lỗi khi đọc file: {str(e)}")
        return f"Lỗi khi đọc file: {str(e)}"


# Hàm tóm tắt tài liệu bằng Gemini API
def summarize_with_api(content, prompt):
    # Đặt mã API từ biến môi trường
    api_key = os.getenv("GEMINI_API_KEY")
    model_version = os.getenv("MODEL_VERSION", "gemini-2.0-flash-thinking-exp-01-21")
    if not api_key:
        return (
            "Không tìm thấy API key trong biến môi trường. Vui lòng kiểm tra file .env."
        )

    try:
        # Khởi tạo Gemini API
        genai.configure(api_key=api_key)

        # Tạo mô hình và cài đặt cấu hình
        model = genai.GenerativeModel(
            model_name=model_version,
            #            generation_config={
            #                "max_output_tokens": 2000,  # Tăng số lượng tokens tối đa
            #                "temperature": 0.2,
            #            }
        )

        # Tạo yêu cầu tóm tắt với system prompt
        system_prompt = "Bạn là một trợ lý AI chuyên tóm tắt tài liệu. Hãy tóm tắt nội dung tài liệu dưới dạng Markdown. Đảm bảo kết thúc mỗi điểm dấu đầu dòng bằng một dấu chấm hoặc dấu phẩy phù hợp."
        user_message = f"{prompt}\n\nĐây là nội dung cần tóm tắt:\n\n{content}"

        try:
            # Kết hợp system prompt và user message
            chat = model.start_chat(history=[])
            response = chat.send_message(f"{system_prompt}\n\n{user_message}")

            # Kiểm tra response trước khi truy cập
            if hasattr(response, "text") and response.text:
                return response.text
            elif hasattr(response, "parts") and response.parts:
                if len(response.parts) > 0 and hasattr(response.parts[0], "text"):
                    return response.parts[0].text
                else:
                    return "Không nhận được định dạng phản hồi hợp lệ."
            else:
                return "Không nhận được phản hồi có nội dung từ API. Vui lòng thử lại."

        except IndexError:
            # Xử lý cụ thể lỗi index out of range
            return "Lỗi xử lý phản hồi từ API. Vui lòng thử lại hoặc kiểm tra cấu hình API."

    except Exception as e:
        return f"Lỗi khi tóm tắt: {str(e)}"


def markdown_to_docx_pandoc(
    markdown_text, original_filename=None, reference_docx_path=None
):
    # Tiêu đề chính
    if original_filename:
        title = f"# TÓM TẮT TÀI LIỆU: {original_filename}\n\n"
    else:
        title = "# TÓM TẮT TÀI LIỆU\n\n"

    # Thêm thời gian tạo tài liệu
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    footer = ""  # f'\n\n---\n_Tạo lúc: {timestamp}_\n'

    # Ghép nội dung đầy đủ
    full_markdown = title + markdown_text.strip() + footer

    # Tạo file tạm để lưu DOCX output
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        output_path = tmp_docx.name

    # Chuyển đổi markdown -> docx với tùy chọn template doc
    extra_args = []
    if reference_docx_path:
        extra_args += [f"--reference-doc={reference_docx_path}"]
    print(extra_args)

    # Chuyển đổi markdown -> docx
    try:
        pypandoc.convert_text(
            full_markdown,
            to="docx",
            format="md",
            outputfile=output_path,
            extra_args=extra_args,
        )
        with open(output_path, "rb") as f:
            docx_io = io.BytesIO(f.read())
        docx_io.seek(0)
    except Exception as e:
        print(f"[ERROR] Pandoc conversion failed: {str(e)}")

    finally:
        os.remove(output_path)  # Dọn dẹp file tạm

    return docx_io


# Route cho trang chủ
@app.route("/")
def index():
    return render_template("index.html")


# Route xử lý upload file
@app.route("/upload", methods=["POST"])
def upload_file():
    print(dir(app.config))
    if "file" not in request.files:
        return jsonify({"error": "Không có file nào được gửi lên"})

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Không có file nào được chọn"})

    # Create a dedicated upload folder instead of using temp directory
    uploads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(uploads_folder, exist_ok=True)

    if file and allowed_file(file.filename):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = timestamp + "_" + secure_filename(file.filename)
        file_path = os.path.join(uploads_folder, filename)
        file.save(file_path)

        file_ext = filename.rsplit(".", 1)[1].lower()

        # Nếu là file doc hoặc docx, copy vào thư mục static
        #        if file_ext in ['doc', 'docx']:
        #            static_dir = 'static'
        #            os.makedirs(static_dir, exist_ok=True)
        #            reference_org_path = os.path.join(static_dir, f"reference_org.{file_ext}")
        #            try:
        #                shutil.copy(file_path, reference_org_path)
        #                print(f"Đã sao chép file gốc vào: {reference_org_path}")
        #            except Exception as e:
        #                print(f"Lỗi khi sao chép file gốc: {e}")

        content = extract_text_from_file(file_path, file_ext)

        # # Xóa file sau khi đã đọc xong
        # os.remove(file_path)

        return jsonify(
            {
                "message": "File đã được tải lên thành công",
                "content": content,
                "file_path": file_path,
            }
        )
    else:
        return jsonify({"error": "Định dạng file không được hỗ trợ"})


# Route xử lý tóm tắt tài liệu
@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.get_json()

    if not data or "documentContent" not in data or "prompt" not in data:
        return jsonify({"error": "Thiếu thông tin cần thiết"})

    document_content = data["documentContent"]
    prompt = data["prompt"]

    if not document_content:
        return jsonify({"error": "Nội dung tài liệu trống"})

    if not prompt:
        return jsonify({"error": "Prompt trống"})

    # Kiểm tra xem nội dung có chứa lỗi Pandoc không
    if "Không tìm thấy Pandoc" in document_content:
        suggestion = """
Hướng dẫn cài đặt Pandoc:
1. Tải Pandoc từ https://pandoc.org/installing.html
2. Cài đặt và đảm bảo Pandoc được thêm vào PATH
3. Khởi động lại ứng dụng
Hoặc sử dụng lệnh: pip install pypandoc
"""
        return jsonify({"error": document_content, "suggestion": suggestion})

    # Tóm tắt tài liệu
    summary = summarize_with_api(document_content, prompt)

    # Kiểm tra xem kết quả có phải là lỗi không
    if summary.startswith("Lỗi"):
        return jsonify({"error": summary})

    return jsonify({"summary": summary})


# Route xử lý export sang DOCX
@app.route("/export_docx", methods=["POST"])
def export_docx():
    data = request.get_json()

    if not data or "summary" not in data:
        return jsonify({"error": "Thiếu thông tin cần thiết"})

    markdown_text = data["summary"]
    original_filename = data.get("filename", "")
    file_path = data.get("file_path", "")

    reference_docx_path = "static/reference.docx"

    print("original_filename:", original_filename)
    print("file_path:", file_path)
    file_ext = original_filename.rsplit(".", 1)[1].lower()
    if file_ext in ["doc", "docx"] and file_path:
        print("Đang sử dụng file gốc để làm mẫu")
        reference_docx_path = file_path

    if not markdown_text:
        return jsonify({"error": "Nội dung tóm tắt trống"})

    try:
        # Chuyển đổi markdown sang DOCX với tên file gốc
        docx_io = markdown_to_docx_pandoc(
            markdown_text, original_filename, reference_docx_path
        )

        # Tạo tên file xuất
        if original_filename:
            # Đảm bảo không có phần mở rộng trong tên file
            base_filename = (
                original_filename.split(".")[0]
                if "." in original_filename
                else original_filename
            )
            download_name = f"{base_filename}_summary.docx"
        else:
            download_name = "summary.docx"

        # Trả về file DOCX
        return send_file(
            docx_io,
            download_name=download_name,
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        return jsonify({"error": f"Lỗi khi xuất file DOCX: {str(e)}"})


# Khởi chạy app
if __name__ == "__main__":
    app.run(debug=True)
