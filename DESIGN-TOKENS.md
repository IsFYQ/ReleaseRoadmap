# 目标地图页面 Design Token 设计规范

> 命名空间 `--tm-*`（Target Map 专用），叠加在全局 `:root` 之上。
> 调性锚定：Modern Minimal（白底、无衬线、功能优先、精简聚合）+ Tech Utility（数据密度、等宽数字、紧凑表格、色编码密集）。

---

## A. 设计理念

这套 Token 的核心设计哲学是**「克制的信息分层」**——在一个 69 条数据 x 11 字段的高密度数据看板中，视觉噪声是最大的敌人。我们通过三个策略解决"丑"的根因：

1. **色彩去撞**：现有系统最大的问题是满足度色（绿/蓝/红）与状态色（蓝/琥珀/灰/红）存在 2 组直接撞色，等级色更是完全复用满足度+状态的 4 个色值，导致读者根本无法区分"这个色块是说它满足度高，还是说它状态是开发中"。本方案将三套语义色彻底分离到不同色相区间，用"色相隔离"替代"明度微调"。

2. **同明度和谐**：满足度三色（绿/蓝/红）校准到 OKLCH 色彩空间中相同明度（L约0.62）和相同饱和度（C约0.12），使三色在视觉权重上完全平等——不存在"红色比绿色更跳"的错觉，扫读时不会因为某个色块更刺眼而误判其重要性。

3. **弱编码不抢戏**：等级（高/中/低/非必须）是辅助维度，不应与满足度争抢视觉注意力。本方案用 border-width 递减 + opacity 递减实现弱编码，完全不引入新色系——等级越低，边框越细、整体越淡，高等级自然"浮"在前面。

---

## B. 完整 CSS 变量定义

> 以下代码可直接复制进 CSS `:root`。

