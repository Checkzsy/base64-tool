# Base64 Tool

**A simple, lightweight Base64 encoder/decoder desktop application built with Python and Tkinter.**

---

## 简介 / Introduction

**中文**

一个基于 Python + Tkinter 构建的本地 Base64 编解码桌面工具，无需安装任何第三方依赖，开箱即用。

**English**

A lightweight local Base64 encode/decode desktop tool built with Python and Tkinter. No third-party dependencies required — works out of the box.

---

## 功能 / Features

| 功能 | Feature |
|---|---|
| Base64 解码（Base64 → 文本） | Base64 decode (Base64 → Text) |
| Base64 编码（文本 → Base64） | Base64 encode (Text → Base64) |
| 一键清空输入与输出 | One-click clear |
| 复制结果到剪贴板 | Copy result to clipboard |
| 非法输入错误提示 | Error hint for invalid input |
| 窗口可自由缩放 | Resizable window |

---

## 截图 / Screenshot

> *(Add a screenshot here after first launch)*

---

## 使用方式 / Usage

### 方式一：直接运行 exe（Windows）/ Run exe directly (Windows)

前往 [Releases](https://github.com/Checkzsy/base64-tool/releases) 页面下载最新版 `Base64Tool.exe`，双击运行，无需安装 Python。

Go to the [Releases](https://github.com/Checkzsy/base64-tool/releases) page, download the latest `Base64Tool.exe`, and double-click to run. No Python installation required.

### 方式二：源码运行 / Run from source

**环境要求 / Requirements**
- Python 3.8+
- 无第三方依赖 / No third-party dependencies

```bash
git clone https://github.com/Checkzsy/base64-tool.git
cd base64-tool
python base64_tool.py
```

### 方式三：自行打包 / Build exe yourself

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Base64Tool" base64_tool.py
# 输出在 dist/Base64Tool.exe
```

---

## 项目结构 / Project Structure

```
base64-tool/
├── base64_tool.py    # 主程序 / Main application
├── requirements.txt  # 依赖说明 / Dependencies
├── LICENSE           # MIT License
└── README.md
```

---

## 开源协议 / License

本项目基于 [MIT License](./LICENSE) 开源。

This project is licensed under the [MIT License](./LICENSE).
