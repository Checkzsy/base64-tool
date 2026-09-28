# -*- coding: utf-8 -*-
"""
ToolBox v3.0 - Web UI 入口
pywebview 承载 webui/ 前端，通过 js_api 桥接 tools.py 工具函数。
运行：python app.py
依赖：pip install pywebview pyyaml
"""

import sys
import os

# 强制标准输出使用 UTF-8（解决 Windows 中文终端乱码）
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import webview

import tools


class Api:
    """暴露给前端 JS 的桥接方法（pywebview js_api）。"""

    def run_tool(self, action, text):
        """执行工具动作，返回 {ok, result|error}"""
        ok, result = tools.run_tool_action(action, text)
        if ok:
            return {"ok": True, "result": result}
        return {"ok": False, "error": result}

    def get_config(self):
        """返回前端初始化所需的配置：主题偏好 + 分组内工具顺序"""
        cfg = tools.get_config()
        group_names = {
            "encoders": [n for n, *_ in tools.ENCODERS],
            "formatters": list(tools.FORMATTERS),
        }
        order = tools.load_tab_order(group_names, cfg["tab_order"])
        return {
            "theme": cfg["theme"],  # None = 跟随系统
            "order": order,
            "yamlAvailable": tools.YAML_AVAILABLE,
        }

    def set_theme(self, theme):
        """保存主题偏好：'dark' / 'light' / None（跟随系统）"""
        if theme not in ("dark", "light", None):
            return {"ok": False}
        tools.save_theme(theme)
        return {"ok": True}

    def save_order(self, order):
        """保存分组内工具顺序 {encoders: [...], formatters: [...]}"""
        if not isinstance(order, dict):
            return {"ok": False}
        clean = {}
        for key in ("encoders", "formatters"):
            val = order.get(key)
            if isinstance(val, list) and all(isinstance(x, str) for x in val):
                clean[key] = val
        tools.save_tab_order(clean)
        return {"ok": True}


def get_ui_path():
    """webui 目录的绝对路径（兼容源码运行与 Nuitka 打包）"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "webui", "index.html")


if __name__ == "__main__":
    api = Api()
    webview.create_window(
        "ToolBox - 编码解码工具箱",
        get_ui_path(),
        js_api=api,
        width=980,
        height=680,
        min_size=(820, 560),
    )
    webview.start()
