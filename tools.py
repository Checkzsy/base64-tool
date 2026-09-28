# -*- coding: utf-8 -*-
"""
ToolBox - 工具函数层
全部编解码/格式化纯函数 + 配置读写。
被 encode_tool.py（旧 Tkinter UI）和 app.py（新 Web UI）共用。
"""

import base64
import hashlib
import html
import json
import os
import unicodedata
from functools import lru_cache


# ══════════════════════════════════════════════════════
#  编解码函数
# ══════════════════════════════════════════════════════

def base64_encode(text):
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")

def base64_decode(text):
    return base64.b64decode(text, validate=True).decode("utf-8")

def url_encode(text):
    from urllib.parse import quote
    return quote(text, safe="")

def url_decode(text):
    from urllib.parse import unquote
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

# 格式化组：默认顺序（旧版 Tkinter 与 app.py 共用，避免常量多头维护）
FORMATTERS = ["JSON", "XML", "YAML"]


# ══════════════════════════════════════════════════════
#  JSON
# ══════════════════════════════════════════════════════

def json_format(text):
    """格式化 JSON：2 空格缩进，中文不转义"""
    data = json.loads(text)
    return json.dumps(data, indent=2, ensure_ascii=False)


def json_to_python(text):
    """将 JSON 转成 Python 字典字面量（True/False/None、单引号字符串）"""
    data = json.loads(text)
    return _py_literal(data, 0)


def python_to_json(text):
    """将 Python 字典字面量转回 JSON 并美化。
    非字面量输入（dataclass/对象 repr，如 Flow(id='x', steps=[...])）走 repr 解析器回退。"""
    import ast
    try:
        data = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        data = _ReprParser(text).parse()
    return json.dumps(data, indent=2, ensure_ascii=False)


