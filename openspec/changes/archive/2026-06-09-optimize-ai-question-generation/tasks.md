## 1. 后端基础与配置

- [x] 1.1 添加 `langchain-tavily` 依赖；`config.py` / `.env.example` 增加 `TAVILY_API_KEY`、`TAVILY_MOCK`、`RESEARCH_AGENT_MAX_TOOL_CALLS`（4）、`RESEARCH_AGENT_TIMEOUT_SECONDS`（45）、`TAVILY_SEARCH_MAX_RESULTS`（8）
- [x] 1.2 新增 `server/schemas/research.py`：`WebMaterial`、`ResearchBundle`、`TopicCandidate`、`ResearchResponse`（含 `input_kind`、`degraded_mode`）
- [x] 1.3 新增 `server/services/research/input_classifier.py`：检测 keyword / url / mixed / text
- [x] 1.4 新增 Mock Tavily 工具（与 LangChain tool schema 一致）供测试与无 Key 开发

## 2. Research Agent（TDD）

- [x] 2.1 编写 `server/tests/test_research_agent.py`：URL→extract 优先、关键词→search 优先、max_tool_calls 上限、无结果降级
- [x] 2.2 实现 `server/services/research/research_agent.py`：绑定 `TavilySearch` + `TavilyExtract`（来自 `langchain_tavily`），bounded tool loop + DeepSeek
- [x] 2.3 编写 `server/prompts/research_agent.txt`：工具选用策略、国内外域名偏好、简繁/复杂度动态参数指引
- [x] 2.4 实现 materials 归一化与 `degraded_mode` ladder（no_web_results / partial / agent_timeout）
- [x] 2.5 新增 `topic_candidate_chain`：基于 materials structured output 1–3 候选；无材料时合成 1 候选

## 3. Research API 与会话（TDD）

- [x] 3.1 编写 `server/tests/test_research_api.py`：400 空内容、Mock、degraded 响应字段、410 过期
- [x] 3.2 扩展 `session_store`：`ResearchSession`（materials、input_kind、degraded_mode、candidates）
- [x] 3.3 新增 `server/routers/research.py`：`POST /api/v1/questions/research`；注册到 `main.py`

## 4. Grounded 出题流水线（TDD）

- [x] 4.1 编写 `server/tests/test_grounded_pipeline.py`：focused、`__all__`、degraded materials、无 research 回归
- [x] 4.2 `grounding.py`：`assemble_focused_document` / `assemble_explore_all_document`（基于 materials）
- [x] 4.3 扩展 `GenerateQuestionsRequest`：`research_session_id`、`selected_topic_id`
- [x] 4.4 `question_pipeline` grounded 分支 + explore/focused Prompt 变体

## 5. 前端

- [x] 5.1 首页 Switch + placeholder 提示可粘贴链接/关键词
- [x] 5.2 `api.ts` + `types/research.ts`（含 `degraded_mode`、`input_kind`）
- [x] 5.3 `topic-confirm` 页：候选 + 广泛了解 + degraded banner
- [x] 5.4 `generating` 页参数传递与 Loading 文案

## 6. 联调与验收

- [x] 6.1 关键词「Harness Engineering」→ Agent search + 可选 extract → 候选正确（Mock/单测覆盖；真实 Key 需本地联调）
- [x] 6.2 粘贴 URL → extract 路径（Mock 单测 + input_classifier）
- [x] 6.3 无结果 degraded_mode + 仍可闯关（`test_materials` / API 测试）
- [x] 6.4 中英文 query 分类（input_classifier；Agent 参数由 Prompt 指导）
- [x] 6.5 关闭联网开关 → 现网行为不变（`test_generate_without_research_regression`）
