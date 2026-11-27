# DESIGN.md — 云栖茶事 (YUNQI TEA)

> 版本: 1.0.0 · 主题: 温润亚麻留白编辑风 · 标准对齐: Shopify Polaris / Google Labs Material 语义令牌规范
> 本文件为设计系统唯一事实来源 (Single Source of Truth)，所有业务 CSS 与页面结构须通过下方 Linter 规则静态校验。

---

## 1. 设计令牌 (Design Tokens)

### 1.1 CSS `:root` 语义变量表

```css
:root {
  /* ---- 画布与表面 ---- */
  --bg-canvas: #F3F1EC;      /* 页面底色：温润亚麻 */
  --bg-surface: #FAF9F6;     /* 卡片/浮层表面：留白纸感 */

  /* ---- 文本 ---- */
  --text-primary: #1C1917;   /* 主文本：墨黑 */
  --text-muted: #78716C;     /* 次要文本：灰褐 */

  /* ---- 强调色 ---- */
  --accent: #157F4B;         /* 茶青绿：CTA / 链接 / 选中态 */

  /* ---- 圆角 ---- */
  --radius: 10px;

  /* ---- 字体族 ---- */
  --font-serif: "Noto Serif SC", "PingFang SC", serif;
  --font-sans: "PingFang SC", "Noto Serif SC", sans-serif;

  /* ---- 安全区（微信小程序胶囊） ---- */
  --safe-capsule-w: 87pt;
  --safe-capsule-h: 32pt;
  --safe-top: calc(var(--safe-capsule-h) + 16px);
}
```

### 1.2 对比度校验（WCAG 2.1 AA）

| 前景 | 背景 | 对比度 | 结论 |
|---|---|---|---|
| `--text-primary` `#1C1917` | `--bg-canvas` `#F3F1EC` | ≈ 15.8:1 | ✅ 远超 4.5:1 |
| `--text-primary` `#1C1917` | `--bg-surface` `#FAF9F6` | ≈ 16.9:1 | ✅ 远超 4.5:1 |
| `--text-muted` `#78716C` | `--bg-canvas` `#F3F1EC` | ≈ 4.6:1 | ✅ 达标（正文/大字号） |
| `--accent` `#157F4B` | `--bg-surface` `#FAF9F6` | ≈ 5.1:1 | ✅ 达标（链接/按钮文字） |

> **约束**：正文文本与背景对比度 **必须 ≥ 4.5:1**；`--text-muted` 仅用于 ≥ 16px 或非关键信息，禁止用于正文段落。

---

## 2. 字体层级与圆角规则

### 2.1 字体层级 (Type Scale)

| 层级 | 令牌 | 字号 / 行高 | 字重 | 字体族 | 用途 |
|---|---|---|---|---|---|
| Display | `--type-display` | 40px / 1.2 | 600 | `--font-serif` | 竖排主标题、Hero |
| H1 | `--type-h1` | 28px / 1.3 | 600 | `--font-serif` | 页面标题 |
| H2 | `--type-h2` | 22px / 1.35 | 500 | `--font-serif` | 区块标题 |
| Body | `--type-body` | 16px / 1.7 | 400 | `--font-sans` | 正文 |
| Caption | `--type-caption` | 13px / 1.5 | 400 | `--font-sans` | 辅助说明（用 `--text-muted`） |

- 中文标题优先 `Noto Serif SC`，正文优先 `PingFang SC`，回退 `serif` / `sans-serif`。
- 字间距：标题 `letter-spacing: 0.02em`，正文 `0`。

### 2.2 圆角规则 (Radius)

- 全局唯一圆角令牌 `--radius: 10px`。
- 卡片、按钮、输入框、图片容器统一使用 `border-radius: var(--radius)`。
- 禁止出现 `border-radius: 4px / 8px / 999px` 等硬编码值（胶囊按钮除外，须用 `calc(var(--radius) * 2)` 或 `50%` 表达）。

---

## 3. Dos & Don'ts（可被脚本静态检查）

### 规则 1 — 禁止裸写 HEX 色值
- **Do**：业务 CSS 一律引用 `var(--bg-canvas)` / `var(--text-primary)` 等语义变量。
- **Don't**：除 `:root` 定义块外，任何 `.css` / `<style>` 中出现 `#` 开头的 3/6/8 位 HEX。
- **Linter 检查**：正则 `#[0-9a-fA-F]{3,8}\b`，排除 `:root { ... }` 区间；命中即 `error: raw-hex-color`。

### 规则 2 — 公网页面禁止后台入口
- **Do**：管理后台仅通过独立域名 / 鉴权路由访问，公网页面不暴露任何链接。
- **Don't**：公网 HTML/JS 中出现 `/admin.html`、`admin.html` 字符串或指向它的 `<a href>`。
- **Linter 检查**：对 `public/**/*.{html,js,jsx,ts,tsx,vue}` 扫描 `/admin\.html/`；命中即 `error: admin-entry-leak`。

### 规则 3 — 微信小程序胶囊安全区
- **Do**：顶栏与移动端首屏顶部预留 `87pt × 32pt` 胶囊安全区，使用 `padding-top: var(--safe-top)` 或 `env(safe-area-inset-top)` 叠加。
- **Don't**：顶栏内容（Logo、标题、操作按钮）侵入右上角胶囊区域；禁止 `padding-top: 0` 的移动端顶栏。
- **Linter 检查**：移动端顶栏选择器须包含 `--safe-capsule-w` / `--safe-capsule-h` 或 `--safe-top` 引用；缺失即 `error: capsule-safe-area-missing`。

---

## 4. Hero 主图生图 Prompt（16:9 · 英文 · 摄影级