# DESIGN.md — QINGYOU STUDIO / 青釉手作工坊

> 版本 1.0.0 · 主题：暖暗陶土极简美学 (Warm Dark Terracotta Minimalism)
> 适用端：Web (Desktop / Mobile) · 微信小程序 · 静态 Linter 校验目标

---

## 1. 设计令牌 (Design Tokens)

### 1.1 CSS `:root` 语义变量表

```css
:root {
  /* ===== 画布与表面 ===== */
  --bg-canvas: #12100E;        /* 页面底色：暖暗褐黑 */
  --bg-surface: #1C1917;       /* 卡片 / 面板 / 顶栏表面 */

  /* ===== 文本 ===== */
  --text-primary: #FAF9F6;     /* 主文本：暖白 */
  --text-muted: #A8A29E;       /* 次要文本 / 说明 / 占位 */

  /* ===== 强调色 ===== */
  --accent: #D97757;           /* 陶土橙：CTA / 链接 / 焦点环 */

  /* ===== 形状 ===== */
  --radius: 0px;               /* 全局直角，禁止圆角 */

  /* ===== 派生令牌（仅供内部引用，业务层只允许使用上方语义变量） ===== */
  --border-subtle: color-mix(in srgb, var(--text-muted) 24%, transparent);
  --accent-contrast: #12100E;  /* 强调色上的文字色 */
  --focus-ring: 0 0 0 2px var(--bg-canvas), 0 0 0 4px var(--accent);
}
```

### 1.2 对比度合规声明

| 前景 | 背景 | 对比度 | 结论 |
|---|---|---|---|
| `--text-primary` `#FAF9F6` | `--bg-canvas` `#12100E` | ≈ 17.8:1 | ✅ AAA |
| `--text-primary` `#FAF9F6` | `--bg-surface` `#1C1917` | ≈ 15.9:1 | ✅ AAA |
| `--text-muted` `#A8A29E` | `--bg-canvas` `#12100E` | ≈ 7.4:1 | ✅ AAA |
| `--text-muted` `#A8A29E` | `--bg-surface` `#1C1917` | ≈ 6.6:1 | ✅ AA |
| `--accent` `#D97757` | `--bg-canvas` `#12100E` | ≈ 5.6:1 | ✅ AA（正文可用） |
| `--accent-contrast` `#12100E` | `--accent` `#D97757` | ≈ 5.6:1 | ✅ AA（按钮文字） |

**硬性约束：正文（`font-size < 24px` 或 `font-weight < 700`）与背景对比度必须 ≥ 4.5:1。** 任何新增色值须先通过 WCAG 2.1 计算并登记于本表，方可进入 `:root`。

---

## 2. 字体层级 (Type Scale)

字体栈：`"Playfair Display", "PingFang SC", "Noto Serif SC", serif`（标题）· `"PingFang SC", "Noto Sans SC", system-ui, sans-serif`（正文）

| Token | 字号 / 行高 | 字重 | 字族 | 用途 |
|---|---|---|---|---|
| `--type-display` | 64px / 1.05 | 400 | Playfair Display | Hero 主标题（桌面） |
| `--type-h1` | 40px / 1.15 | 400 | Playfair Display | 页面标题 |
| `--type-h2` | 28px / 1.25 | 500 | Playfair Display | 区块标题 |
| `--type-h3` | 20px / 1.35 | 600 | PingFang SC | 卡片标题 |
| `--type-body` | 16px / 1.7 | 400 | PingFang SC | 正文 |
| `--type-caption` | 13px / 1.5 | 400 | PingFang SC | 说明 / 图注（用 `--text-muted`） |
| `--type-label` | 12px / 1.2 | 600 | PingFang SC | 全大写标签，`letter-spacing: 0.12em` |

移动端断点 `≤ 768px`：`display → 40px`，`h1 → 32px`，`h2 → 24px`，其余不变。

### 2.1 圆角规则

- **全局 `--radius: 0px`。** 所有容器、按钮、输入框、图片、卡片一律直角。
- 禁止使用 `border-radius` 字面量（含 `50%`、`9999px`、`8px` 等）；如需圆形头像等例外，须在 `:root` 新增语义令牌（如 `--radius-avatar`）并在此登记，业务层仅引用令牌。
- 视觉分隔优先使用 `1px solid var(--border-subtle)` 而非圆角或阴影。

---

## 3. Dos & Don'ts（可被脚本静态检查）

### 规则 1 — 业务 CSS 严禁裸写 `#HEX` 色值

- **Do**：业务样式一律引用语义变量，如 `color: var(--text-primary); background: var(--bg-surface);`
- **Don't**：在 `:root` 之外的任何 `.css / .scss / .vue / .tsx` 样式中出现 `#RRGGBB`、`#RGB`、`rgb()`、`hsl()` 字面量。
- **静态检查**：对 `src/**/*.{css,scss,vue,tsx,jsx}` 执行正则 `/#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/`，命中且所在文件非 `tokens.css`（仅含 `:root`）即报错 `E_COLOR_LITERAL`。

### 规则 2 — 公网页面严禁包含 `/admin.html` 管理后台入口

- **Do**：后台入口仅通过独立域名 / 内网路由 / 环境变量注入，公网构建产物中不出现该路径。
- **Don't**：在公网页面 HTML、导航、`<a href>`、JS