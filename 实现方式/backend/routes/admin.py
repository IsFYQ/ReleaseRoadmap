"""
管理员后台 API（admin.html 使用）
"""
import json
import csv
import io
import random
import time
from flask import Blueprint, request, Response

from backend.db import query, execute
from backend.utils import ok, fail, validate_required, validate_enum, validate_date
from backend.db import reset_all

bp = Blueprint("admin", __name__)


@bp.route("/data-sources/by-module/<module_id>", methods=["GET"])
def data_source_by_module(module_id):
    """通过模块 id 获取数据源基本信息（供运营后台使用）"""
    row = query("SELECT id,name,module_id,dingtalk_url,description FROM data_sources WHERE module_id=?", (module_id,), one=True)
    if not row:
        return ok({"module": module_id, "name": module_id, "dingtalkUrl": "", "description": ""})
    return ok({"id": row["id"], "module": row["module_id"], "name": row["name"], "dingtalkUrl": row["dingtalk_url"] or "", "description": row["description"] or ""})


@bp.route("/reset", methods=["POST"])
def admin_reset():
    """清空所有业务数据并重新种子化（保留字典/排期），写入审计日志。"""
    data = request.get_json(silent=True) or {}
    operator = data.get("operator") or "admin"
    reason = data.get("reason") or "通过管理后台重置"
    try:
        result = reset_all(operator=operator, reason=reason)
        return ok(result, message="重置完成")
    except Exception as e:
        return fail("RESET_FAILED", f"重置失败: {e}", 500)


# ============ 数据源 ============

@bp.route("/data-sources", methods=["GET"])
def list_data_sources():
    rows = query("SELECT * FROM data_sources ORDER BY id")
    for r in rows:
        r["enabled"] = bool(r["enabled"])
    return ok(rows)


