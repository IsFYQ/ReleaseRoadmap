"""
发版路线图 - 启动入口
用法:
  1) 命令行: python run.py
  2) Windows 双击: 直接双击 run.py 即可（控制台会保持开启）
"""
import sys
import os

# 让根目录可被识别
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        from backend import create_app
    except ImportError as e:
        print("[ERROR] 缺少依赖:", e, flush=True)
        print("请先执行: pip install flask flask-cors pillow", flush=True)
        _wait_if_double_clicked()
        return 1

    app = create_app()
    print("[run] 启动 Flask 服务: http://127.0.0.1:5000", flush=True)
    print("[run] 浏览器打开该地址即可使用；关闭此窗口可停止服务", flush=True)
    try:
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[ERROR] 启动失败: {e}", flush=True)
        _wait_if_double_clicked()
        return 1
    return 0


def _wait_if_double_clicked():
    """当用户双击 .py 时，窗口会在脚本退出后自动关闭。
    这里检测是否在交互式终端，如果不是则等待用户按键，保持窗口可见。"""
    try:
        if sys.stdout.isatty():
            return  # 命令行运行，窗口自然保持
    except Exception:
        pass
    print("\n按任意键关闭窗口...", flush=True)
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    sys.exit(main())