```css
:root {
  /* ===== 1. 满足度语义色（3 色，OKLCH 同明度 L约0.62 / 同饱和度 C约0.12）===== */

  /* 完全满足 - 柔和翠绿 */
  --tm-meet-full: #2DA878;
  --tm-meet-full-bg: #E7F4EE;
  --tm-meet-full-border: #2DA878;
  --tm-meet-full-dot: #2DA878;

  /* 基本满足 - 柔和天蓝 */
  --tm-meet-basic: #4488D0;
  --tm-meet-basic-bg: #E9F0FA;
  --tm-meet-basic-border: #4488D0;
  --tm-meet-basic-dot: #4488D0;

  /* 完全不满足 - 柔和珊瑚红 */
  --tm-meet-none: #D0615C;
  --tm-meet-none-bg: #FBEAE9;
  --tm-meet-none-border: #D0615C;
  --tm-meet-none-dot: #D0615C;

  /* 空状态（无满足度数据） */
  --tm-meet-empty-bg: #F1F2F6;
  --tm-meet-empty-border: #C5CAD7;

  /* ===== 2. 状态语义色（4 色，与满足度色相隔离，仅作小圆点使用）===== */

  /* 开发中 - 青色 teal，远离满足度蓝 */
  --tm-status-dev: #0D9488;
  --tm-status-dev-bg: #E0F5F3;

  /* 已排期 - 琥珀色 amber */
  --tm-status-sched: #D97706;
  --tm-status-sched-bg: #FCF0E0;

  /* 待排期 - 中性灰蓝 slate */
  --tm-status-wait: #94A3B8;
  --tm-status-wait-bg: #F0F2F6;

  /* 暂不响应 - 玫瑰红 rose，远离满足度红 */
  --tm-status-nores: #BE185D;
  --tm-status-nores-bg: #FCE8F1;

  /* ===== 3. 等级弱编码（border-width + opacity，不引入独立色系）===== */

  --tm-lv-high-border-width: 4px;
  --tm-lv-high-opacity: 1;

  --tm-lv-mid-border-width: 3px;
  --tm-lv-mid-opacity: 1;

  --tm-lv-low-border-width: 2px;
  --tm-lv-low-opacity: 0.88;

  --tm-lv-na-border-width: 1px;
  --tm-lv-na-opacity: 0.70;

  /* ===== 4. 间距节奏 token（4px / 8px 基线）===== */

  --tm-sp-1: 4px;
  --tm-sp-2: 8px;
  --tm-sp-3: 12px;
  --tm-sp-4: 16px;
  --tm-sp-5: 20px;
  --tm-sp-6: 24px;
  --tm-sp-8: 32px;

  /* 语义化间距别名 */
  --tm-gap-scene: 24px;
  --tm-gap-link: 14px;
  --tm-gap-block: 8px;
  --tm-pad-block-x: 10px;
  --tm-pad-block-y: 8px;
  --tm-pad-table-cell-x: 12px;
  --tm-pad-table-cell-y: 9px;
  --tm-row-height-table: 40px;

  /* ===== 5. 字体层级 token ===== */

  --tm-font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", "Helvetica Neue", sans-serif;
  --tm-font-mono: "SF Mono", "Cascadia Code", "Roboto Mono", "Menlo",
    "Consolas", monospace;

  --tm-fs-page-title: 22px;
  --tm-fw-page-title: 600;
  --tm-lh-page-title: 1.3;

  --tm-fs-group-date: 18px;
  --tm-fw-group-date: 600;

  --tm-fs-scene: 16px;
  --tm-fw-scene: 600;
  --tm-lh-scene: 1.4;

  --tm-fs-link: 13px;
  --tm-fw-link: 600;
  --tm-lh-link: 1.4;

  --tm-fs-block: 12.5px;
  --tm-fw-block: 500;
  --tm-lh-block: 1.4;

  --tm-fs-tip: 12.5px;
  --tm-lh-tip: 1.6;
  --tm-fs-tip-title: 13.5px;
  --tm-fw-tip-title: 600;

  --tm-fs-kpi: 20px;
  --tm-fw-kpi: 700;
  --tm-lh-kpi: 1.1;

  --tm-fs-table: 12.5px;
  --tm-fs-table-head: 12.5px;
  --tm-fw-table-head: 600;

  --tm-fs-meta: 12px;
  --tm-fs-caption: 11px;
  --tm-fw-meta: 500;

  /* ===== 6. 主色基线 + 交互态 ===== */

  --tm-primary: #5B6CFF;
  --tm-primary-hover: #4858E8;
  --tm-primary-active: #3D48D4;
  --tm-primary-soft: #EEF0FF;
  --tm-primary-tint: #F5F6FF;

  /* ===== 7. 背景与表面色 ===== */

  --tm-bg: #FFFFFF;
  --tm-bg-subtle: #FAFBFD;
  --tm-bg-muted: #F7F8FC;
  --tm-bg-inset: #F3F4F8;

  --tm-text: #1F2330;
  --tm-text-2: #5A6172;
  --tm-text-3: #9098AC;

  --tm-border: #E6E8EF;
  --tm-border-light: #EEF0F4;
  --tm-border-strong: #D1D5DE;

  /* ===== 8. 圆角 token ===== */

  --tm-radius-xs: 2px;
  --tm-radius-sm: 4px;
  --tm-radius-md: 6px;
  --tm-radius-lg: 8px;
  --tm-radius-xl: 10px;
  --tm-radius-2xl: 12px;
  --tm-radius-pill: 9999px;

  /* ===== 9. 阴影 token（柔和、有层次，基于文本色低透明度）===== */

  --tm-shadow-xs: 0 1px 2px rgba(31, 35, 48, 0.04);
  --tm-shadow-sm: 0 2px 8px rgba(31, 35, 48, 0.05);
  --tm-shadow-md: 0 4px 14px rgba(31, 35, 48, 0.08);
  --tm-shadow-lg: 0 8px 24px rgba(31, 35, 48, 0.12);
  --tm-shadow-xl: 0 16px 40px rgba(31, 35, 48, 0.16);

  --tm-shadow-card: 0 2px 8px rgba(31, 35, 48, 0.04);
  --tm-shadow-block-hover: 0 4px 14px rgba(31, 35, 48, 0.10);
  --tm-shadow-tip: 0 8px 28px rgba(31, 35, 48, 0.14);
  --tm-shadow-modal: 0 20px 50px rgba(31, 35, 48, 0.20);
  --tm-shadow-dropdown: 0 8px 20px rgba(31, 35, 48, 0.12);

  /* ===== 10. 过渡动画 token ===== */

  --tm-transition-fast: 0.12s ease;
  --tm-transition-base: 0.18s ease;
  --tm-transition-slow: 0.24s ease;
  --tm-transition-spring: 0.18s cubic-bezier(0.34, 1.2, 0.64, 1);
}
```

