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
        tk.Label(header, text="9合1 编码解码工具箱",
                 font=(FONT_FAMILY, 10),
                 bg=ACCENT, fg="#bfdbfe").pack(side="left")

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        # 创建每个 Tab
        for name, enc_fn, dec_fn, reversible, dec_label in ENCODERS:
            self._create_tab(name, enc_fn, dec_fn, reversible, dec_label)

        # JSON tab（独立构建，带树形表格视图）
        self._create_json_tab()

    def _set_output_text(self, output_text, result):
        """往 Text 输出框写入结果"""
        output_text.config(state="normal")
        output_text.delete("1.0", tk.END)
        output_text.insert("1.0", result)
        output_text.config(state="disabled")

    def _create_json_tab(self):
        frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(frame, text="  JSON  ")

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
        self.json_output_container = tk.Frame(output_lf, bg=CARD_BG)
        self.json_output_container.pack(fill="both", expand=True, padx=4, pady=4)

        def parse_input():
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
            for w in self.json_output_container.winfo_children():
                w.destroy()
            output_text = tk.Text(self.json_output_container,
                                   font=FONT_TEXT, relief="flat", bd=0, wrap="word",
                                   bg="#f8fafc", fg=TEXT_DARK, state="disabled",
                                   padx=8, pady=6,
                                   selectbackground="#bfdbfe",
                                   selectforeground=TEXT_DARK)
            scrollbar = ttk.Scrollbar(self.json_output_container,
                                       command=output_text.yview)
            output_text.config(yscrollcommand=scrollbar.set)
            output_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            self._set_output_text(output_text, result)
            self.json_output_text = output_text
            self.json_tree = None

        def show_tree_output(data):
            """清空输出容器，放入 Treeview 显示树形表格"""
            for w in self.json_output_container.winfo_children():
                w.destroy()
            style = ttk.Style()
            style.configure("Json.Treeview",
                             font=(FONT_FAMILY, 10),
                             rowheight=24,
                             background="#f8fafc",
                             fieldbackground="#f8fafc",
                             foreground=TEXT_DARK)
            style.configure("Json.Treeview.Heading", font=FONT_LABEL)
            tree = ttk.Treeview(self.json_output_container,
                                 style="Json.Treeview", show="tree", selectmode="browse")
            scrollbar = ttk.Scrollbar(self.json_output_container,
                                       command=tree.yview)
            tree.config(yscrollcommand=scrollbar.set)
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            root_node = tree.insert("", "end", text="root ▸", open=True)
            _populate_tree(tree, root_node, data)
            self.json_tree = tree
            self.json_output_text = None

        def get_output_text():
            """获取当前输出内容（文本或树的文本表示），用于复制"""
            if self.json_output_text is not None:
                return self.json_output_text.get("1.0", tk.END).strip()
            if self.json_tree is not None:
                lines = []
                def walk(item, depth):
                    lines.append("  " * depth + self.json_tree.item(item, "text"))
                    for child in self.json_tree.get_children(item):
                        walk(child, depth + 1)
                for item in self.json_tree.get_children(""):
                    walk(item, 0)
                return "\n".join(lines)
            return ""

        def do_format():
            if parse_input() is None:
                return
            try:
                result = json_format(input_text.get("1.0", tk.END).strip())
                show_text_output(result)
                status_label.config(text="格式化成功", fg=SUCCESS)
            except Exception as e:
                status_label.config(text=f"操作失败：{e}", fg=ERROR)

        def do_table():
            if parse_input() is None:
                return
            try:
                result = json_to_table(input_text.get("1.0", tk.END).strip())
                show_text_output(result)
                status_label.config(text="转换表格成功", fg=SUCCESS)
            except Exception as e:
                status_label.config(text=f"操作失败：{e}", fg=ERROR)

        def do_python():
            if parse_input() is None:
                return
            try:
                result = json_to_python(input_text.get("1.0", tk.END).strip())
                show_text_output(result)
                status_label.config(text="转换字典成功", fg=SUCCESS)
            except Exception as e:
                status_label.config(text=f"操作失败：{e}", fg=ERROR)

        def do_tree():
            data = parse_input()
            if data is None:
                return
            show_tree_output(data)
            status_label.config(text="树形表格已生成", fg=SUCCESS)

        def copy_output():
            text = get_output_text()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                status_label.config(text="已复制到剪贴板", fg=INFO)

        def clear_all():
            input_text.delete("1.0", tk.END)
            for w in self.json_output_container.winfo_children():
                w.destroy()
            self.json_output_text = None
            self.json_tree = None
            status_label.config(text="")

        ttk.Button(btn_frame, text="复制结果",
                    command=copy_output, style="Info.TButton").pack(side="right", padx=2)
        ttk.Button(btn_frame, text="清空",
                    command=clear_all, style="Muted.TButton").pack(side="right", padx=2)
        ttk.Button(btn_frame, text="树形表格",
                    command=do_tree, style="Muted.TButton").pack(side="right", padx=2)
        ttk.Button(btn_frame, text="转字典",
                    command=do_python, style="Info.TButton").pack(side="right", padx=2)
        ttk.Button(btn_frame, text="转表格",
                    command=do_table, style="Success.TButton").pack(side="right", padx=2)
        ttk.Button(btn_frame, text="格式化",
                    command=do_format, style="Accent.TButton").pack(side="right", padx=2)

        # 初始空状态
        self.json_output_text = None
        self.json_tree = None

    def _create_tab(self, name, enc_fn, dec_fn, reversible, dec_label):
        frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(frame, text=f"  {name}  ")

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
