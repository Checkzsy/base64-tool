/* ═══════════════════════════════════════════════════
   ToolBox v3.0 前端逻辑
   工具注册表 / 切换 / 拖拽排序 / 主题 / 树渲染 / toast
   ═══════════════════════════════════════════════════ */

// ── 工具注册表（action key 与 tools.run_tool_action 对齐）──
const TOOLS = {
  encoders: [
    { id: "Base64",  desc: "Base64 编码 / 解码", actions: [
      { label: "编码", key: "base64_encode", style: "primary" },
      { label: "解码", key: "base64_decode", style: "green" } ] },
    { id: "URL",  desc: "URL 百分号编码 / 解码", actions: [
      { label: "编码", key: "url_encode", style: "primary" },
      { label: "解码", key: "url_decode", style: "green" } ] },
    { id: "HTML",  desc: "HTML 实体编码 / 解码", actions: [
      { label: "编码", key: "html_encode", style: "primary" },
      { label: "解码", key: "html_decode", style: "green" } ] },
    { id: "Unicode",  desc: "Unicode 转义 / 反转义", actions: [
      { label: "编码", key: "unicode_encode", style: "primary" },
      { label: "解码", key: "unicode_decode", style: "green" } ] },
    { id: "Hex",  desc: "十六进制编码 / 解码", actions: [
      { label: "编码", key: "hex_encode", style: "primary" },
      { label: "解码", key: "hex_decode", style: "green" } ] },
    { id: "MD5",  desc: "MD5 哈希生成（单向）", actions: [
      { label: "生成哈希", key: "md5", style: "primary" } ] },
    { id: "SHA-256",  desc: "SHA-256 哈希生成（单向）", actions: [
      { label: "生成哈希", key: "sha256", style: "primary" } ] },
    { id: "JWT",  desc: "解析 JWT（不验签）", actions: [
      { label: "解析", key: "jwt_decode", style: "green" } ] },
  ],
  formatters: [
    { id: "JSON",  desc: "格式化 / 转表格 / 转字典 / 转JSON / 树形视图", actions: [
      { label: "格式化", key: "format", style: "primary" },
      { label: "转表格", key: "table", style: "green" },
      { label: "转字典", key: "python", style: "purple" },
      { label: "转JSON", key: "python_to_json", style: "green" },
      { label: "树形表格", key: "tree", style: "gray" } ] },
    { id: "XML",  desc: "XML 格式化 / 压缩", actions: [
      { label: "格式化", key: "xml_format", style: "primary" },
      { label: "压缩", key: "xml_compress", style: "green" } ] },
    { id: "YAML",  desc: "YAML 美化 / YAML ⇄ JSON", actions: [
      { label: "YAML 美化", key: "yaml_format", style: "primary" },
      { label: "YAML → JSON", key: "yaml_to_json", style: "green" },
      { label: "JSON → YAML", key: "json_to_yaml", style: "purple" } ],
      // 当输入为合法 JSON 时，动态解锁 JSON 工具按钮（复用 JSON 工具定义）
      dynamic: { when: isJsonText, actions: jsonExtraActions } },
  ],
};

const ALL_IDS = {};
for (const g of Object.keys(TOOLS))
  TOOLS[g].forEach(t => { ALL_IDS[t.id] = t; });

// YAML 动态解锁：输入为合法 JSON 时复用 JSON 工具的动作（引用同一份定义，不重复维护）。
// 用函数声明（提升）以便 TOOLS 注册表可直接引用；函数体内的 ALL_IDS 为惰性求值。
function jsonExtraActions() {
  // 排除 format（与 YAML 美化重复）与 python_to_json（输入已是 JSON，无需再转）
  return ALL_IDS["JSON"].actions.filter(a => a.key !== "format" && a.key !== "python_to_json")
    .map(a => ({ ...a, label: `JSON ${a.label}` }));
}

// ── 全局状态 ──
const state = {
  current: "Base64",
  yamlAvailable: true,
  toastTimer: null,
};

const $ = (id) => document.getElementById(id);

