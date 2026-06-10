## 1. 后端 Report 扩展（TDD）

- [x] 1.1 在 `server/schemas/report.py` 的 `ReportData` 新增 `share_tagline`（alias `shareTagline`，max 24）
- [x] 1.2 更新 `server/prompts/report.txt`：追加 shareTagline 输出要求与风格约束
- [x] 1.3 实现 tagline fallback 逻辑（空/超长 → 按 quiz_status + accuracy 规则句）
- [x] 1.4 编写/扩展 `server/tests/test_report*.py`：断言响应含非空 `shareTagline` 及 fallback

## 2. 前端类型与配置

- [x] 2.1 扩展 `frontend/src/types/session.ts`：`ReportData.shareTagline`
- [x] 2.2 更新 `frontend/src/services/api.ts` 的 `mapReportResponse` 映射 `shareTagline`
- [x] 2.3 在 `frontend/config/index.ts` 新增 `posterShareLandingUrl` 配置项

## 3. Canvas 与 QR 绘制

- [x] 3.1 安装前端 QR 库（如 `weapp-qrcode`）并验证微信小程序构建
- [x] 3.2 实现 `frontend/src/utils/posterCanvas.ts`：750×1334 绘制（背景/徽章/分数/标签/金句/QR）
- [x] 3.3 QR 编码 URL：`{posterShareLandingUrl}?from=poster&session_id={sessionId}`
- [x] 3.4 封装 `exportPosterToTempFile()`：`canvasToTempFilePath` 返回本地路径

## 4. 分享页改造

- [x] 4.1 改造 `frontend/src/pages/share/index.tsx`：Canvas 离屏绘制 + Loading/Error/Retry
- [x] 4.2 用 `<Image src={tempFilePath}>` 展示导出图，移除占位 DOM 与「Phase 1 占位」文案
- [x] 4.3 新增 `frontend/src/utils/posterShare.ts`：`ensureAlbumAuth`、`savePosterToAlbum`、`sharePosterImage`
- [x] 4.4 绑定「保存相册」「分享海报」按钮；未就绪时 disabled
- [x] 4.5 按需调整 `frontend/src/pages/share/index.scss` 适配 Image 预览布局

## 5. 联调与验收

- [x] 5.1 完整流程：答题 → 报告（含 shareTagline）→ 分享页 Canvas → 预览
- [x] 5.2 开发者工具验证保存相册（或模拟路径）
- [ ] 5.3 真机验证 `showShareImageMenu` 与相册授权
- [x] 5.4 验证 tagline fallback：Mock LLM 空 tagline 时仍有可展示金句
