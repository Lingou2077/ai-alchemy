## Why

通关/失败后，用户可在报告页点击「分享战绩/分享复盘」进入分享页，但当前 `pages/share` 仅为 Phase 1 占位：海报是静态 DOM 预览，「保存相册」「分享海报」弹出占位 Toast，二维码为假格子。需求分析 §3.4 要求「战绩海报：自动生成精美分享图（成绩+二维码），支持朋友圈分享裂变」；原方案设计 Phase 1 亦明确为 **Canvas 海报**。

经成本评估，**不采用 AI 图像生成**（额外图像 API 费用高、等待慢、需独立 Provider）。改为：**前端 Canvas 按 comic 设计令牌绘制海报 + 报告 Task 3 一并产出 LLM 分享金句**，在低成本下完成复盘→传播闭环。

## What Changes

- 扩展 **Report Task 3**：`ReportData` 新增 `shareTagline`（≤20 字炼金风分享语），与 summary/suggestion 同次 LLM 调用产出
- 分享页 **Canvas 2D 绘制**海报（750×1334）：渐变背景、战绩数据、概念标签、`shareTagline`、**前端 QR 库**生成的 URL 二维码
- 导出 `canvasToTempFilePath` → 本地 PNG，实现 **保存相册** 与 **showShareImageMenu 分享**
- 移除原方案中的后端海报合成 API、图像 API、Pillow/segno 服务端依赖
- LLM 未产出 tagline 时使用规则 fallback，不阻断分享

## Capabilities

### New Capabilities

- `poster-share-tagline`：Report 链扩展 `shareTagline` 字段、Prompt 约束与 fallback 规则
- `poster-canvas-render`：前端 Canvas 绘制、QR 码嵌入、导出与预览
- `poster-share-actions`：保存相册、微信分享菜单、相册权限处理

### Modified Capabilities

（无 — 现有 `grounded-quiz-pipeline` 等 spec 不涉及分享行为变更）

## Impact

- **后端**：仅改 `schemas/report.py`、`prompts/report.txt`、report 相关测试；**无新 router**、无图像 API 配置
- **前端**：改造 `pages/share`；新增 `utils/posterCanvas.ts`、`utils/posterShare.ts`；引入 QR 库（如 `weapp-qrcode`）；扩展 `types/session.ts` 与 `mapReportResponse`
- **配置**：前端 `config` 增加 `POSTER_SHARE_LANDING_URL`（二维码落地页，首版 URL 普通二维码）
- **成本**：每份海报 **零额外 API**（tagline 已含在报告生成的一次 LLM 调用中）
- **不受影响**：出题/答题/用户登录与成长体系主流程

## 已确认的产品决策

| 项 | 决策 |
|----|------|
| 海报视觉 | **纯前端 Canvas** 绘制，对齐原型屏 11 / `comic.scss` |
| LLM 文案 | **并入 Report Task 3**（`shareTagline` 字段） |
| 扫码分享 | **纯前端 QR 库** + URL 落地页（非微信官方小程序码） |
| 分享交互 | `showShareImageMenu` + `saveImageToPhotosAlbum`（对齐原型屏 12） |
| 失败降级 | tagline 缺失时用规则模板句；Canvas 失败可重试 |
