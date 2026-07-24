"""
运营后台 API（ops.html 使用）
"""
import os
import random
import re
import time
from collections import defaultdict
from flask import Blueprint, request

from backend.db import query, execute, query as run_query
from backend.utils import ok, fail, validate_required, validate_enum, validate_date, validate_datetime, VALID_RELEASES_TYPE, VALID_TARGET_USER, VALID_SCOPE, VALID_STATUS


# 多值字段分隔符（前端以「、」提交，兼容英文逗号）
MULTI_SEP_RE = re.compile(r"[、,]")


def _normalize_multi(value, allowed, field):
    """多值字段标准化：拆分 + 逐值校验 + 去空去重 + 用「、」拼接。返回 (normalized, error)"""
    if value is None or value == "":
        return "", None
    if isinstance(value, list):
        parts = value
    else:
        parts = MULTI_SEP_RE.split(str(value))
    cleaned = []
    seen = set()
    for p in parts:
        v = p.strip()
        if not v or v in seen:
            continue
        seen.add(v)
        cleaned.append(v)
    for v in cleaned:
        if allowed and v not in allowed:
            return None, f"{field} 取值「{v}」不合法，允许: {', '.join(sorted(allowed))}"
    return "、".join(cleaned), None

bp = Blueprint("items", __name__)


def _row_to_dict(r):
    module = r["module"]
    data_source_map = {"base": "底座", "resource": "资源应用"}
    img_rows = query(
        "SELECT id, file_path, url, sort_order FROM item_images WHERE item_id=? ORDER BY sort_order, id",
        (r["id"],),
    )
    return {
        "id": r["id"],
        "module": module,
        "dataSource": data_source_map.get(module, module),
        "releaseDate": r["release_date"],
        "platformScope": r["platform_scope"],
        "appPlatform": r["app_platform"],
        "scope": r["scope"],
        "releaseType": r["release_type"],
        "featurePoint": r["feature_point"],
        "featureEntry": r["feature_entry"],
        "specialNotes": r["special_notes"],
        "limitNotes": r["limit_notes"],
        "notes": r["notes"],
        "isHighlight": r["is_highlight"],
        "provideMaterial": r["provide_material"],
        "remarks": r["remarks"],
        "targetUser": r["target_user"],
        "status": r["status"],
        "notifyTime": r["notify_time"],
        "importTime": r["import_time"],
        "productLine": r["product_line"],
        "images": len(img_rows),
        "imageList": [
            {"id": ir["id"], "url": ir["url"], "path": ir["file_path"], "sortOrder": ir["sort_order"]}
            for ir in img_rows
        ],
    }


def _save_item_images(item_id, image_list):
    """全删全插 item_images 关联。image_list 形如 [{path,url,sort_order}, ...]"""
    execute("DELETE FROM item_images WHERE item_id=?", (item_id,))
    for idx, im in enumerate(image_list or []):
        path = (im.get("path") or im.get("file_path") or "").strip()
        url = (im.get("url") or "").strip() or (f"/uploads/{os.path.basename(path)}" if path else "")
        if not path:
            continue
        sort_order = int(im.get("sort_order", im.get("sortOrder", idx)) or idx)
        execute(
            "INSERT INTO item_images(item_id, file_path, url, sort_order) VALUES (?,?,?,?)",
            (item_id, path, url, sort_order),
        )


# ============ 列表与详情 ============

