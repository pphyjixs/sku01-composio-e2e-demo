# DESIGN.md — QINGYOU STUDIO / 青釉手作工坊

> 标准对齐：Shopify / Google Labs `DESIGN.md` 视觉契约  
> 主题风格：暖暗陶土极简美学（Warm Dark Terracotta Minimalism）  
> 适用端口：桌面 Web (`1440×900`) · 电脑微信内置 (`880px`) · 手机 H5 (`390×844`) · 微信小程序安全区 (`87×32pt`)

---

## 1. CSS `:root` 语义变量表（唯一允许出现 `#HEX` 的区域）

```css
:root {
  --bg-canvas: #12100E;
  --bg-surface: #1B1815;
  --bg-elevated: #24201C;
  --text-primary: #F3ECE2;
  --text-muted: #B6ABA0;
  --accent: #C87D55;
  --accent-hover: #D98E66;
  --border: #332D27;
  --danger: #E06C65;
  --success: #6BAF8D;
  --radius: 2px;
  --font-display: "Playfair Display", "Noto Serif SC", "Songti SC", Georgia, serif;
  --font-sans: "Inter", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
}
```

### 对比度门禁校验（WCAG AA ≥ 4.5:1）
- `--text-primary (#F3ECE2)` on `--bg-canvas (#12100E)` ≈ **16.1 : 1**（通过）
- `--text-muted (#B6ABA0)` on `--bg-canvas (#12100E)` ≈ **8.3 : 1**（通过）
- `--bg-canvas (#12100E)` text on `--accent (#C87D55)` ≈ **5.6 : 1**（通过）

---

## 2. 排版与字阶规范（限 2 套字体家族 · 4 级字号 · 统一 2px 建筑直角）

1. **Display Hero (`h1`)**：`clamp(2rem, 4vw, 3.25rem)`，行高 `1.15`，`var(--font-display)`，字重 `600`。
2. **Section Heading (`h2`)**：`clamp(1.5rem, 2.5vw, 2.125rem)`，行高 `1.25`，`var(--font-display)`。
3. **Body / Lead Copy**：`1rem` (`16px`)，行高 `1.7`，`var(--font-sans)`；所有表单输入控件强制 `font-size: 16px` 防 iOS 缩放。
4. **Eyebrow / Caption**：`0.75rem` (`12px`)，`letter-spacing: 0.12em`，大写微距展示。
5. **全局曲率锁死**：按钮、卡片、输入框统一 `border-radius: var(--radius);`（`2px` 硬朗建筑直角），严禁私改圆角胶囊卡片。

---

## 3. 摄影主图与保护遮罩契约

- **首屏主图**：`assets/hero-vessel.jpg`（`1440×810`），左侧 48% 为 `#12100E` 暗褐负空间，右侧 52% 为侧光青釉茶器；叠加线性渐暗保护层（`rgba(18,16,14,0.88) -> rgba(18,16,14,0.18)`）保证左区排版文字高对比无压字，同时保持器物右侧高光透亮。
- **工艺配图**：`assets/craft-detail.jpg`（`960×720`），呈现匠人拉坯湿泥质感。

---

## 4. 可被自动化脚本硬校验的 Dos & Don'ts 红线（≥ 5 条）

1. **零裸写 `#HEX` 红线**：`styles.css` 除顶部 `:root { ... }` 块内部以外，**绝对禁止**出现任何裸 `#HEX` 色值；`index.html` 中不得出现任何 `style="...#..."` 内联十六进制颜色。
2. **严禁伪造 SVG 假主图**：首屏与工艺区块必须真实渲染 `assets/hero-vessel.jpg` 与 `assets/craft-detail.jpg`（`naturalWidth > 0`），严禁使用几何 SVG 图形冒充产品摄影主图。
3. **管理后台零公网暴露**：公网页面、`index.html` 与 `app.js` 中**绝对禁止**出现 `/admin.html` 路径或无鉴权读取列表请求；访客端仅允许触发只写接口 `POST /api/leads`。
4. **区块局部锁标记**：所有主区块必须显式声明 `data-section-id`（`header`、`hero`、`story`、`sessions`、`booking-form`、`faq`、`footer`），`4→3` 返修时只改被打回区块，严禁重排无关区块。
5. **微信小程序胶囊安全区**：在 `@media (max-width: 640px)` 及小程序模拟视图下，顶栏必须设置 `padding-right: 96px;`，确保右上角导航动作严格避开 `87×32pt` 小程序胶囊按钮。
