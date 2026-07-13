"""
公开 API（index.html 使用）
"""
import json
import os
from collections import defaultdict
from flask import Blueprint, request, jsonify

from backend.db import query, execute
from backend.utils import ok, fail, validate_enum, validate_date, validate_datetime

bp = Blueprint("public", __name__)


def _row_to_public(r):
    """对齐发布清单 13 列字段（PRD V2 §3.3）"""
    return {
        "id": r["id"],
        "releaseDate": r["release_date"],
        "platformScope": r["platform_scope"] or "",
        "appPlatform": r["app_platform"],
        "scope": r["scope"] or "",
        "releaseType": r["release_type"],
        "featurePoint": r["feature_point"],
        "featureEntry": r["feature_entry"] or "",
        "specialNotes": r["special_notes"] or "",
        "limitNotes": r["limit_notes"] or "",
        "notes": r["notes"] or "",
        "isHighlight": r["is_highlight"] or "",
        "provideMaterial": r["provide_material"] or "",
        "remarks": r["remarks"] or "",
        "productLine": r["product_line"] or "",
        "notifyTime": r["notify_time"] or "",
        "targetUser": r["target_user"] or "全部",
        "module": r["module"],
    }


@bp.route("/public/releases", methods=["GET"])
def public_releases():
    """
    公开页发版列表，按通知时间分组返回
    Query: productLine, releaseType, start, end
    """
    product_line = request.args.get("productLine")
    release_type = request.args.get("releaseType")
    start = request.args.get("start")
    end = request.args.get("end")

    sql = "SELECT * FROM items WHERE status = 'published' AND notify_time IS NOT NULL"
    params = []
    if product_line and product_line != "全部产品线":
        sql += " AND product_line = ?"
        params.append(product_line)
    if release_type and release_type not in ("全部类型", ""):
        sql += " AND release_type = ?"
        params.append(release_type)
    if start:
        sql += " AND notify_time >= ?"
        params.append(start)
    if end:
        sql += " AND notify_time <= ?"
        params.append(end + " 23:59")
    sql += " ORDER BY notify_time DESC, release_type ASC, id ASC"

    rows = query(sql, tuple(params))
    groups = defaultdict(list)
    overview = {
        "latestRelease": "",
        "last30Count": 0,
        "productLineCount": defaultdict(int),
        "nextReleaseDate": "",
        "nextReleaseTheme": "",
    }

    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    for r in rows:
        d = (r["notify_time"] or "")[:10]
        groups[d].append(_row_to_public(r))
        if not overview["latestRelease"] or d > overview["latestRelease"]:
            overview["latestRelease"] = d
        if d >= cutoff:
            overview["last30Count"] += 1
        overview["productLineCount"][r["product_line"] or "其他"] += 1

    sch = query("SELECT next_release_date,next_release_theme FROM schedule ORDER BY id DESC LIMIT 1", one=True)
    if sch:
        overview["nextReleaseDate"] = sch["next_release_date"] or ""
        overview["nextReleaseTheme"] = sch["next_release_theme"] or ""

    return ok({
        "groups": [{"date": d, "items": items} for d, items in sorted(groups.items(), reverse=True)],
        "overview": {
            "latestRelease": overview["latestRelease"],
            "last30Count": overview["last30Count"],
            "productLineCount": dict(overview["productLineCount"]),
            "nextReleaseDate": overview["nextReleaseDate"],
            "nextReleaseTheme": overview["nextReleaseTheme"],
        }
    })


@bp.route("/public/releases/<date>", methods=["GET"])
def public_release_by_date(date):
    """按通知日期返回已发布详情"""
    err = validate_date(date, "date")
    if err:
        return fail("INVALID_INPUT", err)
    rows = query(
        "SELECT * FROM items WHERE status='published' AND substr(notify_time,1,10)=? ORDER BY release_type",
        (date,)
    )
    if not rows:
        return fail("NOT_FOUND", f"未找到 {date} 的已发布内容", 404)
    return ok({"date": date, "items": [_row_to_public(r) for r in rows]})


@bp.route("/auth/login", methods=["POST"])
def auth_login():
    """模拟登录（MVP 不做密码校验）"""
    data = request.get_json(silent=True) or {}
    role = data.get("role", "").strip()
    username = (data.get("username") or "").strip()
    if role not in ("guest", "ops", "admin"):
        return fail("INVALID_INPUT", "角色不合法: guest/ops/admin")

    if role in ("ops", "admin") and not username:
        # 简单默认账号
        username = "admin" if role == "admin" else "wangrong"

    user_row = None
    if role in ("ops", "admin"):
        user_row = query("SELECT * FROM users WHERE username=? AND status='启用'", (username,), one=True)
        if not user_row:
            return fail("AUTH_FAILED", f"账号 {username} 不存在或已禁用", 401)

    if user_row:
        execute("UPDATE users SET last_login=datetime('now','localtime') WHERE id=?", (user_row["id"],))

    return ok({
        "role": role,
        "username": username,
        "realname": (user_row or {}).get("realname") or ("游客" if role == "guest" else role),
        "productLines": (user_row or {}).get("product_lines", ""),
    })
