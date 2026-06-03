import base64
import tkinter as tk
from tkinter import messagebox


def decode():
    text = input_box.get("1.0", tk.END).strip()
    if not text:
        return
    try:
        result = base64.b64decode(text).decode("utf-8")
        output_box.config(state="normal")
        output_box.delete("1.0", tk.END)
        output_box.insert("1.0", result)
        output_box.config(state="disabled")
        status_label.config(text="解码成功", fg="#27ae60")
    except Exception:
        status_label.config(text="解码失败：输入内容不是合法的 Base64 字符串", fg="#e74c3c")


def encode():
    text = input_box.get("1.0", tk.END).strip()
    if not text:
        return
    try:
        result = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        output_box.config(state="normal")
        output_box.delete("1.0", tk.END)
        output_box.insert("1.0", result)
        output_box.config(state="disabled")
        status_label.config(text="编码成功", fg="#27ae60")
    except Exception as e:
        status_label.config(text=f"编码失败：{e}", fg="#e74c3c")


def clear():
    input_box.delete("1.0", tk.END)
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.config(state="disabled")
    status_label.config(text="", fg="#555")


def copy_output():
    text = output_box.get("1.0", tk.END).strip()
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)
        status_label.config(text="已复制到剪贴板", fg="#2980b9")


# ── 主窗口 ──────────────────────────────────────────
root = tk.Tk()
root.title("Base64 编解码工具")
root.geometry("620x500")
root.resizable(True, True)
root.configure(bg="#f5f5f5")

FONT_LABEL = ("Microsoft YaHei", 10)
FONT_TEXT  = ("Consolas", 11)
FONT_BTN   = ("Microsoft YaHei", 10)
BG         = "#f5f5f5"
BTN_H      = "#3498db"
BTN_DECODE = "#2ecc71"
BTN_ENCODE = "#e67e22"
BTN_CLEAR  = "#95a5a6"
BTN_COPY   = "#9b59b6"

pad = {"padx": 16, "pady": 6}

# ── 输入区 ──────────────────────────────────────────
tk.Label(root, text="输入内容", font=FONT_LABEL, bg=BG, anchor="w").pack(fill="x", **pad)

input_frame = tk.Frame(root, bg=BG)
input_frame.pack(fill="both", expand=True, padx=16)

input_scroll = tk.Scrollbar(input_frame)
input_scroll.pack(side="right", fill="y")

input_box = tk.Text(
    input_frame, height=8, font=FONT_TEXT,
    yscrollcommand=input_scroll.set,
    relief="solid", bd=1, wrap="word",
    bg="white", fg="#222"
)
input_box.pack(side="left", fill="both", expand=True)
input_scroll.config(command=input_box.yview)

# ── 按钮区 ──────────────────────────────────────────
btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(pady=10)

def make_btn(parent, text, cmd, color):
    return tk.Button(
        parent, text=text, command=cmd,
        font=FONT_BTN, bg=color, fg="white",
        activebackground=color, activeforeground="white",
        relief="flat", padx=18, pady=6, cursor="hand2"
    )

make_btn(btn_frame, "解码 (Base64 → 文本)", decode, BTN_DECODE).pack(side="left", padx=6)
make_btn(btn_frame, "编码 (文本 → Base64)", encode, BTN_ENCODE).pack(side="left", padx=6)
make_btn(btn_frame, "清空",                  clear,  BTN_CLEAR ).pack(side="left", padx=6)

# ── 输出区 ──────────────────────────────────────────
tk.Label(root, text="输出结果", font=FONT_LABEL, bg=BG, anchor="w").pack(fill="x", **pad)

output_frame = tk.Frame(root, bg=BG)
output_frame.pack(fill="both", expand=True, padx=16)

output_scroll = tk.Scrollbar(output_frame)
output_scroll.pack(side="right", fill="y")

output_box = tk.Text(
    output_frame, height=8, font=FONT_TEXT,
    yscrollcommand=output_scroll.set,
    relief="solid", bd=1, wrap="word",
    bg="#fafafa", fg="#222", state="disabled"
)
output_box.pack(side="left", fill="both", expand=True)
output_scroll.config(command=output_box.yview)

# ── 底部：状态 + 复制 ────────────────────────────────
bottom_frame = tk.Frame(root, bg=BG)
bottom_frame.pack(fill="x", padx=16, pady=(6, 12))

status_label = tk.Label(bottom_frame, text="", font=FONT_LABEL, bg=BG, fg="#555", anchor="w")
status_label.pack(side="left", fill="x", expand=True)

make_btn(bottom_frame, "复制结果", copy_output, BTN_COPY).pack(side="right")

root.mainloop()
