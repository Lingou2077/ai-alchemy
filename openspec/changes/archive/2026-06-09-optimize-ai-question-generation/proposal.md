## Why

当用户学习较新或较冷门的知识（如「Harness Engineering」）时，大模型受训练数据时效与歧义影响，可能将主题理解到其他领域。用户输入也可能是**关键词**、**长文本**或**网页 URL**，需要不同的联网获取策略。

当前实现仅依赖用户粘贴文本 + 纯 LLM 三任务流水线，无法覆盖短词/新词/多义概念，也无法按 URL 抓取整页内容。

此外，零基础用户往往无法判断哪个候选主题才是自己想学的——强制单选会在确认页形成新的认知门槛。

## What Changes

- 首页「联网学习最新资料」开关（默认关）；开启后进入 **Research Agent** 阶段
- **Research Agent** 绑定 LangChain 官方工具 [`TavilySearch`](https://docs.langchain.com/oss/python/integrations/tools/tavily_search) + [`TavilyExtract`](https://docs.langchain.com/oss/python/integrations/tools/tavily_extract)，由 AI **自主决定**何时搜索、何时抽取 URL、动态调整参数
- 兼容三种输入形态：
  1. **关键词/短语** → Agent 调用 `tavily_search`
  2. **URL（单独或嵌入文本）** → Agent 调用 `tavily_extract` 获取整页
  3. **混合** → Agent 可组合调用（先 extract 再 search 补充）
- **无结果降级**：联网无有效材料时，不阻断闯关，降级为「仅用户原文 + 提示」，并标记 `degraded_mode`
- 主题确认页：2–3 候选 +「我不确定，先广泛了解一下」（入门导览）
- 确认后 grounded Task 1/2 出题（深度 / 导览双模式）
- 依赖改为 **`langchain-tavily`**（非直接 `tavily-python` SDK 编排）

## Capabilities

### New Capabilities

- `web-knowledge-research`：Research Agent、TavilySearch/TavilyExtract 工具、输入形态识别、无结果降级
- `topic-disambiguation`：主题确认页、单一方向 + 广泛了解
- `grounded-quiz-pipeline`：深度/导览双模式 grounded Task 1/2

### Modified Capabilities

（无）

## Impact

- **后端**：新增 `research_agent`（LangChain tool-calling Agent）；移除固定单次 search 编排；`langchain-tavily` 依赖
- **API**：`POST /questions/research` 响应增加 `degraded_mode`、`input_kind`（keyword | url | mixed | text）
- **前端**：降级时 topic-confirm 或 generating 页展示非阻断提示
- **成本**：Agent 最多 N 次 tool call（默认 4），参数由模型动态选择
- **不受影响**：开关关闭时的现网路径；答题/报告/用户系统

## 已确认的产品决策

| 项 | 决策 |
|----|------|
| 检索触发 | 用户开关，默认 **关** |
| 工具集成 | **langchain-tavily** 的 `TavilySearch` + `TavilyExtract`，交给 Agent 调度 |
| 输入兼容 | 关键词搜索 + URL 整页抽取 + 混合 |
| 无结果 | **降级**至用户原文，不硬失败 |
| 歧义处理 | 候选 + 「广泛了解」导览 |
| 参数策略 | Agent 动态选 search_depth、max_results、extract_depth、地域/域名偏好 |
| API Key | 有 Key 设计；Mock 工具作开发兜底 |
