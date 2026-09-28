# -*- coding: utf-8 -*-
"""
EncodeTool - 9合1 编码/解码桌面工具
功能：Base64 / URL / HTML / Unicode / Hex / MD5 / SHA-256 / JWT / JSON
依赖：Python 标准库（零第三方依赖）
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

import base64
import hashlib
import json
import html
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import quote, unquote

# ══════════════════════════════════════════════════════
#  工具函数区
# ══════════════════════════════════════════════════════

def base64_encode(text):
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")

def base64_decode(text):
    return base64.b64decode(text).decode("utf-8")

def url_encode(text):
    return quote(text, safe="")

def url_decode(text):
    return unquote(text)

def html_encode(text):
    return html.escape(text)

def html_decode(text):
    return html.unescape(text)

def unicode_encode(text):
    return text.encode("unicode_escape").decode("utf-8")

def unicode_decode(text):
    return text.encode("utf-8").decode("unicode_escape")

def hex_encode(text):
    return text.encode("utf-8").hex()

def hex_decode(text):
    return bytes.fromhex(text.replace(" ", "")).decode("utf-8")

def md5_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def sha256_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def jwt_decode(token):
    """解析 JWT（不验签），返回格式化的 header 和 payload"""
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError("无效的 JWT 格式（需要 3 段，用 . 分隔）")
    header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    result = "【Header】\n"
    result += json.dumps(header, indent=2, ensure_ascii=False)
    result += "\n\n【Payload】\n"
    result += json.dumps(payload, indent=2, ensure_ascii=False)
    result += "\n\n【Signature】\n" + parts[2]
    return result


def json_format(text):
    """格式化 JSON：2 空格缩进，中文不转义"""
    data = json.loads(text)
    return json.dumps(data, indent=2, ensure_ascii=False)


def json_to_python(text):
    """将 JSON 转成 Python 字典字面量（True/False/None、单引号字符串）"""
    data = json.loads(text)
    result, _ = _py_literal(data, 0)
    return result


def _py_literal(value, depth):
    """递归将 JSON 值转为 Python 字面量文本，返回 (文本, 是否多行)"""
    indent = "    " * depth
    child_indent = "    " * (depth + 1)
    if isinstance(value, dict):
        if not value:
            return "{}", False
        items = []
        for k, v in value.items():
            text, _ = _py_literal(v, depth + 1)
            items.append(f"{child_indent}'{k}': {text}")
        return "{\n" + ",\n".join(items) + f"\n{indent}}}", True
    if isinstance(value, list):
        if not value:
            return "[]", False
        items = []
        for v in value:
            text, _ = _py_literal(v, depth + 1)
            items.append(f"{child_indent}{text}")
        return "[\n" + ",\n".join(items) + f"\n{indent}]", True
    if value is True:
        return "True", False
    if value is False:
        return "False", False
    if value is None:
        return "None", False
    if isinstance(value, str):
        return repr(value), False
    # int / float
    return repr(value), False


def _display_width(s):
    """计算字符串显示宽度：中日韩等全角字符按 2 计算"""
    import unicodedata
    width = 0
    for ch in s:
        width += 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
    return width


def _pad(s, width):
    """按显示宽度右侧补空格对齐"""
    return s + " " * (width - _display_width(s))


def _compact(value):
    """单元格内容：纯字符串直接显示，嵌套值显示为紧凑 JSON"""
    if isinstance(value, str):
        return value
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_to_table(text):
    """将 JSON 转成文本表格。
    顶层数组：每个元素一行，所有键并集做表头；
    顶层对象：Key / Value 两列；
    嵌套值在单元格内显示为紧凑 JSON。"""
    data = json.loads(text)
    if isinstance(data, list):
        if not data:
            return "（空数组）"
        if all(isinstance(item, dict) for item in data):
            # 键并集做表头（保持首次出现顺序）
            headers = []
            for item in data:
                for k in item:
                    if k not in headers:
                        headers.append(k)
            rows = [[_compact(item.get(k)) if k in item else "—" for k in headers]
                    for item in data]
        else:
            headers = ["Index", "Value"]
            rows = [[str(i), _compact(v)] for i, v in enumerate(data)]
    elif isinstance(data, dict):
        headers = ["Key", "Value"]
        rows = [[str(k), _compact(v)] for k, v in data.items()]
    else:
        # 标量
        headers = ["Value"]
        rows = [[_compact(data)]]

    # 计算每列宽度（表头和单元格取最大显示宽度，上限 60）
    widths = []
    for col in range(len(headers)):
        cells = [rows[r][col] for r in range(len(rows))]
        cells.append(headers[col])
        widths.append(min(max(_display_width(c) for c in cells), 60))

    # 截断超宽单元格
    for r in range(len(rows)):
        for c in range(len(headers)):
            if _display_width(rows[r][c]) > widths[c]:
                rows[r][c] = _truncate(rows[r][c], widths[c])

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_line = "|" + "|".join(f" {_pad(h, widths[c])} " for c, h in enumerate(headers)) + "|"
    lines = [sep, header_line, sep]
    for row in rows:
        lines.append("|" + "|".join(f" {_pad(v, widths[c])} " for c, v in enumerate(row)) + "|")
    lines.append(sep)
    return "\n".join(lines)


def _truncate(s, width):
    """按显示宽度截断字符串，末尾加省略号"""
    import unicodedata
    out = ""
    w = 0
    for ch in s:
        cw = 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
        if w + cw > width - 1:
            break
        out += ch
        w += cw
    return out + "…"


def _populate_tree(tree, parent, data):
    """递归填充 Treeview：容器节点可展开，叶子显示 key: 值"""
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                if not v:
                    tree.insert(parent, "end", text=f"{k} : {json.dumps(v)}", open=False)
                else:
                    node = tree.insert(parent, "end", text=f"{k} ▸", open=True)
                    _populate_tree(tree, node, v)
            else:
                tree.insert(parent, "end", text=f"{k} : {json.dumps(v, ensure_ascii=False)}", open=False)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            label = f"[{i}]"
            if isinstance(v, (dict, list)):
                if not v:
                    tree.insert(parent, "end", text=f"{label} {json.dumps(v)}", open=False)
                else:
                    node = tree.insert(parent, "end", text=f"{label} ▸", open=True)
                    _populate_tree(tree, node, v)
            else:
                tree.insert(parent, "end", text=f"{label} {json.dumps(v, ensure_ascii=False)}", open=False)
    else:
        tree.insert(parent, "end", text=json.dumps(data, ensure_ascii=False))


def xml_format(text):
    """格式化 XML：统一缩进美化（保留注释与声明）"""
    import xml.etree.ElementTree as ET
    import xml.dom.minidom as minidom
    # 先解析验证合法性
    root = ET.fromstring(text)
    # 用 minidom 美化（解析通过的文本重新走 minidom 拿缩进）
    dom = minidom.parseString(text if isinstance(text, bytes) else text.encode("utf-8"))
    pretty = dom.toprettyxml(indent="  ", encoding=None)
    # 去掉 minidom 自动加的 <?xml version="1.0" ?>（若原文没有声明）
    lines = [ln for ln in pretty.splitlines() if ln.strip()]
    if not text.lstrip().startswith("<?xml") and lines and lines[0].startswith("<?xml"):
        lines = lines[1:]
    return "\n".join(lines)


def xml_compress(text):
    """压缩 XML：去除元素间空白与缩进，输出单行（元素内文本保留）"""
    import re
    import xml.etree.ElementTree as ET
    root = ET.fromstring(text)
    # 清除纯空白文本/尾随空白节点
    for elem in root.iter():
        if elem.text and not elem.text.strip():
            elem.text = None
        if elem.tail and not elem.tail.strip():
            elem.tail = None
    return re.sub(r">\s+<", "><", ET.tostring(root, encoding="unicode"))


# 尝试导入 PyYAML（可选依赖：未安装时 YAML 功能给出友好提示）
try:
    import yaml as _yaml
    YAML_AVAILABLE = True
except ImportError:
    _yaml = None
    YAML_AVAILABLE = False


def _require_yaml():
    if not YAML_AVAILABLE:
        raise ValueError("未安装 PyYAML，请先执行：pip install pyyaml")


def yaml_format(text):
    """格式化 YAML：重新序列化统一缩进"""
    _require_yaml()
    data = _yaml.safe_load(text)
    return _yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)


def yaml_to_json_text(text):
    """YAML → JSON 格式化输出"""
    _require_yaml()
    data = _yaml.safe_load(text)
    return json.dumps(data, indent=2, ensure_ascii=False)


def json_to_yaml_text(text):
    """JSON → YAML 输出"""
    _require_yaml()
    data = json.loads(text)
    return _yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ── 标签顺序持久化 ──────────────────────────────────

def _config_path():
    """配置文件路径：%APPDATA%\\EncodeTool\\config.json"""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "EncodeTool", "config.json")


def load_tab_order(group_names, default=None):
    """读取保存的标签顺序。返回与 group_names 对齐的 {组名: [标签名...]}，
    无效/缺失的组回退为默认顺序。"""
    defaults = {g: list(names) for g, names in group_names.items()}
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            saved = json.load(f)
        for group, names in defaults.items():
            order = saved.get("tab_order", {}).get(group)
            # 只有当顺序恰好是同一组标签（无增删）时才采用
            if isinstance(order, list) and sorted(order) == sorted(names):
                defaults[group] = order
    except Exception:
        pass
    return defaults


def save_tab_order(order):
    """保存标签顺序到配置文件（失败静默，不影响退出）"""
    try:
        path = _config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # 读旧配置合并（保留其他字段）
        data = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
        data["tab_order"] = order
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  配置
# ══════════════════════════════════════════════════════

# 每种编码的配置：(显示名, 编码函数, 解码函数, 是否可逆, 解码按钮文字)
# is_reversible=False 表示只有"编码/生成"操作
ENCODERS = [
    ("Base64",   base64_encode,   base64_decode,   True,  "解码"),
    ("URL",      url_encode,      url_decode,      True,  "解码"),
    ("HTML",     html_encode,     html_decode,     True,  "解码"),
    ("Unicode",  unicode_encode,  unicode_decode,  True,  "解码"),
    ("Hex",      hex_encode,      hex_decode,      True,  "解码"),
    ("MD5",      md5_hash,        None,            False, ""),
    ("SHA-256",  sha256_hash,     None,            False, ""),
    ("JWT",      None,            jwt_decode,      False, "解析"),
]

# 颜色方案
BG          = "#f0f2f5"
CARD_BG     = "#ffffff"
ACCENT      = "#2563eb"
ACCENT_HOVER= "#1d4ed8"
SUCCESS     = "#16a34a"
ERROR       = "#dc2626"
INFO        = "#0284c7"
TEXT_DARK   = "#1e293b"
TEXT_MUTED  = "#64748b"
BORDER      = "#e2e8f0"

FONT_FAMILY   = "Microsoft YaHei UI"
FONT_LABEL    = (FONT_FAMILY, 10)
FONT_TEXT     = ("Consolas", 11)
FONT_BTN      = (FONT_FAMILY, 10)
FONT_TITLE    = (FONT_FAMILY, 11, "bold")
FONT_STATUS   = (FONT_FAMILY, 9)


# ══════════════════════════════════════════════════════
#  UI 构建
# ══════════════════════════════════════════════════════

class EncodeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EncodeTool - 编码解码工具箱")
        self.root.geometry("720x540")
        self.root.minsize(580, 420)
        self.root.configure(bg=BG)

        # 每个 tab 的状态标签和输入输出框引用
        self.tabs = {}

        # 每个 tab 的状态标签和输入输出框引用
        self.tabs = {}

        self._setup_style()
        self._build_ui()

        # 关闭窗口时保存内层标签顺序
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        save_tab_order(self._current_tab_order())
        self.root.destroy()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Notebook 样式
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                         font=(FONT_FAMILY, 10),
                         padding=[16, 6],
                         background="#e5e7eb",
                         foreground=TEXT_DARK)
        style.map("TNotebook.Tab",
                   background=[("selected", CARD_BG)],
                   foreground=[("selected", ACCENT)],
                   expand=[("selected", [0, 0, 2, 0])])

        # 按钮样式
        style.configure("Accent.TButton",
                         font=FONT_BTN,
                         background=ACCENT,
                         foreground="white",
                         padding=[18, 6],
                         borderwidth=0)
        style.map("Accent.TButton",
                   background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)])

        style.configure("Success.TButton",
                         font=FONT_BTN,
                         background="#16a34a",
                         foreground="white",
                         padding=[18, 6],
                         borderwidth=0)
        style.map("Success.TButton",
                   background=[("active", "#15803d"), ("pressed", "#15803d")])

        style.configure("Muted.TButton",
                         font=FONT_BTN,
                         background="#94a3b8",
                         foreground="white",
                         padding=[18, 6],
                         borderwidth=0)
        style.map("Muted.TButton",
                   background=[("active", "#64748b"), ("pressed", "#64748b")])

        style.configure("Info.TButton",
                         font=FONT_BTN,
                         background="#8b5cf6",
                         foreground="white",
                         padding=[18, 6],
                         borderwidth=0)
        style.map("Info.TButton",
                   background=[("active", "#7c3aed"), ("pressed", "#7c3aed")])

        # LabelFrame 样式
        style.configure("Card.TLabelframe",
                         background=CARD_BG,
                         relief="flat",
                         borderwidth=1)
        style.configure("Card.TLabelframe.Label",
                         font=FONT_LABEL,
                         background=CARD_BG,
                         foreground=TEXT_MUTED)

    def _build_ui(self):
        # 顶部标题
        header = tk.Frame(self.root, bg=ACCENT, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="EncodeTool",
                 font=(FONT_FAMILY, 14, "bold"),
                 bg=ACCENT, fg="white").pack(side="left", padx=16)
        tk.Label(header, text="11合1 编码解码工具箱",
                 font=(FONT_FAMILY, 10),
                 bg=ACCENT, fg="#bfdbfe").pack(side="left")

        # 外层分组 Notebook（编解码 / 格式化，固定顺序）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        # 内层：编解码组
        enc_frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(enc_frame, text="  编解码  ")
        self.enc_notebook = ttk.Notebook(enc_frame)
        self.enc_notebook.pack(fill="both", expand=True, padx=4, pady=4)

        # 内层：格式化组
        fmt_frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(fmt_frame, text="  格式化  ")
        self.fmt_notebook = ttk.Notebook(fmt_frame)
        self.fmt_notebook.pack(fill="both", expand=True, padx=4, pady=4)

        # 创建编解码 Tab
        for name, enc_fn, dec_fn, reversible, dec_label in ENCODERS:
            self._create_tab(self.enc_notebook, name, enc_fn, dec_fn, reversible, dec_label)

        # 创建格式化 Tab（多按钮工具共用骨架）
        self._create_tool_tab(self.fmt_notebook, "JSON", [
            ("格式化", "format", "Accent.TButton"),
            ("转表格", "table", "Success.TButton"),
            ("转字典", "python", "Info.TButton"),
            ("树形表格", "tree", "Muted.TButton"),
        ])
        self._create_tool_tab(self.fmt_notebook, "XML", [
            ("格式化", "xml_format", "Accent.TButton"),
            ("压缩", "xml_compress", "Success.TButton"),
        ])
        self._create_tool_tab(self.fmt_notebook, "YAML", [
            ("YAML 美化", "yaml_format", "Accent.TButton"),
            ("YAML → JSON", "yaml_to_json", "Success.TButton"),
            ("JSON → YAML", "json_to_yaml", "Info.TButton"),
        ])

        # 内层标签拖拽排序（编解码组与格式化组）
        for nb in (self.enc_notebook, self.fmt_notebook):
            self._enable_tab_drag(nb)

        # 启动时恢复上次保存的标签顺序
        self._restore_tab_order()

        # 外层分组旁放 Reset 按钮（恢复默认内层顺序）
        reset_bar = tk.Frame(self.root, bg=BG)
        # 用 place 贴在 Notebook 右上角
        reset_bar.place(relx=1.0, y=6, anchor="ne", x=-16)
        ttk.Button(reset_bar, text="↺ 重置顺序", style="Muted.TButton",
                    command=self._reset_tab_order).pack()

    def _set_output_text(self, output_text, result):
        """往 Text 输出框写入结果"""
        output_text.config(state="normal")
        output_text.delete("1.0", tk.END)
        output_text.insert("1.0", result)
        output_text.config(state="disabled")

    # ── 标签拖拽排序 + 持久化 ────────────────────────

    def _enable_tab_drag(self, notebook):
        """给内层 Notebook 绑定标签拖拽换位事件"""
        state = {"pressed_index": None}

        def on_press(event):
            try:
                state["pressed_index"] = notebook.index(f"@{event.x},{event.y}")
            except tk.TclError:
                state["pressed_index"] = None

        def on_motion(event):
            src = state["pressed_index"]
            if src is None:
                return
            try:
                dst = notebook.index(f"@{event.x},{event.y}")
            except tk.TclError:
                return
            if dst == src:
                return
            # 换位并保持选中跟随拖动的标签
            notebook.insert(src, dst)
            notebook.select(dst)
            state["pressed_index"] = dst

        def on_release(event):
            state["pressed_index"] = None

        notebook.bind("<ButtonPress-1>", on_press, add="+")
        notebook.bind("<B1-Motion>", on_motion, add="+")
        notebook.bind("<ButtonRelease-1>", on_release, add="+")

    def _current_tab_order(self):
        """读取两个内层 Notebook 的当前标签顺序"""
        def names(nb):
            return [nb.tab(t, "text").strip() for t in nb.tabs()]
        return {
            "encoders": names(self.enc_notebook),
            "formatters": names(self.fmt_notebook),
        }

    def _restore_tab_order(self):
        """启动时按保存的顺序重排内层标签（无效则保持默认）"""
        group_names = {
            "encoders": [n for n, *_ in ENCODERS],
            "formatters": ["JSON", "XML", "YAML"],
        }
        order = load_tab_order(group_names)
        for nb, key in ((self.enc_notebook, "encoders"),
                        (self.fmt_notebook, "formatters")):
            tabs = {nb.tab(t, "text").strip(): t for t in nb.tabs()}
            pos = 0
            for name in order.get(key, []):
                if name in tabs:
                    nb.insert(pos, tabs[name])
                    pos += 1

    def _reset_tab_order(self):
        """恢复默认标签顺序并清除保存的配置"""
        default = {
            "encoders": [n for n, *_ in ENCODERS],
            "formatters": ["JSON", "XML", "YAML"],
        }
        for nb, key in ((self.enc_notebook, "encoders"),
                        (self.fmt_notebook, "formatters")):
            tabs = {nb.tab(t, "text").strip(): t for t in nb.tabs()}
            pos = 0
            for name in default[key]:
                if name in tabs:
                    nb.insert(pos, tabs[name])
                    pos += 1
        save_tab_order(default)
        try:
            os.remove(_config_path())
        except OSError:
            pass

    def _create_tool_tab(self, notebook, name, actions):
        """通用多按钮工具 tab（JSON/XML/YAML 共用骨架）。

        actions: [(按钮文字, 动作key, 按钮样式), ...]
        动作key 由 _run_tool_action 解释。
        """
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text=f"  {name}  ")

        # 输入区域
        input_lf = ttk.LabelFrame(frame, text=" 输入内容 ", style="Card.TLabelframe")
        input_lf.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        input_text = tk.Text(input_lf, height=6, font=FONT_TEXT,
                              relief="flat", bd=0, wrap="word",
                              bg=CARD_BG, fg=TEXT_DARK,
                              insertbackground=ACCENT,
                              selectbackground="#bfdbfe",
                              selectforeground=TEXT_DARK,
                              padx=8, pady=6)
        input_text.pack(fill="both", expand=True, padx=4, pady=4)

        # 按钮区域
        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(fill="x", padx=8, pady=4)

        status_label = tk.Label(btn_frame, text="", font=FONT_STATUS,
                                 bg=BG, fg=TEXT_MUTED, anchor="w")
        status_label.pack(side="left", fill="x", expand=True)

        # 输出区域：容器 frame，内部按需放 Text 或 Treeview
        output_lf = ttk.LabelFrame(frame, text=" 输出结果 ", style="Card.TLabelframe")
        output_lf.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        output_container = tk.Frame(output_lf, bg=CARD_BG)
        output_container.pack(fill="both", expand=True, padx=4, pady=4)

        # 每 tab 独立的输出状态
        state = {"text": None, "tree": None}

        def parse_json_input():
            text = input_text.get("1.0", tk.END).strip()
            if not text:
                status_label.config(text="请输入 JSON 内容", fg=ERROR)
                return None
            try:
                return json.loads(text)
            except Exception as e:
                status_label.config(text=f"JSON 解析失败：{e}", fg=ERROR)
                return None

        def show_text_output(result):
            """清空输出容器，放入 Text 显示文本结果"""
            for w in output_container.winfo_children():
                w.destroy()
            output_text = tk.Text(output_container,
                                   font=FONT_TEXT, relief="flat", bd=0, wrap="word",
                                   bg="#f8fafc", fg=TEXT_DARK, state="disabled",
                                   padx=8, pady=6,
                                   selectbackground="#bfdbfe",
                                   selectforeground=TEXT_DARK)
            scrollbar = ttk.Scrollbar(output_container,
                                       command=output_text.yview)
            output_text.config(yscrollcommand=scrollbar.set)
            output_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            self._set_output_text(output_text, result)
            state["text"] = output_text
            state["tree"] = None

        def show_tree_output(data):
            """清空输出容器，放入 Treeview 显示树形表格"""
            for w in output_container.winfo_children():
                w.destroy()
            style = ttk.Style()
            style.configure("Tool.Treeview",
                             font=(FONT_FAMILY, 10),
                             rowheight=24,
                             background="#f8fafc",
                             fieldbackground="#f8fafc",
                             foreground=TEXT_DARK)
            tree = ttk.Treeview(output_container,
                                 style="Tool.Treeview", show="tree", selectmode="browse")
            scrollbar = ttk.Scrollbar(output_container,
                                       command=tree.yview)
            tree.config(yscrollcommand=scrollbar.set)
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            root_node = tree.insert("", "end", text="root ▸", open=True)
            _populate_tree(tree, root_node, data)
            state["tree"] = tree
            state["text"] = None

        def get_output_text():
            """获取当前输出内容（文本或树的文本表示），用于复制"""
            if state["text"] is not None:
                return state["text"].get("1.0", tk.END).strip()
            if state["tree"] is not None:
                tree = state["tree"]
                lines = []
                def walk(item, depth):
                    lines.append("  " * depth + tree.item(item, "text"))
                    for child in tree.get_children(item):
                        walk(child, depth + 1)
                for item in tree.get_children(""):
                    walk(item, 0)
                return "\n".join(lines)
            return ""

        def run_action(action_key):
            raw = input_text.get("1.0", tk.END).strip()
            ok, result = self._run_tool_action(action_key, raw, parse_json_input)
            if not ok:
                status_label.config(text=result, fg=ERROR)
                return
            if isinstance(result, tuple) and result[0] == "__tree__":
                show_tree_output(result[1])
                status_label.config(text="树形表格已生成", fg=SUCCESS)
            else:
                show_text_output(result)
                status_label.config(text="操作成功", fg=SUCCESS)

        def copy_output():
            text = get_output_text()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                status_label.config(text="已复制到剪贴板", fg=INFO)

        def clear_all():
            input_text.delete("1.0", tk.END)
            for w in output_container.winfo_children():
                w.destroy()
            state["text"] = None
            state["tree"] = None
            status_label.config(text="")

        # 固定按钮（右侧）：复制、清空
        ttk.Button(btn_frame, text="复制结果",
                    command=copy_output, style="Info.TButton").pack(side="right", padx=2)
        ttk.Button(btn_frame, text="清空",
                    command=clear_all, style="Muted.TButton").pack(side="right", padx=2)
        # 动作按钮（右侧依次往左）
        for label, action_key, btn_style in reversed(actions):
            ttk.Button(btn_frame, text=label,
                        command=lambda k=action_key: run_action(k),
                        style=btn_style).pack(side="right", padx=2)

    @staticmethod
    def _run_tool_action(action_key, raw_text, parse_json_input):
        """执行工具动作。返回 (ok, 结果)；
        树形视图返回 (True, ("__tree__", data))；失败返回 (False, 错误消息)。"""
        try:
            if action_key == "format":
                return True, json_format(raw_text)
            if action_key == "table":
                return True, json_to_table(raw_text)
            if action_key == "python":
                return True, json_to_python(raw_text)
            if action_key == "tree":
                data = parse_json_input()
                if data is None:
                    return False, "JSON 解析失败"
                return True, ("__tree__", data)
            if action_key == "xml_format":
                if not raw_text:
                    return False, "请输入 XML 内容"
                return True, xml_format(raw_text)
            if action_key == "xml_compress":
                if not raw_text:
                    return False, "请输入 XML 内容"
                return True, xml_compress(raw_text)
            if action_key == "yaml_format":
                if not raw_text:
                    return False, "请输入 YAML 内容"
                return True, yaml_format(raw_text)
            if action_key == "yaml_to_json":
                if not raw_text:
                    return False, "请输入 YAML 内容"
                return True, yaml_to_json_text(raw_text)
            if action_key == "json_to_yaml":
                if not raw_text:
                    return False, "请输入 JSON 内容"
                return True, json_to_yaml_text(raw_text)
            return False, f"未知操作：{action_key}"
        except Exception as e:
            return False, f"操作失败：{e}"

    def _create_tab(self, notebook, name, enc_fn, dec_fn, reversible, dec_label):
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text=f"  {name}  ")

        # 输入区域
        input_lf = ttk.LabelFrame(frame, text=" 输入内容 ", style="Card.TLabelframe")
        input_lf.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        input_text = tk.Text(input_lf, height=6, font=FONT_TEXT,
                              relief="flat", bd=0, wrap="word",
                              bg=CARD_BG, fg=TEXT_DARK,
                              insertbackground=ACCENT,
                              selectbackground="#bfdbfe",
                              selectforeground=TEXT_DARK,
                              padx=8, pady=6)
        input_text.pack(fill="both", expand=True, padx=4, pady=4)

        # 按钮区域
        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(fill="x", padx=8, pady=4)

        status_label = tk.Label(btn_frame, text="", font=FONT_STATUS,
                                 bg=BG, fg=TEXT_MUTED, anchor="w")
        status_label.pack(side="left", fill="x", expand=True)

        # 输出区域
        output_lf = ttk.LabelFrame(frame, text=" 输出结果 ", style="Card.TLabelframe")
        output_lf.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        output_text = tk.Text(output_lf, height=6, font=FONT_TEXT,
                               relief="flat", bd=0, wrap="word",
                               bg="#f8fafc", fg=TEXT_DARK,
                               state="disabled",
                               padx=8, pady=6,
                               selectbackground="#bfdbfe",
                               selectforeground=TEXT_DARK)
        output_text.pack(fill="both", expand=True, padx=4, pady=4)

        # 按钮（从右到左排列）
        def copy_output():
            text = output_text.get("1.0", tk.END).strip()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                status_label.config(text="已复制到剪贴板", fg=INFO)

        def clear_all():
            input_text.delete("1.0", tk.END)
            output_text.config(state="normal")
            output_text.delete("1.0", tk.END)
            output_text.config(state="disabled")
            status_label.config(text="")

        def do_decode():
            text = input_text.get("1.0", tk.END).strip()
            if not text:
                return
            try:
                result = dec_fn(text)
                output_text.config(state="normal")
                output_text.delete("1.0", tk.END)
                output_text.insert("1.0", result)
                output_text.config(state="disabled")
                status_label.config(
                    text=f"{dec_label}成功" if dec_label else "操作成功",
                    fg=SUCCESS)
            except Exception as e:
                status_label.config(text=f"{dec_label}失败：{e}", fg=ERROR)

        def do_encode():
            text = input_text.get("1.0", tk.END).strip()
            if not text:
                return
            try:
                if enc_fn:
                    result = enc_fn(text)
                else:
                    # JWT 没有编码功能
                    status_label.config(text="该类型不支持编码操作", fg=ERROR)
                    return
                output_text.config(state="normal")
                output_text.delete("1.0", tk.END)
                output_text.insert("1.0", result)
                output_text.config(state="disabled")
                op_name = "生成哈希" if name in ("MD5", "SHA-256") else "编码成功"
                status_label.config(text=op_name, fg=SUCCESS)
            except Exception as e:
                status_label.config(text=f"操作失败：{e}", fg=ERROR)

        ttk.Button(btn_frame, text="复制结果",
                    command=copy_output, style="Info.TButton").pack(side="right", padx=2)
        ttk.Button(btn_frame, text="清空",
                    command=clear_all, style="Muted.TButton").pack(side="right", padx=2)

        if dec_fn and reversible:
            ttk.Button(btn_frame, text=dec_label or "解码",
                        command=do_decode, style="Success.TButton").pack(side="right", padx=2)
        elif dec_fn and not reversible:
            # JWT 的"解析"按钮
            ttk.Button(btn_frame, text=dec_label or "解析",
                        command=do_decode, style="Success.TButton").pack(side="right", padx=2)

        if enc_fn:
            enc_label = "生成哈希" if name in ("MD5", "SHA-256") else "编码"
            ttk.Button(btn_frame, text=enc_label,
                        command=do_encode, style="Accent.TButton").pack(side="right", padx=2)

        # 存储引用
        self.tabs[name] = {
            "input": input_text,
            "output": output_text,
            "status": status_label,
        }

    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════════
#  启动
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    app = EncodeApp()
    app.run()
