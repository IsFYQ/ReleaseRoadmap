"""
统一错误响应辅助
"""
from flask import jsonify


def ok(data=None, message="success", status=200):
    return jsonify({"code": "OK", "message": message, "data": data}), status


def fail(code, message, status=400, data=None):
    return jsonify({"code": code, "message": message, "data": data}), status


VALID_RELEASES_TYPE = {"新增", "优化", "修复", "删除", "微软云相关依赖移除"}
VALID_TARGET_USER = {"全部", "作业", "教辅"}
VALID_SCOPE = {"web", "App", "小程序", "PC", "Android", "钉钉", "后端", "服务端", "多端", "\\"}
VALID_STATUS = {"imported", "edited", "published"}


def validate_required(data, fields):
    missing = [f for f in fields if not str(data.get(f, "")).strip()]
    if missing:
        return f"缺少必填字段: {', '.join(missing)}"
    return None


def validate_enum(value, allowed, field):
    if value is None or value == "":
        return None
    if value not in allowed:
        return f"{field} 取值不合法，允许: {', '.join(allowed)}"
    return None


def validate_date(value, field):
    if not value:
        return None
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return f"{field} 日期格式应为 YYYY-MM-DD"
    return None


def validate_datetime(value, field):
    if not value:
        return None
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", value):
        return f"{field} 时间格式应为 YYYY-MM-DD HH:MM"
    return None