// ── 后端桥接（pywebview 注入）──
function backend() {
  return window.pywebview?.api;
}

// ── 初始化 ──
window.addEventListener("DOMContentLoaded", async () => {
  renderNav("encoders");
  renderNav("formatters");
  bindGlobal();
  selectTool("Base64", true);

  // 读配置：主题 + 顺序 + YAML 可用性
  let cfg = null;
  try {
    cfg = await backend()?.get_config();
  } catch {}
  if (cfg) {
    state.yamlAvailable = cfg.yamlAvailable !== false;
    if (cfg.order) applyOrder(cfg.order);
  }
  initTheme(cfg?.theme ?? null);
  if (!state.yamlAvailable) {
    TOOLS.formatters.find(t => t.id === "YAML").desc +=
      "（未安装 PyYAML，请先 pip install pyyaml）";
    $("tool-desc").textContent = ALL_IDS[state.current].desc;
  }
});

// ── 侧边栏渲染 ──
function renderNav(group) {
  const ul = $(`nav-${group}`);
  ul.innerHTML = "";
  for (const tool of TOOLS[group]) {
    const li = document.createElement("li");
    li.className = "nav-item";
    li.textContent = tool.id;
    li.draggable = true;
    li.dataset.id = tool.id;
    li.addEventListener("click", () => selectTool(tool.id));
    bindDrag(li, ul);
    ul.appendChild(li);
  }
}

// ── 工具切换 ──
function selectTool(id, silent) {
  state.current = id;
  const tool = ALL_IDS[id];

  document.querySelectorAll(".nav-item").forEach(el =>
    el.classList.toggle("active", el.dataset.id === id));

  $("tool-title").textContent = id;
  $("tool-desc").textContent = tool.desc;

  // 渲染按钮（容器一次性淡入，无逐个级联）
  renderActions(tool);
  clearOutput();
  if (!silent) $("input").focus();
}

// ── 按钮渲染（含动态按钮注入）──
// 工具可通过 registry `dynamic: { when(input), actions() }` 声明条件按钮；
// 由 input-to-render 时求值（YAML 工具在输入为合法 JSON 时附加 JSON 按钮）。
function renderActions(tool) {
  const box = $("actions");
  box.innerHTML = "";
  let actions = tool.actions;
  if (tool.dynamic && tool.dynamic.when($("input").value)) {
    actions = [...tool.actions, ...tool.dynamic.actions()];
  }
  for (const act of actions) {
    const btn = document.createElement("button");
    btn.className = `action-btn ${act.style}`;
    btn.textContent = act.label;
    btn.addEventListener("click", () => runAction(act.key));
    box.appendChild(btn);
  }
}

// 输入检查：仅当前工具带动态按钮（且输入变化）时才重算，避免每次按键整份 JSON.parse
const _jsonCheckMemo = { text: "", ok: false };
function isJsonText(text) {
  if (!text || !text.trim()) return false;
  if (_jsonCheckMemo.text === text) return _jsonCheckMemo.ok;
  const t = text.trim();
  const ok = (t.startsWith("{") || t.startsWith("[")) && (() => {
    try { JSON.parse(t); return true; } catch { return false; }
  })();
  _jsonCheckMemo.text = text;
  _jsonCheckMemo.ok = ok;
  return ok;
}

function hasDynamic(tool) {
  return !!(tool.dynamic && tool.dynamic.when);
}

// ── 执行动作 ──
async function runAction(key) {
  const text = $("input").value;
  if (!text.trim()) { toast("请输入内容", "error"); return; }

  const api = backend();
  if (!api) { toast("后端未就绪", "error"); return; }

  let res;
  try {
    res = await api.run_tool(key, text);
  } catch (e) {
    toast(`调用失败：${e}`, "error");
    return;
  }

  if (!res.ok) {
    // 友好错误提示：toast 提示摘要，详细原因显示在输出区
    toast("操作失败，详见输出区说明", "error");
    showOutputText("✗ " + (res.error || "操作失败"));
    return;
  }

  if (key === "tree") {
    showTree(res.result);
  } else {
    showOutputText(typeof res.result === "string"
      ? res.result : JSON.stringify(res.result, null, 2));
  }
  toast("操作成功", "success");
}

