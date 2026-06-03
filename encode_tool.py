# -*- coding: utf-8 -*-
"""
EncodeTool - 8合1 编码/解码桌面工具
功能：Base64 / URL / HTML / Unicode / Hex / MD5 / SHA-256 / JWT
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
        tk.Label(header, text="8合1 编码解码工具箱",
                 font=(FONT_FAMILY, 10),
                 bg=ACCENT, fg="#bfdbfe").pack(side="left")

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        # 创建每个 Tab
        for name, enc_fn, dec_fn, reversible, dec_label in ENCODERS:
            self._create_tab(name, enc_fn, dec_fn, reversible, dec_label)

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