class _ReprParser:
    """把 Python 对象 repr 文本解析回数据结构。

    支持：dict/list/tuple/set、字符串/数字/True/False/None、
    构造器表示 ClassName(field=value) -> {"_type": "ClassName", ...}、
    枚举表示 <Enum.VALUE: 'value'> -> 'value'。
    """

    _WS = " \t\n\r"

    def __init__(self, text):
        self.s = text
        self.i = 0
        self.n = len(text)

    def parse(self):
        value = self._value()
        self._skip_ws()
        if self.i < self.n:
            raise ValueError(f"输入在第 {self.i} 字符处有剩余内容")
        return value

    def _skip_ws(self):
        while self.i < self.n and self.s[self.i] in self._WS:
            self.i += 1

    def _value(self):
        self._skip_ws()
        if self.i >= self.n:
            raise ValueError("输入意外结束")
        c = self.s[self.i]
        if c in "'\"":
            return self._string()
        if c == "[":
            return self._list()
        if c == "{":
            return self._dict_or_set()
        if c == "(":
            return self._tuple()
        if c == "<":
            return self._enum()
        return self._atom()

    def _string(self):
        # 完整字符串 token（含转义），交给 literal_eval 还原
        quote = self.s[self.i]
        j = self.i + 1
        while j < self.n:
            if self.s[j] == "\\":
                j += 2
                continue
            if self.s[j] == quote:
                break
            j += 1
        if j >= self.n:
            raise ValueError("字符串未闭合")
        token = self.s[self.i:j + 1]
        self.i = j + 1
        import ast
        return ast.literal_eval(token)

    def _list(self):
        self.i += 1  # [
        items = []
        self._skip_ws()
        if self.i < self.n and self.s[self.i] == "]":
            self.i += 1
            return items
        while True:
            items.append(self._value())
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("列表未闭合")
            if self.s[self.i] == "]":
                self.i += 1
                return items
            if self.s[self.i] == ",":
                self.i += 1
            else:
                raise ValueError("列表元素间缺少逗号")

    def _tuple(self):
        self.i += 1  # (
        items = []
        self._skip_ws()
        if self.i < self.n and self.s[self.i] == ")":
            self.i += 1
            return items
        while True:
            items.append(self._value())
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("元组未闭合")
            if self.s[self.i] == ")":
                self.i += 1
                return items
            if self.s[self.i] == ",":
                self.i += 1
                self._skip_ws()
                # 允许尾随逗号后直接闭合：(1,)
                if self.i < self.n and self.s[self.i] == ")":
                    self.i += 1
                    return items
            else:
                raise ValueError("元组元素间缺少逗号")

    def _dict_or_set(self):
        self.i += 1  # {
        self._skip_ws()
        if self.i < self.n and self.s[self.i] == "}":
            self.i += 1
            return {}
        # 先解析首个元素判断是 dict 还是 set
        first = self._value()
        self._skip_ws()
        if self.i < self.n and self.s[self.i] == ":":
            # dict
            self.i += 1
            result = {self._hashable(first): self._value()}
            while True:
                self._skip_ws()
                if self.i >= self.n:
                    raise ValueError("字典未闭合")
                if self.s[self.i] == "}":
                    self.i += 1
                    return result
                if self.s[self.i] == ",":
                    self.i += 1
                    self._skip_ws()
                    if self.i < self.n and self.s[self.i] == "}":
                        self.i += 1
                        return result
                    key = self._value()
                    self._skip_ws()
                    if self.i >= self.n or self.s[self.i] != ":":
                        raise ValueError("字典键后缺少冒号")
                    self.i += 1
                    result[self._hashable(key)] = self._value()
                else:
                    raise ValueError("字典项间缺少逗号")
        # set
        result = [self._hashable(first)]
        while True:
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("集合未闭合")
            if self.s[self.i] == "}":
                self.i += 1
                return result
            if self.s[self.i] == ",":
                self.i += 1
                self._skip_ws()
                if self.i < self.n and self.s[self.i] == "}":
                    self.i += 1
                    return result
                result.append(self._hashable(self._value()))
            else:
                raise ValueError("集合项间缺少逗号")

    @staticmethod
    def _hashable(key):
        """dict 键需可哈希：list/set 键转为紧凑 JSON 字符串"""
        if isinstance(key, (str, int, float, bool)) or key is None:
            return key
        return json.dumps(key, ensure_ascii=False, separators=(",", ":"))

    def _enum(self):
        # <Enum.VALUE: 'value'> -> 取 'value'；无值形式 <Enum.VALUE> -> 'Enum.VALUE'
        j = self.s.find(">", self.i)
        if j < 0:
            raise ValueError("枚举表示未闭合")
        content = self.s[self.i + 1:j].strip()
        self.i = j + 1
        if ": " in content or content.endswith(":"):
            _, _, val = content.rpartition(":")
            val = val.strip()
            if val:
                import ast
                try:
                    return ast.literal_eval(val)
                except (ValueError, SyntaxError):
                    return val
        return content

    def _atom(self):
        # 数字 / 标识符 / 构造器 ClassName(...)
        j = self.i
        if self.s[j] in "+-":
            j += 1
        num_start = j
        while j < self.n and (self.s[j].isdigit() or self.s[j] in ".eE+-_"):
            # eE 后允许符号；简化处理：交给 literal_eval 验证
            if self.s[j] in "+-" and self.s[j - 1] not in "eE":
                break
            j += 1
        if j > num_start and self.s[num_start:j].strip():
            token = self.s[self.i:j]
            self.i = j
            import ast
            try:
                return ast.literal_eval(token)
            except (ValueError, SyntaxError):
                self.i = num_start  # 不是数字，回退按标识符处理
        # 标识符（含点号）
        j = self.i
        if j < self.n and (self.s[j].isalpha() or self.s[j] == "_"):
            while j < self.n and (self.s[j].isalnum() or self.s[j] in "._"):
                j += 1
            name = self.s[self.i:j]
            self.i = j
            self._skip_ws()
            if self.i < self.n and self.s[self.i] == "(":
                return self._constructor(name)
            if name in ("True", "False", "None"):
                return {"True": True, "False": False, "None": None}[name]
            return name  # 裸标识符按字符串处理
        raise ValueError(f"无法识别的字符：{self.s[self.i]!r}")

    def _constructor(self, name):
        # ClassName(k=v, k2=v) -> {"_type": name, ...}；位置参数按 _0/_1 编号
        self.i += 1  # (
        # set({...}) / frozenset({...}) / list([...])：直接返回参数的集合/数组表示
        if name in ("set", "frozenset", "list", "tuple"):
            self._skip_ws()
            if self.i < self.n and self.s[self.i] in "[{(":
                val = self._value()
                self._skip_ws()
                if self.i >= self.n or self.s[self.i] != ")":
                    raise ValueError(f"{name}(...) 参数未闭合")
                self.i += 1
                return val
            # 空集合 set() / list()：返回空数组
            if self.i < self.n and self.s[self.i] == ")":
                self.i += 1
                return []
            # 带关键字参数的其他形式（罕见）：按普通构造器处理
        result = {"_type": name}
        pos_index = 0
        self._skip_ws()
        if self.i < self.n and self.s[self.i] == ")":
            self.i += 1
            return result
        while True:
            # 尝试 k=v 形式
            save = self.i
            key = None
            j = self.i
            if j < self.n and (self.s[j].isalpha() or self.s[j] == "_"):
                while j < self.n and (self.s[j].isalnum() or self.s[j] == "_"):
                    j += 1
                self._skip_ws_back(j)
                if self.i < self.n and self.s[self.i] == "=" and \
                        (self.i + 1 >= self.n or self.s[self.i + 1] != "="):
                    key = self.s[save:j]
                    self.i += 1
            if key is None:
                self.i = save
                key = f"_{pos_index}"
            result[key] = self._value()
            pos_index += 1
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("构造器参数未闭合")
            if self.s[self.i] == ")":
                self.i += 1
                return result
            if self.s[self.i] == ",":
                self.i += 1
                self._skip_ws()
                if self.i < self.n and self.s[self.i] == ")":
                    self.i += 1
                    return result
            else:
                raise ValueError("构造器参数间缺少逗号")

    def _skip_ws_back(self, j):
        """从标识符结束位置 j 向后跳过空白，更新 self.i"""
        while j < self.n and self.s[j] in self._WS:
            j += 1
        self.i = j


