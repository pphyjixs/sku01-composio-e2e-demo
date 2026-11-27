# DESIGN.md — 智工精密 ZHIGONG PRECISION

> 版本 1.0.0 · 设计系统规范 · 适用于 Web / H5 / 小程序跨端实现
> 视觉主题：极简工业直角科技风（Minimal Industrial Right-Angle Tech）

---

## 1. 设计令牌（Design Tokens）

### 1.1 CSS `:root` 语义变量表

所有业务样式必须且只能通过以下语义变量取色、取圆角。变量名不可重命名，值不可在业务层覆写。

```css
:root {
  /* ---- 背景 ---- */
  --bg-canvas: #F4F4F5;      /* 页面画布底色（浅灰） */
  --bg-surface: #FFFFFF;     /* 卡片 / 面板 / 浮层表面 */

  /* ---- 文本 ---- */
  --text-primary: #18181B;   /* 主文本、标题 */
  --text-muted: #52525B;     /* 次级文本、说明、占位 */

  /* ---- 强调 ---- */
  --accent: #2563EB;         /* 主操作、链接、焦点环、数据高亮 */

  /* ---- 形状 ---- */
  --radius: 2px;             /* 全局唯一圆角基准（直角工业风） */

  /* ---- 派生（由上述令牌计算，禁止硬编码） ---- */
  --border-subtle: color-mix(in srgb, var(--text-primary) 12%, transparent);
  --accent-hover: color-mix(in srgb, var(--accent) 88%, #000);
  --focus-ring: 0 0 0 2px var(--bg-surface), 0 0 0 4px var(--accent);
}
```

### 1.2 对比度合规声明

正文与背景对比度 **>= 4.5:1**（WCAG 2.1 AA 正文级）：

| 前景 | 背景 | 对比度 | 结论 |
|---|---|---|---|
| `--text-primary` #18181B | `--bg-canvas` #F4F4F5 | ≈ 15.9:1 | ✅ AAA |
| `--text-primary` #18181B | `--bg-surface` #FFFFFF | ≈ 17.4:1 | ✅ AAA |
| `--text-muted` #52525B | `--bg-canvas` #F4F4F5 | ≈ 7.1:1 | ✅ AAA |
| `--text-muted` #52525B | `--bg-surface` #FFFFFF | ≈ 7.8:1 | ✅ AAA |
| `--accent` #2563EB | `--bg-surface` #FFFFFF | ≈ 5.2:1 | ✅ AA（正文可用） |

> 约束：`--accent` 仅用于 ≥ 16px 正文或非文本元素；若用于小号文本，须叠加 `--text-primary` 或加粗至 600 字重。禁止将 `--text-muted` 用于小于 12px 的文本。

---

## 2. 字体层级（Typography Scale）

字体栈：`Inter`（拉丁）+ `Noto Sans SC`（中文），回退系统无衬线。

```css
:root {
  --font-sans: "Inter", "Noto Sans SC", -apple-system, "Segoe UI",
               "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
}
```

| 层级 | 令牌 | 字号 / 行高 | 字重 | 字距 | 用途 |
|---|---|---|---|---|---|
| Display | `--fs-display` | 56px / 1.05 | 700 | -0.02em | Hero 主标题 |
| H1 | `--fs-h1` | 40px / 1.15 | 700 | -0.01em | 页面标题 |
| H2 | `--fs-h2` | 28px / 1.25 | 600 | 0 | 区块标题 |
| H3 | `--fs-h3` | 20px / 1.35 | 600 | 0 | 卡片标题 |
| Body | `--fs-body` | 16px / 1.6 | 400 | 0 | 正文 |
| Small | `--fs-small` | 14px / 1.5 | 400 | 0 | 辅助说明 |
| Caption | `--fs-caption` | 12px / 1.4 | 500 | 0.04em | 标签、元信息（大写英文） |
| Mono | `--fs-mono` | 14px / 1.5 | 500 | 0 | 参数、型号、序列号 |

规则：
- 中文正文行高不低于 1.6；英文标题行高可收紧至 1.05–1.15。
- 数字与型号（如 `ZG-TC200`）统一使用 `--font-mono`，保证等宽对齐。
- 禁止使用斜体；强调通过字重（600/700）与 `--accent` 表达。

### 2.1 圆角规则（Radius Rules）

- 全局唯一圆角基准 `--radius: 2px`，体现直角工业风。
- 允许值仅三种：`0`（表格、分隔线、全宽区块）、`var(--radius)`（按钮、输入框、卡片、标签）、`9999px`（仅限头像与状态圆点）。
- **禁止**出现 `4px / 8px / 12px / 16px` 等中间圆角值；禁止 `border-radius: 50%` 用于非圆形元素。
- 阴影与圆角解耦：卡片默认无阴影，用 `1px solid var(--border-subtle)` 描边区分层级。

---

## 3. Dos & Don'ts（可被脚本静态检查）

以下三条规则须由 CI 中的静态 Linter 强制执行，任一违规即构建失败。

### 规则 1 — 业务 CSS 严禁裸写 HEX 色值

- **Do**：业务样式一律引用语义变量，如 `color: var(--text-primary);`、`background: var(--bg-surface);`。
- **Don't**：在 `:root` 之外的任何 `.css / .scss / .less / <style>` 中出现 `#RGB`、`#RRGGBB`、`#RRGGBBAA` 字面量。
- **静态检查**：正则 `#[0-9a-fA-F]{3,8}\b` 扫描除 `:root` 块外的全部样式源；命中即报错 `E-