@bp.route("/data-sources", methods=["POST"])
def create_data_source():
    data = request.get_json(silent=True) or {}
    err = validate_required(data, ["name", "type", "productLine", "moduleId"])
    if err:
        return fail("INVALID_INPUT", err)
    new_id = execute(
        """INSERT INTO data_sources(module_id,name,type,product_line,dingtalk_url,sync_freq,enabled,description)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            data["moduleId"], data["name"], data["type"], data["productLine"],
            data.get("dingtalkUrl", ""), data.get("syncFreq", "手动"),
            1 if data.get("enabled", True) else 0, data.get("description", "")
        )
    )
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "create", f"data_source:{new_id}", f"新建数据源 {data['name']}"))
    row = query("SELECT * FROM data_sources WHERE id=?", (new_id,), one=True)
    row["enabled"] = bool(row["enabled"])
    return ok(row, message="数据源创建成功", status=201)


@bp.route("/data-sources/<int:ds_id>", methods=["PUT"])
def update_data_source(ds_id):
    row = query("SELECT * FROM data_sources WHERE id=?", (ds_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"数据源 {ds_id} 不存在", 404)
    data = request.get_json(silent=True) or {}
    execute(
        """UPDATE data_sources SET name=?, type=?, product_line=?, dingtalk_url=?, sync_freq=?, enabled=?, description=?
           WHERE id=?""",
        (
            data.get("name", row["name"]),
            data.get("type", row["type"]),
            data.get("productLine", row["product_line"]),
            data.get("dingtalkUrl", row["dingtalk_url"] or ""),
            data.get("syncFreq", row["sync_freq"]),
            1 if data.get("enabled", bool(row["enabled"])) else 0,
            data.get("description", row["description"] or ""),
            ds_id,
        )
    )
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "update", f"data_source:{ds_id}", f"更新数据源"))
    new_row = query("SELECT * FROM data_sources WHERE id=?", (ds_id,), one=True)
    new_row["enabled"] = bool(new_row["enabled"])
    return ok(new_row, message="数据源更新成功")


@bp.route("/data-sources/<int:ds_id>/sync", methods=["POST"])
def sync_data_source(ds_id):
    row = query("SELECT * FROM data_sources WHERE id=?", (ds_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"数据源 {ds_id} 不存在", 404)
    if not row["enabled"]:
        return fail("DATA_SOURCE_DISABLED", f"数据源 {row['name']} 已禁用，请先启用", 400)

    # 模拟同步：8% 概率失败
    if random.random() < 0.08:
        execute("INSERT INTO sync_logs(data_source_id,status,message) VALUES (?,?,?)",
                (ds_id, "失败", "网络请求超时（模拟）"))
        return fail("SYNC_FAILED", "钉钉文档拉取失败，请稍后重试", 504)

    rows_count = row["total_rows"] or random.randint(50, 300)
    execute("UPDATE data_sources SET last_sync=datetime('now','localtime') WHERE id=?", (ds_id,))
    execute("INSERT INTO sync_logs(data_source_id,status,imported_rows,message) VALUES (?,?,?,?)",
            (ds_id, "成功", rows_count, f"导入 {rows_count} 条"))
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "sync", f"data_source:{ds_id}", f"同步数据源 {row['name']}"))
    return ok({"imported": rows_count, "lastSync": "now"}, message=f"同步成功，导入 {rows_count} 条")


@bp.route("/data-sources/<int:ds_id>/logs", methods=["GET"])
def data_source_logs(ds_id):
    row = query("SELECT * FROM data_sources WHERE id=?", (ds_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"数据源 {ds_id} 不存在", 404)
    rows = query("SELECT * FROM sync_logs WHERE data_source_id=? ORDER BY sync_time DESC LIMIT 20", (ds_id,))
    return ok(rows)


# ============ 用户 ============

@bp.route("/users", methods=["GET"])
def list_users():
    rows = query("SELECT id,username,realname,role,product_lines,status,last_login,created_at FROM users ORDER BY id")
    return ok(rows)


@bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}
    err = validate_required(data, ["username", "realname"])
    if err:
        return fail("INVALID_INPUT", err)
    if data.get("role") and data["role"] not in ("ops", "admin", "guest"):
        return fail("INVALID_INPUT", "role 取值不合法: ops/admin/guest")
    # 重复校验
    exists = query("SELECT id FROM users WHERE username=?", (data["username"],), one=True)
    if exists:
        return fail("USERNAME_EXISTS", f"账号 {data['username']} 已存在")
    product_lines = data.get("productLines", "")
    if isinstance(product_lines, list):
        product_lines = " / ".join(product_lines)
    new_id = execute(
        "INSERT INTO users(username,realname,password,role,product_lines,status) VALUES (?,?,?,?,?,?)",
        (data["username"], data["realname"], data.get("password", ""), data.get("role", "ops"),
         product_lines, data.get("status", "启用"))
    )
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "create", f"user:{new_id}", f"新建账号 {data['username']}"))
    row = query("SELECT id,username,realname,role,product_lines,status,last_login,created_at FROM users WHERE id=?", (new_id,), one=True)
    return ok(row, message="账号创建成功", status=201)


@bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    row = query("SELECT * FROM users WHERE id=?", (user_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"账号 {user_id} 不存在", 404)
    data = request.get_json(silent=True) or {}
    product_lines = data.get("productLines", row["product_lines"])
    if isinstance(product_lines, list):
        product_lines = " / ".join(product_lines)
    execute(
        "UPDATE users SET realname=?, role=?, product_lines=?, status=? WHERE id=?",
        (data.get("realname", row["realname"]), data.get("role", row["role"]),
         product_lines, data.get("status", row["status"]), user_id)
    )
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "update", f"user:{user_id}", f"更新账号 {row['username']}"))
    new_row = query("SELECT id,username,realname,role,product_lines,status,last_login,created_at FROM users WHERE id=?", (user_id,), one=True)
    return ok(new_row, message="账号更新成功")


@bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    row = query("SELECT * FROM users WHERE id=?", (user_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"账号 {user_id} 不存在", 404)
    if row["role"] == "admin":
        return fail("FORBIDDEN", "管理员账号不允许删除", 403)
    execute("DELETE FROM users WHERE id=?", (user_id,))
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "delete", f"user:{user_id}", f"删除账号 {row['username']}"))
    return ok(message="账号已删除")


# ============ 产品线 ============

@bp.route("/product-lines", methods=["GET"])
def list_product_lines():
    rows = query("SELECT * FROM product_lines ORDER BY id")
    return ok(rows)


@bp.route("/product-lines", methods=["POST"])
def create_product_line():
    data = request.get_json(silent=True) or {}
    err = validate_required(data, ["code", "name"])
    if err:
        return fail("INVALID_INPUT", err)
    exists = query("SELECT id FROM product_lines WHERE code=?", (data["code"],), one=True)
    if exists:
        return fail("CODE_EXISTS", f"产品线代码 {data['code']} 已存在")
    new_id = execute("INSERT INTO product_lines(code,name,status) VALUES (?,?,?)",
                     (data["code"], data["name"], data.get("status", "启用")))
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "create", f"product_line:{new_id}", f"新建产品线 {data['name']}"))
    row = query("SELECT * FROM product_lines WHERE id=?", (new_id,), one=True)
    return ok(row, message="产品线创建成功", status=201)


@bp.route("/product-lines/<int:pl_id>", methods=["PUT"])
def update_product_line(pl_id):
    row = query("SELECT * FROM product_lines WHERE id=?", (pl_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"产品线 {pl_id} 不存在", 404)
    data = request.get_json(silent=True) or {}
    execute("UPDATE product_lines SET name=?, status=? WHERE id=?",
            (data.get("name", row["name"]), data.get("status", row["status"]), pl_id))
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "update", f"product_line:{pl_id}", f"更新产品线 {row['name']}"))
    new_row = query("SELECT * FROM product_lines WHERE id=?", (pl_id,), one=True)
    return ok(new_row, message="产品线更新成功")


# ============ 审计日志 ============

@bp.route("/audit-logs", methods=["GET"])
def list_audit_logs():
    operator = request.args.get("operator")
    action = request.args.get("action")
    sql = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    if operator and operator != "全部":
        sql += " AND operator=?"
        params.append(operator)
    if action and action != "全部":
        sql += " AND action=?"
        params.append(action)
    sql += " ORDER BY created_at DESC LIMIT 100"
    rows = query(sql, tuple(params))
    return ok(rows)


# ============ 导出 ============

@bp.route("/export/report", methods=["GET"])
def export_report():
    """导出月度发版报表（JSON）"""
    from collections import defaultdict
    items = query("SELECT release_date,product_line,release_type,COUNT(*) c FROM items WHERE status='published' AND notify_time IS NOT NULL GROUP BY release_date,product_line,release_type ORDER BY release_date DESC")
    return ok({"exportedAt": _now(), "items": items})


@bp.route("/export/csv", methods=["GET"])
def export_csv():
    rows = query("SELECT id,module,release_date,app_platform,release_type,feature_point,feature_entry,target_user,status,notify_time FROM items ORDER BY release_date DESC")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "模块", "发版日期", "应用/平台", "类型", "功能点", "功能入口", "面向用户", "状态", "通知时间"])
    for r in rows:
        writer.writerow([r["id"], r["module"], r["release_date"], r["app_platform"], r["release_type"],
                         r["feature_point"], r["feature_entry"], r["target_user"], r["status"], r["notify_time"]])
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=releases-{_now()[:10]}.csv"}
    )


@bp.route("/export/json", methods=["GET"])
def export_json():
    rows = query("SELECT * FROM items ORDER BY release_date DESC")
    data = json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2, default=str)
    return Response(data, mimetype="application/json; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename=releases-{_now()[:10]}.json"})


@bp.route("/import/excel", methods=["POST"])
def import_excel():
    """Excel 导入（MVP 阶段占位实现）"""
    file = request.files.get("file")
    if not file:
        return fail("INVALID_INPUT", "未上传文件")
    if not file.filename.endswith((".xlsx", ".xls")):
        return fail("INVALID_INPUT", "仅支持 .xlsx/.xls 格式")
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "import", "excel", f"上传 {file.filename}"))
    return ok({"filename": file.filename, "size": len(file.read())}, message="Excel 导入已提交（解析逻辑待后端完整实现）")


def _now():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