def _py_literal(value, depth):
    """递归将 JSON 值转为 Python 字面量文本"""
    indent = "    " * depth
    child_indent = "    " * (depth + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = []
        for k, v in value.items():
            items.append(f"{child_indent}'{k}': {_py_literal(v, depth + 1)}")
        return "{\n" + ",\n".join(items) + f"\n{indent}}}"
    if isinstance(value, list):
        if not value:
            return "[]"
        items = []
        for v in value:
            items.append(f"{child_indent}{_py_literal(v, depth + 1)}")
        return "[\n" + ",\n".join(items) + f"\n{indent}]"
    return _literal_scalar(value)


def _literal_scalar(value):
    """将 JSON 标量转成 Python 字面量（bool/None/str/int/float）"""
    if value is True:
        return "True"
    if value is False:
        return "False"
    if value is None:
        return "None"
    return repr(value)


def _char_width(ch):
    """单字符显示宽度：中日韩等全角字符按 2 计算"""
    return 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1


@lru_cache(maxsize=2048)
def _display_width(s):
    """计算字符串显示宽度：中日韩等全角字符按 2 计算"""
    return sum(_char_width(ch) for ch in s)


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
            # 键并集做表头（dict.fromkeys 保持首次出现顺序且去重）
            headers = list(dict.fromkeys(k for item in data for k in item))
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
    out = ""
    w = 0
    for ch in s:
        cw = _char_width(ch)
        if w + cw > width - 1:
            break
        out += ch
        w += cw
    return out + "…"


# ══════════════════════════════════════════════════════
#  XML
# ══════════════════════════════════════════════════════

def xml_format(text):
    """格式化 XML：统一缩进美化（保留注释与声明）"""
    import xml.dom.minidom as minidom
    # minidom 解析即校验：非法 XML 会抛 ExpatError，由路由层统一转中文提示
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
    return re.sub(r">\s+<", "><", ET.tostring(root, encoding="unicode")).replace(" />", "/>")


# ══════════════════════════════════════════════════════
#  YAML（可选依赖 PyYAML）
# ══════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════
#  工具动作路由（UI 无关，供 Tkinter / Web 两端复用）
# ══════════════════════════════════════════════════════

def _friendly_error(action_key, error):
    """把常见解析异常翻译成中文友好提示"""
    msg = str(error)
    looks_like_yaml = msg.startswith(("Expected a key", "could not find expected", "mapping values"))
    looks_like_json = msg.startswith(("Expecting value", "Expecting property name",
                                      "Extra data", "Invalid control character",
                                      "Unexpected UTF-8 BOM", "Unterminated string"))
    # 输入疑似 YAML 却喂给了 JSON 动作（用户反馈的核心连用场景）
    if looks_like_json and action_key == "json_to_yaml":
        return ("输入内容不是合法的 JSON——看起来像 YAML（无引号键/无大括号）。\n"
                "请改用「YAML 美化」或「YAML → JSON」，或检查后重试。\n原始错误：" + msg)
    if looks_like_json:
        if action_key == "yaml_to_json":
            return "输入内容不是合法的 YAML（看起来更像 JSON，请改用「JSON → YAML」）：" + msg
        return "JSON 解析失败，请检查格式（键和字符串需用双引号、不能有尾随逗号）：" + msg
    if looks_like_yaml:
        if action_key == "json_to_yaml":
            return "输入内容不是合法的 JSON（看起来更像 YAML）：" + msg
        return "YAML 解析失败，请检查缩进和冒号后空格：" + msg
    if action_key == "python_to_json":
        # literal_eval 抛出的异常均为解析失败（SyntaxError/ValueError）
        return ("输入内容不是合法的 Python 字面量（需为字典/列表，True/False/None 大写开头、"
                "字符串用单引号或双引号）：" + msg)
    return msg


# 动作路由表：action key → 处理函数（tree 返回原始 JSON 数据，由前端渲染）
_ACTIONS = {
    "base64_encode": base64_encode,
    "base64_decode": base64_decode,
    "url_encode": url_encode,
    "url_decode": url_decode,
    "html_encode": html_encode,
    "html_decode": html_decode,
    "unicode_encode": unicode_encode,
    "unicode_decode": unicode_decode,
    "hex_encode": hex_encode,
    "hex_decode": hex_decode,
    "md5": md5_hash,
    "sha256": sha256_hash,
    "jwt_decode": jwt_decode,
    "format": json_format,
    "table": json_to_table,
    "python": json_to_python,
    "python_to_json": python_to_json,
    "tree": json.loads,
    "xml_format": xml_format,
    "xml_compress": xml_compress,
    "yaml_format": yaml_format,
    "yaml_to_json": yaml_to_json_text,
    "json_to_yaml": json_to_yaml_text,
}


def run_tool_action(action_key, raw_text):
    """执行工具动作。返回 (ok, 结果)；
    失败返回 (False, 错误消息)。"""
    fn = _ACTIONS.get(action_key)
    if fn is None:
        return False, f"未知操作：{action_key}"
    try:
        return True, fn(raw_text)
    except Exception as e:
        return False, _friendly_error(action_key, str(e) or e.__class__.__name__)


# ══════════════════════════════════════════════════════
#  配置读写（标签顺序 + 主题）
# ══════════════════════════════════════════════════════

def _config_path():
    """配置文件路径：%APPDATA%\\ToolBox\\config.json（兼容读取旧 EncodeTool 目录）"""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    new_path = os.path.join(base, "ToolBox", "config.json")
    if os.path.exists(new_path):
        return new_path
    legacy = os.path.join(base, "EncodeTool", "config.json")
    if os.path.exists(legacy):
        return legacy
    return new_path


def _read_config():
    """读取整个配置文件，失败返回空 dict"""
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_tab_order(group_names, saved_order=None):
    """读取保存的标签顺序。返回与 group_names 对齐的 {组名: [标签名...]}，
    无效/缺失的组回退为默认顺序。saved_order 可传入已读出的 tab_order 字典
    （避免重复读文件），缺省时自行读取。"""
    defaults = {g: list(names) for g, names in group_names.items()}
    saved = saved_order if saved_order is not None else _read_config().get("tab_order", {})
    for group, names in defaults.items():
        order = saved.get(group)
        # 只有当顺序恰好是同一组标签（无增删）时才采用
        if isinstance(order, list) and sorted(order) == sorted(names):
            defaults[group] = order
    return defaults


def save_tab_order(order):
    """保存标签顺序到配置文件（失败静默，不影响退出）"""
    _update_config(lambda data: data.update(tab_order=order))


def load_theme():
    """读取主题偏好：'dark' / 'light' / None（未设置）"""
    theme = _read_config().get("theme")
    return theme if theme in ("dark", "light") else None


def save_theme(theme):
    """保存主题偏好（失败静默）"""
    _update_config(lambda data: data.update(theme=theme))


def get_config():
    """一次性读取整套配置：主题 + 分组标签顺序（单次文件读取）"""
    data = _read_config()
    theme = data.get("theme")
    theme = theme if theme in ("dark", "light") else None
    order = data.get("tab_order", {})
    return {"theme": theme, "tab_order": order}


def _update_config(mutator):
    """合并更新配置文件（失败静默）"""
    try:
        path = _config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = _read_config()
        mutator(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