@bp.route("/items", methods=["GET"])
def list_items():
    """运营后台发版列表"""
    module = request.args.get("module")
    status = request.args.get("status")
    start = request.args.get("start")
    end = request.args.get("end")
    keyword = request.args.get("keyword")

    # 筛选参数（发版列表页面用，单日匹配）
    release_date = request.args.get("releaseDate")
    notify_date = request.args.get("notifyDate")
    data_source = request.args.get("dataSource")
    # 兜底视图用：按产品线精确匹配
    product_line = request.args.get("productLine")
    # 兜底视图用：通知状态（notified=已通知 / unnotified=未通知），映射 notify_time 是否为空
    notify_status = (request.args.get("notifyStatus") or "").strip()
    # 兼容旧 List 后缀（getlist 方式）；新规范直接用逗号分隔
    release_types = request.args.getlist("releaseTypeList") or (request.args.get("releaseType", "").split(",") if "," in (request.args.get("releaseType") or "") else ([request.args["releaseType"]] if request.args.get("releaseType") else []))
    target_users = request.args.getlist("targetUserList") or (request.args.get("targetUser", "").split(",") if "," in (request.args.get("targetUser") or "") else ([request.args["targetUser"]] if request.args.get("targetUser") else []))

    sql = "SELECT * FROM items WHERE 1=1"
    params = []
    if module:
        sql += " AND module = ?"
        params.append(module)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if start:
        sql += " AND notify_time >= ?"
        params.append(start + "T00:00")
    if end:
        sql += " AND notify_time <= ?"
        params.append(end + "T23:59")
    if release_date:
        sql += " AND release_date = ?"
        params.append(release_date)
    if notify_date:
        sql += " AND notify_time >= ? AND notify_time <= ?"
        params.append(notify_date + "T00:00")
        params.append(notify_date + "T23:59")
    if data_source:
        sources = [s.strip() for s in data_source.split(",") if s.strip()]
        if sources:
            placeholders = ",".join("?" * len(sources))
            sql += f" AND module IN ({placeholders})"
            params.extend(sources)
    if product_line:
        sql += " AND product_line = ?"
        params.append(product_line)
    if notify_status == "notified":
        sql += " AND notify_time IS NOT NULL AND notify_time != ''"
    elif notify_status == "unnotified":
        sql += " AND (notify_time IS NULL OR notify_time = '')"
    if release_types:
        # 去空 + 保留顺序
        seen = set(); cleaned = []
        for v in release_types:
            v = v.strip()
            if v and v not in seen:
                seen.add(v); cleaned.append(v)
        if cleaned:
            placeholders = ",".join("?" * len(cleaned))
            sql += f" AND release_type IN ({placeholders})"
            params.extend(cleaned)
    if target_users:
        seen = set(); cleaned = []
        for v in target_users:
            v = v.strip()
            if v and v not in seen:
                seen.add(v); cleaned.append(v)
        if cleaned:
            # 多值字段：用 LIKE 包含任一值（OR 语义）
            or_parts = " OR ".join(["target_user LIKE ?" for _ in cleaned])
            sql += f" AND ({or_parts})"
            params.extend([f"%{v}%" for v in cleaned])
    if keyword:
        sql += " AND (feature_point LIKE ? OR feature_entry LIKE ? OR app_platform LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])
    sql += " ORDER BY release_date DESC, release_type ASC, id DESC"
    rows = query(sql, tuple(params))
    return ok([_row_to_dict(r) for r in rows])


