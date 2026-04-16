# -*- coding: utf-8 -*-
"""
3D模型网页查看器服务器
在PyCharm中右键运行即可启动

使用方法：右键运行此脚本
"""

import http.server
import socketserver
import webbrowser
import os
import time

# 配置
PORT = 8080

# 获取目录路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
WEB_DIR = os.path.join(PROJECT_DIR, "web")


class Handler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        """添加CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def guess_type(self, path):
        """设置正确的MIME类型"""
        ext = os.path.splitext(path)[1].lower()
        mime_types = {
            '.html': 'text/html; charset=utf-8',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.glb': 'model/gltf-binary',
            '.gltf': 'model/gltf+json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
        }
        return mime_types.get(ext, super().guess_type(path))

    def log_message(self, format, *args):
        """简化日志输出"""
        if '127.0.0.1' in args[0] or 'localhost' in args[0]:
            print(f"  {args[0].split()[-1] if args else 'request'}")


def main():
    """启动服务器"""
    print("=" * 50)
    print("3D模型网页查看器")
    print("=" * 50)
    print(f"\n网页目录: {WEB_DIR}")
    print(f"端口: {PORT}")

    # 检查文件
    index_path = os.path.join(WEB_DIR, "index.html")
    model_path = os.path.join(WEB_DIR, "model.glb")

    if os.path.exists(index_path):
        print(f"[OK] 找到: index.html")
    else:
        print(f"[X] 未找到: index.html")

    if os.path.exists(model_path):
        print(f"[OK] 找到: model.glb")
    else:
        print(f"[X] 未找到: model.glb")

    # 允许端口重用
    socketserver.TCPServer.allow_reuse_address = True

    # 创建服务器
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"

        print("\n" + "=" * 50)
        print("服务器已启动!")
        print("=" * 50)
        print(f"\n请在浏览器中打开: {url}")
        print("\n按 Ctrl+C 停止服务器")
        print("=" * 50 + "\n")

        # 延迟打开浏览器
        time.sleep(0.5)
        webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止。")


if __name__ == "__main__":
    main()