// ── 输出区持有态：tool 类决定 textarea/树谁可见（CSS 负责显隐）──
function showOutputText(text) {
  $("output-card").classList.remove("tree-mode");
  $("output").value = text;
  $("output-card").hidden = false;
}

// ── 树渲染（同层括号 + 折叠计数）──
function showTree(data) {
  $("output-card").classList.add("tree-mode");
  const box = $("tree");
  box.innerHTML = "";
  box.appendChild(buildNode(data, null));
  $("output-card").hidden = false;
}

function buildNode(value, key) {
  if (value && typeof value === "object") {
    const isArray = Array.isArray(value);
    const entries = Object.entries(value);
    const openCh = isArray ? "[" : "{";
    const closeCh = isArray ? "]" : "}";

    const details = document.createElement("details");
    details.open = true;

    const summary = document.createElement("summary");
    const arrow = document.createElement("span");
    arrow.className = "arrow";
    arrow.textContent = "▶";
    summary.appendChild(arrow);
    appendKey(summary, key);
    // 展开态：{ ；折叠态：{…n 项}
    const openBracket = document.createElement("span");
    openBracket.className = "bracket";
    openBracket.textContent = openCh;
    summary.appendChild(openBracket);
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = `${entries.length} 项 ${closeCh}`;
    summary.appendChild(badge);
    // 折叠时显示徽标，展开时隐藏
    const syncBadge = () => { badge.hidden = details.open; };
    details.addEventListener("toggle", syncBadge);
    syncBadge();

    details.appendChild(summary);
    const frag = document.createDocumentFragment();
    // 单次遍历 entries（无需 Object.keys 单独再数一遍）
    for (const [k, v] of entries)
      frag.appendChild(buildNode(v, isArray ? `[${k}]` : k));
    details.appendChild(frag);

    // 闭括号行
    const closeLine = document.createElement("div");
    closeLine.className = "leaf";
    closeLine.style.paddingLeft = "6px";
    const close = document.createElement("span");
    close.className = "bracket";
    close.textContent = closeCh;
    closeLine.appendChild(close);
    details.appendChild(closeLine);
    return details;
  }

  const leaf = document.createElement("div");
  leaf.className = "leaf";
  appendKey(leaf, key);
  const val = document.createElement("span");
  val.className = "val";
  val.textContent = JSON.stringify(value) ?? String(value);
  leaf.appendChild(val);
  return leaf;
}

function appendKey(parent, key) {
  if (key === null) return;
  const span = document.createElement("span");
  span.className = "key";
  span.textContent = key + ": ";
  parent.appendChild(span);
}

// ── 拖拽排序 ──
const clearDropTargets = () =>
  document.querySelectorAll(".nav-item.drop-target")
    .forEach(el => el.classList.remove("drop-target"));

function bindDrag(item, ul) {
  item.addEventListener("dragstart", e => {
    item.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", item.dataset.id);
  });
  item.addEventListener("dragend", () => {
    item.classList.remove("dragging");
    clearDropTargets();
    persistOrder();
  });
  item.addEventListener("dragover", e => {
    e.preventDefault();
    const dragging = ul.querySelector(".dragging");
    if (!dragging || dragging === item) return;
    clearDropTargets();
    item.classList.add("drop-target");
    // 实时换位
    const rect = item.getBoundingClientRect();
    const after = (e.clientY - rect.top) > rect.height / 2;
    ul.insertBefore(dragging, after ? item.nextSibling : item);
  });
}

function applyOrder(order) {
  for (const group of Object.keys(TOOLS)) {
    const names = order[group];
    if (!Array.isArray(names)) continue;
    const ul = $(`nav-${group}`);
    const byId = {};
    [...ul.children].forEach(li => byId[li.dataset.id] = li);
    // 仅当标签集合一致时应用
    if (names.length !== ul.children.length ||
        !names.every(n => byId[n])) continue;
    names.forEach(n => ul.appendChild(byId[n]));
  }
}

