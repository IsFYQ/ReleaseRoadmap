"""
发版路线图 - Flask 后端入口
"""
import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from backend.db import init_db
from backend.routes.items import bp as items_bp
from backend.routes.public import bp as public_bp
from backend.routes.admin import bp as admin_bp
from backend.routes.images import bp as images_bp


def create_app():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__, static_folder=None, root_path=root)
    CORS(app)

    # 配置
    app.config["UPLOAD_FOLDER"] = os.path.join(root, "uploads")
    app.config["JSON_AS_ASCII"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # 初始化数据库
    init_db()

    # 注册蓝图
    app.register_blueprint(public_bp, url_prefix="/api")
    app.register_blueprint(items_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(images_bp, url_prefix="/api/images")

    # 静态文件服务（前端 HTML）
    @app.route("/")
    def root_index():
        return send_from_directory(root, "index.html")

    @app.route("/<path:filename>")
    def static_file(filename):
        return send_from_directory(root, filename)

    # 统一错误处理
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"code": "NOT_FOUND", "message": "接口不存在"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"code": "INTERNAL_ERROR", "message": "服务器内部错误"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