---

## C. 关键设计决策说明

### C1. 满足度三色：从"硬"调到"和谐"

三色在 OKLCH 色彩空间中校准到**相同明度 L约0.62、相同饱和度 C约0.12**，仅靠色相（Hue）区分。这样三色视觉权重完全平等，扫读时不会因某个色更刺眼而误判。

| 语义 | 旧色值 | 旧色问题 | 新色值 | 新色 OKLCH | 变化说明 |
|------|--------|---------|--------|-----------|---------|
| 完全满足 | #1F9D5C | 饱和度过高(L约0.57,C约0.15)，绿色过于跳眼 | #2DA878 | L0.62 C0.12 H150 | 降饱和、提明度，更柔和的翠绿 |
| 基本满足 | #3D8EE0 | 偏暗偏硬(L约0.58)，且与状态色"开发中"完全撞色 | #4488D0 | L0.62 C0.12 H245 | 提明度、降饱和，更通透的天蓝 |
| 完全不满足 | #D64545 | 纯正正红(L约0.55,C约0.17)，攻击性过强 | #D0615C | L0.62 C0.12 H25 | 降饱和、提明度，更温暖的珊瑚红 |

浅底色（*-bg）均为主色在 L约0.96 层级的极浅 tint，保证白底上可读但不喧宾夺主，色块大面积铺底时不会造成视觉疲劳。

### C2. 状态色与满足度色区分：彻底消除红蓝撞色

