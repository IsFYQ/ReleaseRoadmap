"""
图片生成与上传 API
"""
import os
import io
import time
from datetime import datetime
from flask import Blueprint, request, send_file, current_app
from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET

from backend.db import query, execute
from backend.utils import ok, fail, validate_enum

bp = Blueprint("images", __name__)

ALLOWED_VERSIONS = {"all", "homework", "teaching"}
ALLOWED_TARGET = {"全部", "作业", "教辅"}
VERSION_TO_TARGET = {"all": "全部", "homework": "作业", "teaching": "教辅"}
VERSION_TO_TITLE = {"all": "总图", "homework": "仅作业", "teaching": "仅教辅"}


def _filter_items(version):
    rows = query("SELECT * FROM items WHERE status='published' AND notify_time IS NOT NULL")
    if version == "all":
        return rows
    target = VERSION_TO_TARGET[version]
    # 多值 target_user：包含目标值 或 包含"全部"都视为命中
    return [r for r in rows if target in (r["target_user"] or "") or "全部" in (r["target_user"] or "")]


def _build_svg(version, title, target, rows):
    width = 600
    item_h = 86
    header_h = 90
    footer_h = 50
    height = max(260, header_h + len(rows) * item_h + footer_h)
    today = datetime.now().strftime("%Y-%m-%d")

    parts = [f'<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    parts.append(f'<rect width="{width}" height="{height}" fill="#F5F6FA"/>')
    parts.append(f'<rect x="0" y="0" width="{width}" height="80" fill="#5B6CFF"/>')
    parts.append(f'<text x="40" y="46" font-size="22" fill="#fff" font-weight="600">闻道作业 · {title}</text>')
    parts.append(f'<text x="40" y="72" font-size="12" fill="#CFD3FF">{today} · 共 {len(rows)} 项功能 · 面向用户：{target}</text>')

    y = 100
    for r in rows:
        parts.append(f'<rect x="20" y="{y}" width="560" height="{item_h - 6}" rx="8" fill="#FAFBFD" stroke="#E6E8EF"/>')
        color = {"新增": "#2BB673", "优化": "#3D8EE0", "修复": "#E89B2A", "删除": "#E25555"}.get(r["release_type"], "#5B6CFF")
        parts.append(f'<rect x="32" y="{y + 12}" width="60" height="20" rx="4" fill="{color}"/>')
        parts.append(f'<text x="62" y="{y + 26}" font-size="12" fill="#fff" font-weight="600" text-anchor="middle">{_xml(r["release_type"])}</text>')
        parts.append(f'<text x="104" y="{y + 26}" font-size="14" fill="#1F2330" font-weight="600">{_truncate(_xml(r["feature_point"]), 30)}</text>')
        parts.append(f'<text x="40" y="{y + 52}" font-size="12" fill="#5A6172">入口：{_truncate(_xml(r["feature_entry"] or ""), 30)} · 面向用户：{_xml(r["target_user"])}</text>')
        y += item_h

    parts.append(f'<text x="40" y="{height - 20}" font-size="11" fill="#9098AC">发版路线图系统自动生成 · 闻道作业</text>')
    parts.append("</svg>")
    return "".join(parts)


def _truncate(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


def _xml(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _svg_to_png_bytes(svg_str, png_path):
    """将 SVG 字符串保存为 PNG（基于 PIL：渲染至 Image）"""
    # 简单方案：解析 SVG 尺寸，构建空白 Image，再用矢量绘制（这里采用绘制近似版）
    import re
    m = re.search(r'width="(\d+)"\s+height="(\d+)"', svg_str)
    if not m:
        raise ValueError("SVG 缺少 width/height")
    w, h = int(m.group(1)), int(m.group(2))
    # 白色底
    img = Image.new("RGB", (w, h), "#F5F6FA")
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 12)
        font_body = ImageFont.truetype("arial.ttf", 14)
        font_meta = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = font_body = font_meta = font_title

    # 顶部色条
    draw.rectangle([(0, 0), (w, 80)], fill="#5B6CFF")
    # 简单绘制：仅展示基本信息（不重渲染每行细节，避免依赖额外 SVG 解析库）
    draw.text((40, 30), "闻道作业 · " + ("总图" if "总" in svg_str else "仅作业" if "作业" in svg_str else "仅教辅"),
              fill="#FFFFFF", font=font_title)
    rows = _filter_items("all" if "总" in svg_str else "homework" if "作业" in svg_str else "teaching")
    draw.text((40, 60), f"{datetime.now().strftime('%Y-%m-%d')} · 共 {len(rows)} 项功能", fill="#CFD3FF", font=font_sub)
    y = 100
    for r in rows[:max(0, (h - 100 - 50) // 86)]:
        draw.rectangle([(20, y), (w - 20, y + 80)], fill="#FAFBFD", outline="#E6E8EF")
        color = {"新增": "#2BB673", "优化": "#3D8EE0", "修复": "#E89B2A"}.get(r["release_type"], "#5B6CFF")
        draw.rectangle([(32, y + 12), (92, y + 32)], fill=color)
        draw.text((62 - 12, y + 16), r["release_type"], fill="#FFFFFF", font=font_body)
        draw.text((104, y + 16), _truncate(r["feature_point"], 30), fill="#1F2330", font=font_body)
        draw.text((40, y + 48), f"入口：{_truncate(r['feature_entry'] or '', 28)} · 面向用户：{r['target_user']}",
                  fill="#5A6172", font=font_sub)
        y += 86
    draw.text((40, h - 24), "发版路线图系统自动生成 · 闻道作业", fill="#9098AC", font=font_meta)
    img.save(png_path, "PNG")


@bp.route("/generate", methods=["POST"])
def generate_images():
    """
    一次性生成总图/仅作业/仅教辅 3 张长图
    """
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    today = datetime.now().strftime("%Y%m%d")
    results = []
    for version in ALLOWED_VERSIONS:
        rows = _filter_items(version)
        target = VERSION_TO_TARGET[version]
        title = VERSION_TO_TITLE[version]
        svg = _build_svg(version, title, target, rows)
        svg_path = os.path.join(upload_dir, f"long_{version}_{today}.svg")
        png_path = os.path.join(upload_dir, f"long_{version}_{today}.png")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
        try:
            _svg_to_png_bytes(svg, png_path)
        except Exception as e:
            return fail("RENDER_FAILED", f"渲染失败: {e}")
        new_id = execute(
            "INSERT INTO generated_images(version,title,target_user,item_count,file_path) VALUES (?,?,?,?,?)",
            (version, title, target, len(rows), os.path.relpath(png_path, os.path.dirname(upload_dir)))
        )
        results.append({
            "id": new_id,
            "version": version,
            "title": title,
            "targetUser": target,
            "itemCount": len(rows),
            "url": f"/api/images/{version}/download?date={today}",
        })
    return ok({"images": results, "generatedAt": _now()}, message=f"已生成 {len(results)} 张长图")


@bp.route("/<version>/download", methods=["GET"])
def download_image(version):
    if version not in ALLOWED_VERSIONS:
        return fail("INVALID_INPUT", f"version 仅支持: {', '.join(ALLOWED_VERSIONS)}")
    date = request.args.get("date") or datetime.now().strftime("%Y%m%d")
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    png_path = os.path.join(upload_dir, f"long_{version}_{date}.png")
    if not os.path.exists(png_path):
        return fail("NOT_FOUND", f"长图 {version} 尚未生成", 404)
    return send_file(png_path, mimetype="image/png", as_attachment=True,
                     download_name=f"闻道作业-{version}-{date}.png")


@bp.route("/<version>/preview", methods=["GET"])
def preview_image(version):
    """返回 base64 编码的 PNG 数据用于前端预览"""
    if version not in ALLOWED_VERSIONS:
        return fail("INVALID_INPUT", f"version 仅支持: {', '.join(ALLOWED_VERSIONS)}")
    date = request.args.get("date") or datetime.now().strftime("%Y%m%d")
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    png_path = os.path.join(upload_dir, f"long_{version}_{date}.png")
    if not os.path.exists(png_path):
        return fail("NOT_FOUND", f"长图 {version} 尚未生成", 404)
    import base64
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return ok({"version": version, "dataUrl": f"data:image/png;base64,{b64}"})


@bp.route("/upload", methods=["POST"])
def upload_image():
    """上传图片（发版详情配图）"""
    file = request.files.get("file")
    if not file:
        return fail("INVALID_INPUT", "未上传文件")
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return fail("INVALID_INPUT", "仅支持 PNG/JPG/JPEG/GIF/WEBP")
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    safe_name = f"{int(time.time())}_{file.filename}"
    save_path = os.path.join(upload_dir, safe_name)
    file.save(save_path)
    rel = os.path.relpath(save_path, os.path.dirname(upload_dir))
    return ok({"filename": file.filename, "path": rel, "url": f"/uploads/{safe_name}"}, message="上传成功", status=201)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
