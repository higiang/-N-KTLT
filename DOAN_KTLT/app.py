import webview
from flask import Flask, render_template, url_for
import threading
import socket

app = Flask(__name__, static_folder='static', template_folder='templates')


# Tìm một cổng (port) trống để tránh lỗi "Address already in use"
def get_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@app.route('/')
def reports():
    return render_template('ceo.html/ceo_reports.html')


def run_flask(port):
    # Tắt reloader để không bị xung đột với threading
    app.run(port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    port = get_free_port()

    # Chạy Flask server ngầm
    t = threading.Thread(target=run_flask, args=(port,), daemon=True)
    t.start()

    # Cấu hình cửa sổ WebView để fit màn hình
    # - width/height: Kích thước khởi tạo
    # - min_size: Không cho phép thu nhỏ quá mức làm hỏng layout
    # - resizable: Cho phép người dùng kéo giãn cửa sổ
    window = webview.create_window(
        'Lemonade CEO Reports',
        f'http://127.0.0.1:{port}',
        width=1280,
        height=800,
        min_size=(1024, 768),
        resizable=True,
        confirm_close=True
    )

    webview.start()