**问题根因**：旧版满足度有蓝(#3D8EE0)和红(#D64545)，状态也有蓝(开发中 #3D8EE0)和红(暂不响应 #D64545)——**完全相同的色值**，读者无法区分一个色块上的颜色到底代表满足度还是状态。

**解决方案**：采用**色相隔离策略**，将状态色推到完全不同的色相区间，而非在同色相内微调明度：

| 状态 | 旧色值 | 撞色对象 | 新色值 | 新色相 | 区分逻辑 |
|------|--------|---------|--------|--------|---------|
| 开发中 | #3D8EE0 | 撞满足度蓝 | #0D9488 | 青色 Teal (H175) | 从蓝色相(215)跳到青色相(175)，色相差40，一眼可辨 |
| 已排期 | #C9862A | 无撞色 | #D97706 | 琥珀 Amber (H35) | 微调为更标准的琥珀色，保持暖色系 |
| 待排期 | #B3B9C8 | 无撞色 | #94A3B8 | 石板灰 Slate (H215) | 微调为更冷的中性灰，降低饱和度 |
| 暂不响应 | #D64545 | 撞满足度红 | #BE185D | 玫瑰红 Rose (H340) | 从红色相(5)跳到玫瑰红(340)，带粉调，与珊瑚红明确区分 |

**使用场景隔离**（双重保险）：
- 满足度色 -> 用作**色块底色大面积铺色** + **左边框** + **表格色点**
- 状态色 -> **仅用作色块右上角 7px 小圆点**，不作底色、不作大面积铺色

读者即使色盲，也能通过"面积大小"区分：大色块 = 满足度，小圆点 = 状态。

### C3. 等级弱编码：border-width + opacity 递减

**问题根因**：旧版等级色（高=红、中=琥珀、低=绿、非必须=灰）**完全复用**满足度色和状态色，造成 4 组撞色。等级是辅助维度，不应与核心维度争抢注意力。

**解决方案**：移除等级独立色系，改用纯结构性弱编码：

| 等级 | 左边框宽度 | 整体不透明度 | 视觉效果 |
|------|-----------|------------|---------|
| 高 | 4px | 1.0 | 最粗边框，完全实心，自然"浮"在最前 |
| 中 | 3px | 1.0 | 标准边框，正常显示 |
| 低 | 2px | 0.88 | 细边框，略微淡化 |
| 非必须 | 1px | 0.70 | 极细边框，明显淡化，视觉退后 |

在**表格视图**中，等级不做色点，改用文字 + font-weight + opacity 区分：
- 高：font-weight 600，opacity 1，color --tm-text
- 中：font-weight 500，opacity 1，color --tm-text
- 低：font-weight 400，opacity 0.85，color --tm-text-2
- 非必须：font-weight 400，opacity 0.65，color --tm-text-3

### C4. 间距节奏：4/8 基线

选择 4px 作为最小粒度、8px 作为基础单位的原因：

1. **4px 是人眼可感知的最小间距差**——小于 4px 的差异在常规屏幕上几乎不可见，4px 恰好是"有感知但不拥挤"的阈值。
2. **8px 是 4px 的整数倍**，保证了所有间距值（4/8/12/16/20/24/32）都在同一节奏上，不会出现 5px/7px/13px 这种"游离值"导致的视觉不齐。
3. **与组件尺寸对齐**：色块高 54px、表格行高 40px、KPI 数字 20px——这些都是 4 的倍数或接近值，保证了组件尺寸与间距的节奏一致性。
4. **行业惯例**：Material Design、Tailwind CSS、Linear 等主流设计系统均采用 4/8 基线，开发者熟悉度高。

---

## D. 组件级视觉规范

### D1. 色块（地图视图核心单元）

| 属性 | 值 | Token |
|------|-----|-------|
| 宽度 | 168px | 固定值（保证网格对齐） |
| 最小高度 | 54px | — |
| 内边距 | 8px 10px 8px 11px | --tm-pad-block-y / --tm-pad-block-x |
| 圆角 | 8px | --tm-radius-lg |
| 左边框宽度 | 4px(高) / 3px(中) / 2px(低) / 1px(非必须) | --tm-lv-*-border-width |
| 左边框颜色 | 满足度对应色 | --tm-meet-*-border |
| 底色 | 满足度对应浅色 | --tm-meet-*-bg |
| 不透明度 | 1(高/中) / 0.88(低) / 0.70(非必须) | --tm-lv-*-opacity |
| 标题字体 | 12.5px / 500 / 1.4 | --tm-fs-block / --tm-fw-block / --tm-lh-block |
| 标题截断 | -webkit-line-clamp: 2 + overflow: hidden | 两行省略 |
| 状态点位置 | top: 7px; right: 7px | 绝对定位 |
| 状态点尺寸 | 7px x 7px 圆形 | — |
| 状态点颜色 | 状态对应色 | --tm-status-* |
| 空状态点 | 不显示（status 为空时不渲染） | — |
| hover 位移 | translateY(-1px) | — |
| hover 阴影 | --tm-shadow-block-hover | 0 4px 14px rgba(31,35,48,0.10) |
| hover z-index | 2 | 浮于相邻色块之上 |
| 过渡 | --tm-transition-fast | 0.12s ease |

### D2. 总览仪表盘 KPI 卡片

| 属性 | 值 | Token |
|------|-----|-------|
| 容器底色 | --tm-bg-subtle | #FAFBFD |
| 容器边框 | 1px solid --tm-border | #E6E8EF |
| 容器圆角 | 12px | --tm-radius-2xl |
| 容器内边距 | 16px 18px | — |
| KPI 数字 | 20px / 700 / 1.1 | --tm-fs-kpi / --tm-fw-kpi / --tm-lh-kpi |
| KPI 数字颜色 | 满足度色或 --tm-text | 数字着色区分维度 |
| KPI 百分比 | 12px / 500，--tm-text-3 | 内联在数字后 |
| KPI 标签 | 12px / 500，--tm-text-3 | — |
| 分隔线 | 1px solid --tm-border，高度撑满 | KPI 组之间 |
| 堆叠条高度 | 12px | — |
| 堆叠条圆角 | 6px，overflow: hidden | — |
| 堆叠条底色 | --tm-border-light | #EEF0F4 |
| 堆叠条分段色 | 满足度三色 | --tm-meet-full / --tm-meet-basic / --tm-meet-none |
| 图例字号 | 12px，--tm-text-2 | — |
| 图例色块 | 9px x 9px，--tm-radius-xs | — |
| 业务线小条高度 | 8px | 比主堆叠条矮，表示子级 |
| 业务线小条圆角 | 4px | — |
| 数字等宽 | font-variant-numeric: tabular-nums | Tech Utility 数据密度感 |

### D3. 表格行

| 属性 | 值 | Token |
|------|-----|-------|
| 行高 | 约40px（9px padding x 2 + 内容） | --tm-row-height-table |
| 单元格内边距 | 9px 12px | --tm-pad-table-cell-* |
| 正文字号 | 12.5px | --tm-fs-table |
| 表头背景 | #FAFBFF，sticky | — |
| 表头字色 | --tm-text-2，600 | — |
| 表头下边框 | 1px solid --tm-border | — |
| 场景行背景 | --tm-bg-muted | #F7F8FC |
| 场景行字色 | --tm-text，600 | 合并单元格 colspan |
| hover 行背景 | --tm-bg-subtle | #FAFBFD |
| 色点尺寸 | 8px 圆形 | 表格内比色块状态点略大 |
| 色点位置 | 文字左侧，gap: 6px | — |
| 展开行背景 | --tm-bg-subtle | — |
| 展开行上边框 | 1px dashed --tm-border（继承） | — |
| 展开行内边距 | 12px 16px | — |
| 展开图标 | 三角箭头旋转 90 度 | 0.15s ease |
| 展开图标字色 | --tm-text-3 | — |
| 展开标签 | --tm-text-3，600 | "现状：" "后续计划：" |
| 展开正文 | --tm-text-2 | — |
| 表格容器 | 1px solid --tm-border，--tm-radius-xl，overflow: hidden | — |
| 滚动区最大高度 | 72vh | — |

### D4. hover 气泡

| 属性 | 值 | Token |
|------|-----|-------|
| 定位 | position: fixed，跟随色块位置计算 | — |
| 与色块间距 | 8px（下方优先，空间不足翻到上方） | — |
| 最大宽度 | 340px | — |
| 内边距 | 12px 14px | — |
| 背景 | #FFFFFF | --tm-bg |
| 边框 | 1px solid --tm-border | — |
| 圆角 | 10px | --tm-radius-xl |
| 阴影 | --tm-shadow-tip | 0 8px 28px rgba(31,35,48,0.14) |
| 正文字号 | 12.5px / 1.6 | --tm-fs-tip / --tm-lh-tip |
| 标题字号 | 13.5px / 600 | --tm-fs-tip-title / --tm-fw-tip-title |
| 标题下边距 | 6px | — |
| 行标签 | --tm-text-3，500，margin-right: 5px | "环节："等 |
| 行正文 | --tm-text-2 | — |
| 分区分隔 | 1px dashed --tm-border，上 padding 8px | 现状/后续计划区 |
| 信息排列顺序 | 标题 > 环节+功能 > 等级+满足度+状态 > 业务线+计划时间 > (分隔)现状 > 后续计划 | — |
| 智能定位 | 右边界检测：left + 350 > innerWidth 时左移；下边界检测：翻到色块上方 | — |
| pointer-events | none | 不阻挡色块交互 |
| z-index | 1000 | 最高层 |

### D5. 场景目录 TOC

| 属性 | 值 | Token |
|------|-----|-------|
| 宽度 | 180px | 固定，flex-shrink: 0 |
| 定位 | position: sticky; top: 160px | 跟随滚动 |
| 背景 | #FFFFFF | --tm-bg |
| 边框 | 1px solid --tm-border | — |
| 圆角 | 10px | --tm-radius-xl |
| 内边距 | 16px | — |
| 标题字号 | 13px / 600 | "场景目录" |
| 标题下边距 | 10px | — |
| 条目字号 | 12.5px | — |
| 条目字色（默认） | --tm-text-2 | — |
| 条目内边距 | 6px 0 6px 8px | — |
| 左边框（默认） | 2px solid transparent | — |
| hover | 字色 -> --tm-primary，左边框 -> --tm-primary | — |
| active | 字色 -> --tm-primary，左边框 -> --tm-primary，font-weight: 500 | — |
| 响应式（<=900px） | 宽度 100%，横向滚动，边框改为底部 2px | — |

---

## E. Anti-Slop 检查清单

以下 8 条是本设计系统必须避免的"偷懒"做法，原型构建师在交付前应逐条自检：

- [ ] **1. 禁止用纯黑 #000000 作为文字或背景色** — 使用 --tm-text: #1F2330（带微蓝调的深灰），纯黑在白底上对比度过强，造成视觉疲劳。

- [ ] **2. 禁止用黑色阴影 rgba(0,0,0,\*)** — 所有阴影必须基于文本色 rgba(31,35,48,\*)，黑色阴影偏脏偏重，与靛蓝主色调不协调。

- [ ] **3. 禁止满足度色与状态色使用相同或相近色值** — 满足度（绿/蓝/红）与状态（青/琥珀/灰/玫瑰）必须在色相上相隔 >=30 度，绝不共用同一 HEX。旧版的 #3D8EE0 同时用于"基本满足"和"开发中"、#D64545 同时用于"完全不满足"和"暂不响应"是明确禁止的。

- [ ] **4. 禁止等级编码引入独立色系** — 等级（高/中/低/非必须）只通过 border-width 递减 + opacity 递减编码，禁止用红/橙/绿/灰色点表示等级。旧版 tm-dot-lv-high 等色点类必须移除。

- [ ] **5. 禁止色块底色饱和度过高** — 色块底色（*-bg）必须是主色的极浅 tint（L>=0.94），禁止直接用满足度主色作为大面积底色。浅底 + 左边框 + 小圆点的三段式编码才是正确做法。

- [ ] **6. 禁止间距使用非 4px 倍数的值** — 所有 margin/padding/gap 必须是 4/8/12/16/20/24/32 之一，禁止 5px/7px/13px/15px 等游离值。唯一的例外是 14px（环节间距，历史兼容）。

- [ ] **7. 禁止在默认视图整段铺现状/后续计划文字** — 现状和后续计划只能在 hover 气泡或表格行展开时出现，默认视图用颜色和图标替代文字堆叠。违反此条等于回到"丑"的根因之一。

- [ ] **8. 禁止相邻同明度色无分隔** — 两个相邻元素如果底色明度差 < 5%（如 #FAFBFD 和 #F7F8FC），必须用 1px solid --tm-border 分隔，禁止纯靠底色差异区分区域——在低色域屏幕上会糊在一起。

---

## 附：色值速查表

### 满足度色板
| 语义 | 主色 | 浅底 | 用途 |
|------|------|------|------|
| 完全满足 | #2DA878 | #E7F4EE | 色块底色 + 左边框 + 表格色点 |
| 基本满足 | #4488D0 | #E9F0FA | 色块底色 + 左边框 + 表格色点 |
| 完全不满足 | #D0615C | #FBEAE9 | 色块底色 + 左边框 + 表格色点 |
| 空状态 | — | #F1F2F6 | 无数据色块底色 |

### 状态色板
| 语义 | 主色 | 浅底 | 用途 |
|------|------|------|------|
| 开发中 | #0D9488 | #E0F5F3 | 仅色块右上角小圆点 |
| 已排期 | #D97706 | #FCF0E0 | 仅色块右上角小圆点 |
| 待排期 | #94A3B8 | #F0F2F6 | 仅色块右上角小圆点 |
| 暂不响应 | #BE185D | #FCE8F1 | 仅色块右上角小圆点 |

### 等级编码
| 等级 | 边框宽度 | 不透明度 | 表格字重 | 表格字色 |
|------|---------|---------|---------|---------|
| 高 | 4px | 1.0 | 600 | --tm-text |
| 中 | 3px | 1.0 | 500 | --tm-text |
| 低 | 2px | 0.88 | 400 | --tm-text-2 |
| 非必须 | 1px | 0.70 | 400 | --tm-text-3 |

### 新旧撞色消除对照
| 维度 | 旧版撞色 | 新版方案 |
|------|---------|---------|
| 满足度蓝 = 状态开发中 | #3D8EE0 = #3D8EE0 | #4488D0 vs #0D9488（蓝 vs 青） |
| 满足度红 = 状态暂不响应 | #D64545 = #D64545 | #D0615C vs #BE185D（珊瑚 vs 玫瑰） |
| 等级高 = 满足度红 | #D64545 = #D64545 | 移除等级色，改用 border-width 4px |
| 等级中 = 状态已排期 | #C9862A = #C9862A | 移除等级色，改用 border-width 3px |
| 等级低 = 满足度绿 | #1F9D5C = #1F9D5C | 移除等级色，改用 border-width 2px |
| 等级非必须 = 状态待排期 | #B3B9C8 = #B3B9C8 | 移除等级色，改用 border-width 1px |
