# EncodeTool

**A comprehensive 11-in-1 encoding/decoding & formatting desktop toolbox built with Python and Tkinter.**

---

## 简介 / Introduction

**中文**

一个基于 Python + Tkinter 构建的本地编码解码桌面工具箱，按「编解码 / 格式化」两个功能区分组，共集成 11 种常用工具。标签页支持拖动排序（自动记忆），开箱即用。

**English**

A local encoding/decoding & formatting desktop toolbox built with Python and Tkinter, grouping 11 tools into two sections (Encode/Decode, Format). Tabs are drag-to-reorder (position remembered). Works out of the box.

---

## 功能 / Features

### 编解码 / Encode & Decode

| 功能 | Feature |
|---|---|
| Base64 编码/解码 | Base64 encode/decode |
| URL 编码/解码 | URL encode/decode |
| HTML 实体编码/解码 | HTML entity encode/decode |
| Unicode 转义/反转义 | Unicode escape/unescape |
| Hex 十六进制编/解码 | Hex encode/decode |
| MD5 哈希生成 | MD5 hash generation |
| SHA-256 哈希生成 | SHA-256 hash generation |
| JWT 解析 | JWT payload parsing |

### 格式化 / Format

| 功能 | Feature |
|---|---|
| JSON 格式化 / 转表格 / 转字典 / 树形视图 | JSON format / to-table / to-Python-dict / tree view |
| XML 格式化 / 压缩 | XML pretty-print / minify |
| YAML 美化 / YAML ⇄ JSON | YAML format / YAML ⇄ JSON *(需 PyYAML / requires PyYAML)* |

### 其他特性 / Extras

- 标签页拖动排序，顺序自动保存（`%APPDATA%\EncodeTool\config.json`），可用「↺ 重置顺序」恢复默认 / Drag-to-reorder tabs, persisted and resettable

---

## 截图 / Screenshot

<img width="720" height="570" alt="image" src="https://github.com/user-attachments/assets/6a707a01-4726-4f7e-b1b7-de7807b63e7d" />

> *(Add a screenshot here after first launch)*

---

## 使用方式 / Usage

### 方式一：直接运行 exe（Windows）/ Run exe directly (Windows)

前往 [Releases](https://github.com/Checkzsy/base64-tool/releases) 页面下载最新版 `EncodeTool.exe`，双击运行，无需安装 Python。

Go to the [Releases](https://github.com/Checkzsy/base64-tool/releases) page, download the latest `EncodeTool.exe`, and double-click to run. No Python installation required.

### 方式二：源码运行 / Run from source

**环境要求 / Requirements**
- Python 3.8+
- 无第三方依赖 / No third-party dependencies

```bash
git clone https://github.com/Checkzsy/base64-tool.git
cd base64-tool
python encode_tool.py
```

### 方式三：自行打包 / Build exe yourself

```bash
pip install nuitka ordered-set zstandard
python -m nuitka --standalone --onefile --windows-disable-console --enable-plugin=tk-inter --output-filename=EncodeTool.exe encode_tool.py
# 输出在当前目录 EncodeTool.exe
```

---

## 项目结构 / Project Structure

```
base64-tool/
├── encode_tool.py     # 主程序（11合1版本）/ Main application (v2.2)
├── base64_tool.py     # 旧版（仅Base64）/ Legacy Base64-only version
├── icon.ico           # 应用图标 / App icon
├── requirements.txt   # 依赖说明 / Dependencies
├── LICENSE            # MIT License
└── README.md
```

---

## 编码功能对照 / Encoding Reference

| 编码类型 | 编码函数 | 解码函数 |
|---|---|---|
| Base64 | `base64.b64encode` | `base64.b64decode` |
| URL | `urllib.parse.quote` | `urllib.parse.unquote` |
| HTML | `html.escape` | `html.unescape` |
| Unicode | `str.encode('unicode_escape')` | `bytes.decode('unicode_escape')` |
| Hex | `str.encode().hex()` | `bytes.fromhex()` |
| MD5 | `hashlib.md5` | *(单向哈希 / one-way)* |
| SHA-256 | `hashlib.sha256` | *(单向哈希 / one-way)* |
| JWT | — | `base64.urlsafe_b64decode` + `json.loads` |
| JSON | `json.dumps(indent=2)` | `json.loads` / Treeview 树形视图 |
| XML | `xml.dom.minidom` / `xml.etree` | *(单向格式化 / formatting only)* |
| YAML | `yaml.dump`（PyYAML） | `yaml.safe_load`（PyYAML） |

---

## 开源协议 / License

本项目基于 [MIT License](./LICENSE) 开源。

This project is licensed under the [MIT License](./LICENSE).
