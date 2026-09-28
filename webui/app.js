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
    { id: "JSON",  desc: "格式化 / 转表格 / 转字典 / 树形视图", actions: [
      { label: "格式化", key: "format", style: "primary" },
      { label: "转表格", key: "table", style: "green" },
      { label: "转字典", key: "python", style: "purple" },
      { label: "树形表格", key: "tree", style: "gray" } ] },
    { id: "XML",  desc: "XML 格式化 / 压缩", actions: [
      { label: "格式化", key: "xml_format", style: "primary" },
      { label: "压缩", key: "xml_compress", style: "green" } ] },
    { id: "YAML",  desc: "YAML 美化 / YAML ⇄ JSON", actions: [
      { label: "YAML 美化", key: "yaml_format", style: "primary" },
      { label: "YAML → JSON", key: "yaml_to_json", style: "green" },
      { label: "JSON → YAML", key: "json_to_yaml", style: "purple" } ] },
  ],
};

const ALL_IDS = {};
for (const g of Object.keys(TOOLS))
  TOOLS[g].forEach((t, i) => { ALL_IDS[t.id] = { group: g, index: i, ...t }; });

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
  try {
    const cfg = await backend()?.get_config();
    if (cfg) {
      state.yamlAvailable = cfg.yamlAvailable !== false;
      if (cfg.order) applyOrder(cfg.order);
      initTheme(cfg.theme);
    } else {
      initTheme(null);
    }
  } catch {
    initTheme(null);
  }
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

  // 面板切换动画：先移出再入场
  const ws = $("workspace");
  ws.style.animation = "none";
  void ws.offsetWidth; // reflow 重启动画
  ws.style.animation = "";

  $("tool-title").textContent = id;
  $("tool-desc").textContent = tool.desc;

  // 渲染按钮
  const box = $("actions");
  box.innerHTML = "";
  for (const act of tool.actions) {
    const btn = document.createElement("button");
    btn.className = `action-btn ${act.style}`;
    btn.textContent = act.label;
    btn.addEventListener("click", () => runAction(act.key));
    box.appendChild(btn);
  }

  clearOutput();
  if (!silent) $("input").focus();
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

  if (!res.ok) { toast(res.error || "操作失败", "error"); return; }

  if (key === "tree") {
    renderTree(res.result);
  } else {
    $("output").hidden = false;
    $("tree").hidden = true;
    $("output").value = typeof res.result === "string"
      ? res.result : JSON.stringify(res.result, null, 2);
  }
  $("output-card").hidden = false;
  toast("操作成功", "success");
}

// ── 树渲染（嵌套 details/summary）──
function renderTree(data) {
  $("output").hidden = true;
  const box = $("tree");
  box.hidden = false;
  box.innerHTML = "";
  box.appendChild(buildNode(data, null));
  $("output-card").hidden = false;
}

function buildNode(value, key) {
  const isObj = value && typeof value === "object";

  if (isObj) {
    const details = document.createElement("details");
    details.open = true;
    const summary = document.createElement("summary");
    const arrow = document.createElement("span");
    arrow.className = "arrow";
    arrow.textContent = "▶";
    summary.appendChild(arrow);
    appendKey(summary, key);
    summary.appendChild(document.createTextNode(
      Array.isArray(value) ? `[${value.length} 项]` : `{${Object.keys(value).length} 项}`));
    details.appendChild(summary);
    for (const [k, v] of Object.entries(value))
      details.appendChild(buildNode(v, Array.isArray(value) ? `[${k}]` : k));
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
function bindDrag(item, ul) {
  item.addEventListener("dragstart", e => {
    item.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", item.dataset.id);
  });
  item.addEventListener("dragend", () => {
    item.classList.remove("dragging");
    document.querySelectorAll(".nav-item.drop-target")
      .forEach(el => el.classList.remove("drop-target"));
    persistOrder();
  });
  item.addEventListener("dragover", e => {
    e.preventDefault();
    const dragging = ul.querySelector(".dragging");
    if (!dragging || dragging === item) return;
    document.querySelectorAll(".nav-item.drop-target")
      .forEach(el => el.classList.remove("drop-target"));
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

  $("btn-copy").addEventListener("click", async () => {
    const out = $("output").hidden ? "" : $("output").value;
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
}

function clearOutput() {
  $("output").value = "";
  $("tree").innerHTML = "";
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
