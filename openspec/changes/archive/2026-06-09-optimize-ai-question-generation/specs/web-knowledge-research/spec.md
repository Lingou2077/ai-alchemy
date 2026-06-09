## ADDED Requirements

### Requirement: LangChain Tavily tools integration

The system SHALL integrate Tavily via the **`langchain-tavily`** package using official LangChain tools `TavilySearch` and `TavilyExtract` (not ad-hoc REST or standalone `tavily-python` orchestration for the research phase).

#### Scenario: TavilySearch tool available to Research Agent

- **WHEN** web research is enabled and `TAVILY_API_KEY` is configured
- **THEN** the system instantiates `TavilySearch` with configurable defaults (`max_results` up to 8, `search_depth`, `topic`)
- **THEN** the Research Agent MAY invoke `tavily_search` with dynamic invoke-time arguments including `query`, `search_depth`, `time_range`, `include_domains`, and `exclude_domains` per LangChain docs

#### Scenario: TavilyExtract tool available to Research Agent

- **WHEN** user input contains one or more HTTP(S) URLs
- **THEN** the Research Agent MAY invoke `tavily_extract` with `urls` and dynamic `extract_depth` (`basic` or `advanced`)
- **THEN** extracted `raw_content` is normalized into `WebMaterial` records with `source=extract`

#### Scenario: Mock tools without API key

- **WHEN** `TAVILY_API_KEY` is empty or `TAVILY_MOCK=true`
- **THEN** Mock implementations of both tools return deterministic fixtures
- **THEN** the API response includes `mock_mode: true`

### Requirement: Research Agent orchestrates tool selection

The system SHALL run a bounded Research Agent that binds `TavilySearch` and `TavilyExtract` and lets the LLM decide which tool(s) to call and with what parameters.

#### Scenario: Keyword input triggers search-first strategy

- **WHEN** pre-check classifies input as `keyword` (short text without URL)
- **THEN** the Agent is instructed to prioritize `tavily_search`
- **THEN** the Agent MAY follow up with `tavily_extract` on high-value URLs if snippets are insufficient

#### Scenario: URL input triggers extract-first strategy

- **WHEN** pre-check classifies input as `url` or `mixed`
- **THEN** the Agent is instructed to call `tavily_extract` on detected URL(s)
- **THEN** the Agent MAY optionally call `tavily_search` to supplement context

#### Scenario: Agent respects tool call budget

- **WHEN** the Agent executes web research
- **THEN** total tool invocations MUST NOT exceed `RESEARCH_AGENT_MAX_TOOL_CALLS` (default 4)
- **THEN** total research time MUST NOT exceed `RESEARCH_AGENT_TIMEOUT_SECONDS` (default 45)

#### Scenario: Dynamic locale-aware search parameters

- **WHEN** user query is primarily Chinese
- **THEN** the Agent SHOULD prefer Chinese-relevant sources via `include_domains` and/or Chinese-enriched queries
- **WHEN** user query is international/English technical terms
- **THEN** the Agent SHOULD use broader global search without restrictive Chinese-only domains

#### Scenario: Dynamic depth based on knowledge complexity

- **WHEN** the topic appears simple and search snippets are self-contained
- **THEN** the Agent SHOULD use lighter search settings (`search_depth=basic`, fewer results) and avoid unnecessary extract calls
- **WHEN** the topic is complex, ambiguous, or snippets are incomplete
- **THEN** the Agent SHOULD use `search_depth=advanced`, higher `max_results`, and `extract_depth=advanced` on selected URLs

### Requirement: Degraded mode when web research yields no results

The system SHALL NOT hard-fail the learning flow when Tavily returns no usable materials.

#### Scenario: No usable materials after Agent completes

- **WHEN** normalized `materials` is empty after Agent tool calls
- **THEN** the system sets `degraded_mode=no_web_results`
- **THEN** the system wraps user original text as fallback material
- **THEN** the system produces at least one synthetic candidate based on user input
- **THEN** the response includes a non-blocking user message equivalent to「未找到足够网页资料，将主要依据您输入的内容」

#### Scenario: Partial success

- **WHEN** some tool calls fail but at least one valid material exists
- **THEN** the system sets `degraded_mode=partial` and continues with available materials

#### Scenario: Agent timeout defaults to degrade not block

- **WHEN** research exceeds agent timeout
- **THEN** the system sets `degraded_mode=agent_timeout` and falls back to user text when no materials exist
- **THEN** the user MAY still proceed to topic confirmation and quiz generation

### Requirement: Research session API

The system SHALL expose `POST /api/v1/questions/research` accepting `{ content: string }` (max 5000 chars).

#### Scenario: Successful research with candidates

- **WHEN** a valid research request completes
- **THEN** the response includes `research_session_id`, `candidates` (1–3), `input_kind`, and `degraded_mode`
- **THEN** materials are stored in `ResearchSession` with TTL 30 minutes

#### Scenario: Empty content rejected

- **WHEN** `content` is empty after trim
- **THEN** the system responds with HTTP 400

### Requirement: Research session storage

The system SHALL store research sessions in memory separately from quiz sessions.

#### Scenario: Research session expires

- **WHEN** more than 30 minutes elapse since creation
- **THEN** generate requests with that `research_session_id` receive HTTP 410