@bp.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    row = query("SELECT * FROM items WHERE id=?", (item_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"发版记录 {item_id} 不存在", 404)
    return ok(_row_to_dict(row))


# ============ 创建/更新/删除 ============

@bp.route("/items", methods=["POST"])
def create_item():
    data = request.get_json(silent=True) or {}
    err = validate_required(data, ["appPlatform", "featurePoint", "releaseDate", "releaseType"])
    if err:
        return fail("INVALID_INPUT", err)
    err = validate_date(data["releaseDate"], "releaseDate")
    if err:
        return fail("INVALID_INPUT", err)
    err = validate_enum(data["releaseType"], VALID_RELEASES_TYPE, "releaseType")
    if err:
        return fail("INVALID_INPUT", err)
    # 多值字段：targetUser、scope（前端以「、」分隔，兼容英文逗号）
    target_user, err = _normalize_multi(data.get("targetUser", "全部"), VALID_TARGET_USER, "targetUser")
    if err:
        return fail("INVALID_INPUT", err)
    if not target_user:
        target_user = "全部"
    scope, err = _normalize_multi(data.get("scope", ""), VALID_SCOPE, "scope")
    if err:
        return fail("INVALID_INPUT", err)

    # 通知日期由 publish 流程自动写入,创建/编辑时不再处理
    notify_time = ""  # 始终为空,需走 /publish 单独接口
    status = "edited"  # 默认草稿状态

    new_id = execute(
        """INSERT INTO items(module,release_date,platform_scope,app_platform,scope,release_type,
           feature_point,feature_entry,special_notes,limit_notes,notes,is_highlight,
           provide_material,remarks,target_user,status,notify_time,product_line)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data.get("module", "base"),
            data["releaseDate"],
            data.get("platformScope", ""),
            data["appPlatform"].strip(),
            scope or "App",
            data["releaseType"],
            data["featurePoint"].strip(),
            (data.get("featureEntry") or "").strip(),
            (data.get("specialNotes") or "").strip(),
            (data.get("limitNotes") or "").strip(),
            (data.get("notes") or "").strip(),
            data.get("isHighlight", "否"),
            (data.get("provideMaterial") or "").strip(),
            (data.get("remarks") or "").strip(),
            target_user,
            status,
            notify_time,
            data.get("productLine", "闻道作业"),
        )
    )
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            (data.get("operator") or "ops", "create", f"item:{new_id}", f"新建发版 {data['featurePoint'][:30]}"))
    _save_item_images(new_id, data.get("imageList") or [])
    row = query("SELECT * FROM items WHERE id=?", (new_id,), one=True)
    return ok(_row_to_dict(row), message="创建成功", status=201)


@bp.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    row = query("SELECT * FROM items WHERE id=?", (item_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"发版记录 {item_id} 不存在", 404)
    data = request.get_json(silent=True) or {}

    err = validate_date(data.get("releaseDate", row["release_date"]), "releaseDate")
    if err:
        return fail("INVALID_INPUT", err)
    if data.get("releaseType"):
        err = validate_enum(data["releaseType"], VALID_RELEASES_TYPE, "releaseType")
        if err:
            return fail("INVALID_INPUT", err)
    # 多值字段校验
    if "targetUser" in data:
        target_user, err = _normalize_multi(data.get("targetUser") or "", VALID_TARGET_USER, "targetUser")
        if err:
            return fail("INVALID_INPUT", err)
        if not target_user:
            target_user = row["target_user"] or "全部"
    else:
        target_user = row["target_user"]
    if "scope" in data:
        scope, err = _normalize_multi(data.get("scope") or "", VALID_SCOPE, "scope")
        if err:
            return fail("INVALID_INPUT", err)
        if not scope:
            scope = row["scope"] or "App"
    else:
        scope = row["scope"]

    # 通知日期由 publish 流程自动写入,update 不再覆盖
    notify_time = row["notify_time"] or ""  # 始终保留原 notify_time

    new_status = data.get("status") or row["status"]  # 默认保持原状态

    execute(
        """UPDATE items SET module=?,release_date=?,platform_scope=?,app_platform=?,scope=?,release_type=?,
           feature_point=?,feature_entry=?,special_notes=?,limit_notes=?,notes=?,is_highlight=?,
           provide_material=?,remarks=?,target_user=?,status=?,notify_time=?,product_line=?,
           updated_at=datetime('now','localtime') WHERE id=?""",
        (
            data.get("module", row["module"]),
            data.get("releaseDate", row["release_date"]),
            data.get("platformScope", row["platform_scope"] or ""),
            (data.get("appPlatform") or row["app_platform"]).strip(),
            scope,
            data.get("releaseType", row["release_type"]),
            (data.get("featurePoint") or row["feature_point"]).strip(),
            (data.get("featureEntry") or row["feature_entry"] or "").strip(),
            (data.get("specialNotes") or row["special_notes"] or "").strip(),
            (data.get("limitNotes") or row["limit_notes"] or "").strip(),
            (data.get("notes") or row["notes"] or "").strip(),
            data.get("isHighlight", row["is_highlight"] or "否"),
            (data.get("provideMaterial") or row["provide_material"] or "").strip(),
            (data.get("remarks") or row["remarks"] or "").strip(),
            target_user,
            new_status,
            notify_time,
            data.get("productLine", row["product_line"] or "闻道作业"),
            item_id,
        )
    )
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            (data.get("operator") or "ops", "update", f"item:{item_id}", f"更新发版 {row['feature_point'][:30]}"))
    if "imageList" in data:
        _save_item_images(item_id, data.get("imageList") or [])
    new_row = query("SELECT * FROM items WHERE id=?", (item_id,), one=True)
    return ok(_row_to_dict(new_row), message="更新成功")


@bp.route("/items/<int:item_id>/publish", methods=["POST"])
def publish_item(item_id):
    """发布单条：若已通知（notify_time 非空）则跳过；否则用今天日期记录（首次通知）。"""
    row = query("SELECT * FROM items WHERE id=?", (item_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"发版记录 {item_id} 不存在", 404)
    if row["notify_time"]:
        # 已通知过,跳过,直接返回当前数据
        return ok(_row_to_dict(row), message="已通知过,无需重复发布")
    # 用今天日期 (yyyy/MM/dd)
    from datetime import datetime
    today = datetime.now().strftime("%Y/%m/%d")
    execute("UPDATE items SET status='published', notify_time=?, updated_at=datetime('now','localtime') WHERE id=?",
            (today, item_id))
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("ops", "publish", f"item:{item_id}", f"发布发版 {row['feature_point'][:30]}"))
    new_row = query("SELECT * FROM items WHERE id=?", (item_id,), one=True)
    return ok(_row_to_dict(new_row), message="发布成功")


@bp.route("/items/batch-publish", methods=["POST"])
def batch_publish_items():
    """批量发布：接 { ids: [int, ...] }，对每条若已通知则跳过，否则用今天日期发布。返回 { published: [...], skipped: [...], today }"""
    from datetime import datetime
    today = datetime.now().strftime("%Y/%m/%d")
    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or []
    if not isinstance(ids, list) or not ids:
        return fail("INVALID_INPUT", "ids 必须是非空数组")
    ids = [int(i) for i in ids if str(i).isdigit()]
    if not ids:
        return fail("INVALID_INPUT", "ids 数组内没有有效 id")

    published, skipped, not_found = [], [], []
    for item_id in ids:
        row = query("SELECT * FROM items WHERE id=?", (item_id,), one=True)
        if not row:
            not_found.append(item_id)
            continue
        if row["notify_time"]:
            skipped.append({"id": item_id, "notifyTime": row["notify_time"]})
            continue
        execute("UPDATE items SET status='published', notify_time=?, updated_at=datetime('now','localtime') WHERE id=?",
                (today, item_id))
        execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
                ("ops", "batch-publish", f"item:{item_id}", f"批量发布发版 {row['feature_point'][:30]}"))
        published.append({"id": item_id, "notifyTime": today})
    return ok({
        "today": today,
        "published": published,
        "skipped": skipped,
        "notFound": not_found,
    }, message=f"已发布 {len(published)} 条,跳过 {len(skipped)} 条已通知")


@bp.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    row = query("SELECT * FROM items WHERE id=?", (item_id,), one=True)
    if not row:
        return fail("NOT_FOUND", f"发版记录 {item_id} 不存在", 404)
    execute("DELETE FROM items WHERE id=?", (item_id,))
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            ("admin", "delete", f"item:{item_id}", f"删除发版 {row['feature_point'][:30]}"))
    return ok(message="删除成功")


# ============ 导入发布清单 ============

@bp.route("/import/<module_id>", methods=["POST"])
def import_release_list(module_id):
    """
    模拟从钉钉文档拉取发布清单。
    实际场景下这里会调用钉钉 OpenAPI；MVP 阶段基于已有种子数据做模拟。
    """
    if module_id not in ("base", "resource"):
        return fail("INVALID_INPUT", f"模块 {module_id} 不存在", 404)

    source = query("SELECT * FROM data_sources WHERE module_id=?", (module_id,), one=True)
    if not source:
        return fail("NOT_FOUND", f"数据源 {module_id} 未配置", 404)
    if not source["enabled"]:
        return fail("DATA_SOURCE_DISABLED", f"数据源 {source['name']} 已禁用，请先启用", 400)

    # 模拟网络延迟与偶发失败
    force_refresh = (request.get_json(silent=True) or {}).get("force", False)
    if not force_refresh and random.random() < 0.08:
        time.sleep(0.3)
        execute("INSERT INTO sync_logs(data_source_id,status,message) VALUES (?,?,?)",
                (source["id"], "失败", "网络请求超时（模拟）"))
        return fail("IMPORT_TIMEOUT", "钉钉文档拉取超时，请重试", 504)

    # 增量导入模式：仅导入 release_date > last_import_date 的数据
    progress = query("SELECT * FROM import_progress WHERE module_id=?", (module_id,), one=True)
    last_import_date = (progress or {}).get("last_import_date")
    mode = "incremental" if last_import_date else "full"

    # 从内置样本数据中取子集作为"拉取结果"
    seed_rows = _seed_source_data(module_id)
    if mode == "incremental":
        seed_rows = [r for r in seed_rows if r["releaseDate"] > last_import_date]

    added = 0
    skipped = 0
    skipped_rows = []
    max_imported_date = last_import_date or ""
    for r in seed_rows:
        # 跳过已存在（按 module + releaseDate + featurePoint 判定）
        exists = query(
            "SELECT id FROM items WHERE module=? AND release_date=? AND feature_point=?",
            (module_id, r["releaseDate"], r["featurePoint"]), one=True
        )
        if exists:
            skipped += 1
            skipped_rows.append(r["featurePoint"][:30])
            continue
        execute(
            """INSERT INTO items(module,release_date,platform_scope,app_platform,scope,release_type,
               feature_point,feature_entry,special_notes,limit_notes,notes,is_highlight,
               provide_material,remarks,target_user,status,notify_time,product_line,import_time)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))""",
            (
                module_id, r["releaseDate"], r.get("platformScope", ""), r["appPlatform"], r.get("scope", "App"),
                r["releaseType"], r["featurePoint"], r.get("featureEntry", ""), r.get("specialNotes", ""),
                r.get("limitNotes", ""), r.get("notes", ""), r.get("isHighlight", ""), r.get("provideMaterial", ""),
                r.get("remarks", ""), r.get("targetUser", "全部"), "imported", "",
                r.get("productLine", "闻道作业"),
            )
        )
        added += 1
        if not max_imported_date or r["releaseDate"] > max_imported_date:
            max_imported_date = r["releaseDate"]

    # 更新进度：只有真正追加了数据才推进 last_import_date
    if added > 0 and max_imported_date:
        if progress:
            execute("""UPDATE import_progress SET last_import_date=?, last_import_time=datetime('now','localtime'),
                        last_imported_count=last_imported_count+? WHERE module_id=?""",
                    (max_imported_date, added, module_id))
        else:
            execute("""INSERT INTO import_progress(module_id,last_import_date,last_import_time,last_imported_count)
                        VALUES (?,?,datetime('now','localtime'),?)""",
                    (module_id, max_imported_date, added))

    execute("UPDATE data_sources SET last_sync=datetime('now','localtime') WHERE id=?", (source["id"],))
    log_msg = f"导入 {added} 条，跳过 {skipped} 条重复"
    if mode == "incremental":
        log_msg = f"[增量 自 {last_import_date}] {log_msg}"
    else:
        log_msg = f"[全量] {log_msg}"
    execute("INSERT INTO sync_logs(data_source_id,status,imported_rows,message) VALUES (?,?,?,?)",
            (source["id"], "成功", added, log_msg))
    return ok({
        "module": module_id,
        "mode": mode,
        "lastImportDate": last_import_date or "",
        "added": added,
        "skipped": skipped,
        "skippedRows": skipped_rows,
        "lastSync": "now",
    }, message=f"导入完成，新增 {added} 条" + (f"（增量，自 {last_import_date}）" if mode == "incremental" else "（全量）"))


@bp.route("/import/<module_id>/progress", methods=["GET"])
def import_progress(module_id):
    """查询某模块上次导入进度（last_import_date / time / count）"""
    if module_id not in ("base", "resource"):
        return fail("INVALID_INPUT", f"模块 {module_id} 不存在", 404)
    row = query("SELECT * FROM import_progress WHERE module_id=?", (module_id,), one=True)
    return ok({
        "module": module_id,
        "lastImportDate": (row or {}).get("last_import_date") or "",
        "lastImportTime": (row or {}).get("last_import_time") or "",
        "lastImportedCount": (row or {}).get("last_imported_count") or 0,
    })


def _seed_source_data(module_id):
    """与 app.js 中样本数据保持一致"""
    base = [
        {"releaseDate": "2026-07-09", "appPlatform": "试题列表", "scope": "web", "releaseType": "修复",
         "featurePoint": "修复题干区选中内容标记作答，复制粘贴到非题干区，非题干区仍然存在标记作答的样式的问题",
         "featureEntry": "试题编辑", "targetUser": "全部"},
        {"releaseDate": "2026-07-09", "appPlatform": "试题列表", "scope": "web", "releaseType": "修复",
         "featurePoint": "修复编辑器中对已存在的田字格复制粘贴后，操作某一个田字格会影响到复制粘贴的田字格的问题",
         "featureEntry": "试题编辑", "targetUser": "全部"},
        {"releaseDate": "2026-06-25", "appPlatform": "管理平台", "scope": "web", "releaseType": "优化",
         "featurePoint": "微软云相关依赖移除-用户头像上传、显示功能正常", "featureEntry": "教师管理/学生管理-编辑",
         "targetUser": "全部"},
        {"releaseDate": "2026-06-11", "appPlatform": "管理平台", "scope": "web", "releaseType": "优化",
         "featurePoint": "数据库从微软云迁移到阿里云", "featureEntry": "首页登录", "targetUser": "全部"},
        {"releaseDate": "2026-05-28", "appPlatform": "认证中心", "scope": "全部", "releaseType": "优化",
         "featurePoint": "敏感词扫描不再进行底层资源仓库的扫描，仅进行各个信息录入端口的扫描", "featureEntry": "底层资源库",
         "targetUser": "全部"},
    ]
    resource = [
        {"releaseDate": "2026-07-09", "appPlatform": "作业-钉钉提交通知", "scope": "钉钉", "releaseType": "优化",
         "featurePoint": "作业提交通知中提及王蓉（依赖于王蓉给的手机号是否正确）", "featureEntry": "钉钉通知",
         "targetUser": "全部"},
        {"releaseDate": "2026-07-09", "appPlatform": "测验", "scope": "web", "releaseType": "优化",
         "featurePoint": "优化客观题的几个易错选项的识别（存在易错选项时，根据试题现有范围进行识别）",
         "featureEntry": "测验-答题卡练习-客观题识别", "targetUser": "作业"},
        {"releaseDate": "2026-07-01", "appPlatform": "班级错题", "scope": "web", "releaseType": "优化",
         "featurePoint": "错题再练，查找并找出试题后支持在下方呈现已选中的试题", "featureEntry": "班级错题-错题再练",
         "targetUser": "作业"},
        {"releaseDate": "2026-06-18", "appPlatform": "闻道微课web", "scope": "web", "releaseType": "优化",
         "featurePoint": "屏蔽AI对话框入口", "featureEntry": "闻道资源平台", "targetUser": "全部"},
    ]
    return base if module_id == "base" else resource


# ============ 统计 ============

@bp.route("/stats", methods=["GET"])
def stats():
    module = request.args.get("module")
    sql_base = "FROM items WHERE 1=1"
    params = []
    if module:
        sql_base += " AND module=?"
        params.append(module)

    total = query("SELECT COUNT(*) c " + sql_base, tuple(params), one=True)["c"]
    by_type = {row["release_type"]: row["c"] for row in query("SELECT release_type, COUNT(*) c " + sql_base + " GROUP BY release_type", tuple(params))}
    # by_target：按单值聚合（多值字段按 LIKE 计入每个匹配的目标）
    by_target = {k: 0 for k in VALID_TARGET_USER}
    for target in VALID_TARGET_USER:
        cnt = query("SELECT COUNT(*) c " + sql_base + " AND target_user LIKE ?", tuple(params + [f"%{target}%"]), one=True)["c"]
        by_target[target] = cnt
    published = query("SELECT COUNT(*) c " + sql_base + " AND status='published'", tuple(params), one=True)["c"]
    draft = total - published
    highlight = query("SELECT COUNT(*) c " + sql_base + " AND is_highlight='是'", tuple(params), one=True)["c"]

    return ok({
        "total": total,
        "published": published,
        "draft": draft,
        "highlight": highlight,
        "byType": by_type,
        "byTarget": by_target,
    })


@bp.route("/releases/<date>", methods=["GET"])
def releases_by_date(date):
    """按通知日期返回已发布功能点（公开/运营详情通用）"""
    err = validate_date(date, "date")
    if err:
        return fail("INVALID_INPUT", err)
    rows = query(
        "SELECT * FROM items WHERE status='published' AND substr(notify_time,1,10)=? ORDER BY release_type",
        (date,)
    )
    return ok({"date": date, "items": [_row_to_dict(r) for r in rows]})


@bp.route("/schedule", methods=["GET"])
def get_schedule():
    row = query("SELECT * FROM schedule ORDER BY id DESC LIMIT 1", one=True)
    return ok(row or {"next_release_date": "", "next_release_theme": ""})


@bp.route("/schedule", methods=["PUT"])
def update_schedule():
    data = request.get_json(silent=True) or {}
    date = data.get("nextReleaseDate") or ""
    theme = data.get("nextReleaseTheme") or ""
    err = validate_date(date, "nextReleaseDate") if date else None
    if err:
        return fail("INVALID_INPUT", err)
    execute("UPDATE schedule SET next_release_date=?, next_release_theme=?, updated_at=datetime('now','localtime') WHERE id=(SELECT MAX(id) FROM schedule)", (date, theme))
    row = query("SELECT * FROM schedule ORDER BY id DESC LIMIT 1", one=True)
    return ok(row)
