"""
数据库初始化与连接
"""
import json
import os
import sqlite3
import threading

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.db")
_lock = threading.Lock()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query(sql, params=(), one=False):
    with _lock, get_conn() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows] if not one else (dict(rows[0]) if rows else None)


def execute(sql, params=()):
    with _lock, get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def execute_many(sql, seq):
    with _lock, get_conn() as conn:
        conn.executemany(sql, seq)
        conn.commit()


def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS product_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT '启用',
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        realname TEXT,
        password TEXT,
        role TEXT NOT NULL DEFAULT 'ops',
        product_lines TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT '启用',
        last_login TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS data_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT '钉钉文档',
        product_line TEXT,
        dingtalk_url TEXT,
        sync_freq TEXT NOT NULL DEFAULT '手动',
        enabled INTEGER NOT NULL DEFAULT 1,
        description TEXT,
        last_sync TEXT,
        total_rows INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_source_id INTEGER NOT NULL,
        sync_time TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        status TEXT NOT NULL,
        imported_rows INTEGER DEFAULT 0,
        message TEXT,
        FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module TEXT NOT NULL,
        release_date TEXT NOT NULL,
        platform_scope TEXT,
        app_platform TEXT NOT NULL,
        scope TEXT,
        release_type TEXT NOT NULL,
        feature_point TEXT NOT NULL,
        feature_entry TEXT,
        special_notes TEXT,
        limit_notes TEXT,
        notes TEXT,
        is_highlight TEXT,
        provide_material TEXT,
        remarks TEXT,
        target_user TEXT NOT NULL DEFAULT '全部',
        status TEXT NOT NULL DEFAULT 'imported',
        notify_time TEXT,
        import_time TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        product_line TEXT,
        created_by TEXT,
        updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS generated_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT NOT NULL,
        title TEXT,
        target_user TEXT,
        item_count INTEGER NOT NULL DEFAULT 0,
        file_path TEXT NOT NULL,
        data_url TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operator TEXT,
        action TEXT NOT NULL,
        target TEXT,
        message TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        next_release_date TEXT,
        next_release_theme TEXT,
        updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS import_progress (
        module_id TEXT PRIMARY KEY,
        last_import_date TEXT,
        last_import_time TEXT,
        last_imported_count INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS item_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        url TEXT NOT NULL,
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS target_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_row_no INTEGER NOT NULL,
        scene TEXT NOT NULL,
        link TEXT,
        func TEXT,
        demand TEXT NOT NULL,
        level TEXT,
        biz TEXT,
        current_state TEXT,
        meet_status TEXT,
        follow_up TEXT,
        planned_at TEXT,
        status TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE INDEX IF NOT EXISTS idx_items_module ON items(module);
    CREATE INDEX IF NOT EXISTS idx_items_release_date ON items(release_date);
    CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
    CREATE INDEX IF NOT EXISTS idx_item_images_item ON item_images(item_id);
    CREATE INDEX IF NOT EXISTS idx_target_map_scene ON target_map(scene);
    """
    with _lock, get_conn() as conn:
        conn.executescript(schema)
        conn.commit()

    # 种子数据（首次启动时）
    seed_if_empty()
    seed_target_map_if_empty()


def seed_if_empty():
    # 仅当 items 表为空时才认为是全新初始化
    if query("SELECT id FROM items LIMIT 1", one=True):
        return
    # 产品线
    plist = [
        ("wd-homework", "闻道作业", "启用"),
        ("live-teach", "直播教学", "启用"),
        ("open-school", "开放学校", "启用"),
    ]
    for code, name, status in plist:
        if not query("SELECT id FROM product_lines WHERE code=?", (code,), one=True):
            execute("INSERT INTO product_lines(code,name,status) VALUES (?,?,?)", (code, name, status))

    # 用户（product_lines 使用产品线名称，便于前后端联动）
    users = [
        ("admin", "付羽淇", "admin", "全产品线", "启用"),
        ("wangrong", "王蓉", "ops", "闻道作业", "启用"),
        ("zhangying", "张颖", "ops", "直播教学", "启用"),
        ("yuting", "余婷", "ops", "开放学校", "启用"),
    ]
    for u, n, r, pl, s in users:
        if not query("SELECT id FROM users WHERE username=?", (u,), one=True):
            execute("INSERT INTO users(username,realname,role,product_lines,status) VALUES (?,?,?,?,?)", (u, n, r, pl, s))

    # 数据源
    sources = [
        ("base", "底座", "底座发布清单", "wd-homework", "https://alidocs.dingtalk.com/i/nodes/o14dA3GK8g55wx5KU515Ad99V9ekBD76", 113, "底座能力发版"),
        ("resource", "资源应用", "资源应用发布清单", "wd-homework", "https://alidocs.dingtalk.com/i/nodes/YMyQA2dXW799zB9lS9NejgBZJzlwrZgb", 280, "闻道资源平台等发版"),
    ]
    for mid, name, doc, pl, url, total, desc in sources:
        if not query("SELECT id FROM data_sources WHERE module_id=?", (mid,), one=True):
            execute("""INSERT INTO data_sources(module_id,name,product_line,dingtalk_url,total_rows,description,last_sync)
                       VALUES (?,?,?,?,?,?,?)""", (mid, name, pl, url, total, desc, "2026-07-12 15:24"))

    # 排期
    if not query("SELECT id FROM schedule", one=True):
        execute("INSERT INTO schedule(next_release_date,next_release_theme) VALUES (?,?)", ("2026-07-15", "V3.7 暑期升级"))

    # 初始 items（字段顺序：module, release_date, product_line, app_platform, scope, release_type, feature_point, feature_entry, target_user, status, notify_time）
    items = [
        ("base",     "2026-07-08", "闻道作业", "试题列表",       "web",   "修复", "章节树偶发空白问题",                                                   "课程-章节",                          "全部", "published", "2026-07-08T10:00"),
        ("base",     "2026-07-08", "闻道作业", "运营后台",       "App",   "新增", "运营后台 MVP 上线",                                                    "—",                                 "全部", "published", "2026-07-08T10:00"),
        ("resource", "2026-07-05", "直播教学", "直播连麦",       "App",   "优化", "直播连麦稳定性优化",                                                   "课堂-连麦",                          "全部", "published", "2026-07-05T10:00"),
        ("base",     "2026-07-01", "闻道作业", "作业批改",       "App",   "新增", "V3.6 月度迭代",                                                        "作业-批改 / 练习-错题本",          "作业", "published", "2026-07-01T10:00"),
        ("base",     "2026-06-25", "底座",     "建设中心-试题编辑", "web",   "修复", "修复题干区选中内容标记作答，复制粘贴到非题干区，非题干区仍然存在标记作答的样式", "试题编辑",                          "全部", "published", "2026-06-25T10:00"),
        ("base",     "2026-06-25", "底座",     "建设中心-试题编辑", "web",   "修复", "修复编辑器中对已存在的田字格复制粘贴后，操作某一个田字格会影响到复制粘贴的田字格",     "试题编辑",                          "全部", "published", "2026-06-25T10:00"),
        ("base",     "2026-06-25", "底座",     "管理平台",       "web",   "优化", "数据库从微软云迁移到阿里云",                                          "首页登录",                          "全部", "published", "2026-06-25T10:00"),
        ("resource", "2026-06-25", "资源应用", "教辅作业-试题详情", "web",   "新增", "支持点击试题题号板块（小程序）或讲解按钮（web端）查看教师讲解",     "教辅作业-试题详情",                "教辅", "published", "2026-06-25T10:00"),
        ("resource", "2026-06-25", "资源应用", "教辅作业-讲解",   "web",   "新增", "教辅作业支持进入讲评页面，对单题进行讲解",                          "教辅作业-讲解",                    "教辅", "published", "2026-06-25T10:00"),
        ("resource", "2026-06-25", "资源应用", "教辅作业-识别异常", "web",  "新增", "支持批量处理「识别异常」数据",                                       "教辅作业-识别异常",                "教辅", "published", "2026-06-25T10:00"),
        ("resource", "2026-06-25", "资源应用", "钉钉通知",       "钉钉",  "优化", "作业提交通知中隐藏发布者的姓（第一个字）",                          "钉钉通知",                          "全部", "published", "2026-06-25T10:00"),
        ("resource", "2026-06-25", "资源应用", "答题卡",         "web",   "优化", "英文作文智能批阅的大模型由国外模型更换为国内模型",                  "测验-英语作文智能批阅",            "作业", "published", "2026-06-25T10:00"),
        ("resource", "2026-06-25", "资源应用", "教辅作业",       "web",   "修复", "教辅提交作答时，钉钉发通知提交了某个章节，但进入教辅作业模块，该章节无提交数据", "教辅作业",                            "教辅", "published", "2026-06-25T10:00"),
    ]
    for it in items:
        execute("""INSERT INTO items(module,release_date,product_line,app_platform,scope,release_type,feature_point,feature_entry,target_user,status,notify_time)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""", it)


def reset_all(operator="system", reason="手动重置"):
    """
    清空所有业务数据并重新种子化（保留表结构、字典数据）。
    返回 { "deletedCounts": {...}, "seededCounts": {...}, "resetRecord": {...} }
    调用前会写入 audit_logs 作为可追溯记录。
    """
    # 1) 写审计（在删之前记）
    reset_at = _now_str()
    execute("INSERT INTO audit_logs(operator,action,target,message) VALUES (?,?,?,?)",
            (operator, "reset", "items,users,data_sources,sync_logs,audit_logs,generated_images",
             f"重置原因: {reason}"))

    # 2) 统计清空前数量
    before = {
        "items": query("SELECT COUNT(*) c FROM items", one=True)["c"],
        "users": query("SELECT COUNT(*) c FROM users", one=True)["c"],
        "data_sources": query("SELECT COUNT(*) c FROM data_sources", one=True)["c"],
        "sync_logs": query("SELECT COUNT(*) c FROM sync_logs", one=True)["c"],
        "audit_logs": query("SELECT COUNT(*) c FROM audit_logs", one=True)["c"],
        "generated_images": query("SELECT COUNT(*) c FROM generated_images", one=True)["c"],
    }
    # 先取出刚写入的 reset 记录，避免被清掉
    last_reset = query("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 1", one=True)

    # 3) 清空（包含 product_lines 字典，seed 会重建）
    for table in ("generated_images", "audit_logs", "sync_logs", "items", "data_sources", "users", "product_lines"):
        execute(f"DELETE FROM {table}")
        execute(f"DELETE FROM sqlite_sequence WHERE name=?", (table,))

    # 4) 重新种子化
    seed_if_empty()

    # 5) 把 reset 记录追加回去（保证可追溯）
    if last_reset:
        execute("INSERT INTO audit_logs(operator,action,target,message,created_at) VALUES (?,?,?,?,?)",
                (last_reset["operator"], last_reset["action"], last_reset["target"],
                 last_reset["message"], reset_at))

    after = {
        "items": query("SELECT COUNT(*) c FROM items", one=True)["c"],
        "users": query("SELECT COUNT(*) c FROM users", one=True)["c"],
        "data_sources": query("SELECT COUNT(*) c FROM data_sources", one=True)["c"],
    }
    return {
        "deletedCounts": before,
        "seededCounts": after,
        "resetRecord": {
            "operator": operator, "reason": reason, "resetAt": reset_at,
            "id": last_reset["id"] if last_reset else None,
        }
    }


def _now_str():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def seed_target_map_if_empty():
    """从 backend/data/target_map_seed.json 灌入目标地图数据，仅在表为空时执行。"""
    if query("SELECT id FROM target_map LIMIT 1", one=True):
        return
    seed_path = os.path.join(os.path.dirname(__file__), "data", "target_map_seed.json")
    if not os.path.isfile(seed_path):
        return
    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            rows = json.load(f)
    except (OSError, ValueError) as e:
        print(f"[seed_target_map] 读取种子失败: {e}")
        return
    if not rows:
        return
    seq = [
        (r["source_row_no"], r["scene"], r["link"], r["func"], r["demand"],
         r["level"], r["biz"], r["current_state"], r["meet_status"],
         r["follow_up"], r["planned_at"], r["status"])
        for r in rows
    ]
    execute_many(
        """INSERT INTO target_map
           (source_row_no, scene, link, func, demand, level, biz,
            current_state, meet_status, follow_up, planned_at, status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        seq,
    )
    print(f"[seed_target_map] 已灌入 {len(seq)} 条目标地图数据")
