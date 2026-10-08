import http.server
import socketserver
import webbrowser
import os
import socket

PORT = 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def get_lan_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    lan_ip = get_lan_ip()
    print(f"本机访问：http://localhost:{PORT}/index.html")
    print(f"手机访问：http://{lan_ip}:{PORT}/index.html")
    print("按 Ctrl+C 停止")
    webbrowser.open(f"http://localhost:{PORT}/index.html")
    httpd.serve_forever()