async function persistOrder() {
  const order = {};
  for (const group of Object.keys(TOOLS))
    order[group] = [...$(`nav-${group}`).children].map(li => li.dataset.id);
  try { await backend()?.save_order(order); } catch {}
}

// ── 主题 ──
function initTheme(saved) {
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = saved || (systemDark ? "dark" : "light");
  document.documentElement.dataset.theme = theme;
  $("theme-btn").textContent = theme === "dark" ? "☀" : "☾";
}

async function toggleTheme() {
  const cur = document.documentElement.dataset.theme;
  const next = cur === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  $("theme-btn").textContent = next === "dark" ? "☀" : "☾";
  try { await backend()?.set_theme(next); } catch {}
}

// ── 全局绑定 ──
function bindGlobal() {
  $("theme-btn").addEventListener("click", toggleTheme);

  // 传回输入：把当前结果送回输入框，便于连续多步处理
  $("btn-toinput").addEventListener("click", () => {
    const out = getOutputText();
    if (!out) { toast("暂无结果可传回", "error"); return; }
    $("input").value = out;
    clearOutput();
    renderActions(ALL_IDS[state.current]);  // 立即刷新（YAML→JSON 后解锁 JSON 按钮）
    $("input").focus();
    toast("已传回输入框", "success");
  });

  $("btn-copy").addEventListener("click", async () => {
    const out = getOutputText();
    if (!out) { toast("暂无结果可复制", "error"); return; }
    try {
      await navigator.clipboard.writeText(out);
      toast("已复制到剪贴板", "success");
    } catch {
      // WebView2 下降级：选中文本 + execCommand
      $("output").select();
      document.execCommand("copy");
      toast("已复制到剪贴板", "success");
    }
  });

  $("btn-clear").addEventListener("click", () => {
    $("input").value = "";
    clearOutput();
  });

  $("btn-paste").addEventListener("click", async () => {
    try {
      $("input").value = await navigator.clipboard.readText();
      toast("已粘贴", "success");
    } catch {
      toast("无法读取剪贴板", "error");
    }
  });

  // Ctrl+Enter 快捷执行第一个动作
  $("input").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      const first = ALL_IDS[state.current].actions[0];
      if (first) runAction(first.key);
    }
  });

  // 输入变化时刷新动作按钮（仅带 dynamic 的工具需要重算；其余工具按钮不变，跳过重建）
  let inputDebounce = null;
  $("input").addEventListener("input", () => {
    if (!hasDynamic(ALL_IDS[state.current])) return;
    clearTimeout(inputDebounce);
    inputDebounce = setTimeout(() => {
      renderActions(ALL_IDS[state.current]);
    }, 250);
  });
}

function getOutputText() {
  // 树模式下导出层级文本，否则取输出框
  if (!$("output-card").classList.contains("tree-mode")) return $("output").value;
  const lines = [];
  const walk = (el, depth) => {
    for (const child of el.children) {
      if (child.tagName === "SUMMARY") {
        lines.push("  ".repeat(depth) + child.textContent.replace(/▶/g, "").trim());
        const details = child.parentElement;
        if (details.open) [...details.children].forEach(c => { if (c.tagName !== "SUMMARY") walk(c, depth + 1); });
      } else if (child.tagName === "DETAILS") {
        walk(child, depth);
      } else {
        lines.push("  ".repeat(depth) + child.textContent.trim());
      }
    }
  };
  walk($("tree"), 0);
  return lines.join("\n");
}

function clearOutput() {
  $("output").value = "";
  $("tree").innerHTML = "";
  $("output-card").classList.remove("tree-mode");
  $("output-card").hidden = true;
}

// ── toast ──
function toast(msg, type) {
  const el = $("toast");
  el.textContent = msg;
  el.className = `toast ${type || ""}`;
  el.hidden = false;
  requestAnimationFrame(() => el.classList.add("show"));
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => {
    el.classList.remove("show");
    setTimeout(() => { el.hidden = true; }, 250);
  }, 2000);
}
