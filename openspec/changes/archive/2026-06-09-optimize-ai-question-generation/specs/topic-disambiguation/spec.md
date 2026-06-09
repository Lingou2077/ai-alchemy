## ADDED Requirements

### Requirement: Web research toggle on home page

The home page SHALL provide a user-controlled toggle labeled「联网学习最新资料」defaulting to **off**.

#### Scenario: Toggle off preserves legacy flow

- **WHEN** the toggle is off and the user taps「开始闯关」
- **THEN** the app navigates directly to the generating page without calling the research API

#### Scenario: Toggle on triggers research before quiz generation

- **WHEN** the toggle is on and the user taps「开始闯关」
- **THEN** the app calls `POST /api/v1/questions/research` and navigates to the topic confirmation page on success

#### Scenario: Input placeholder supports URL and keywords

- **WHEN** the user views the home input area
- **THEN** placeholder or hint text indicates that pasted links or keywords are supported when web research is enabled

### Requirement: Topic confirmation page

The system SHALL present a topic confirmation page showing 1–3 candidate topics plus an explore-all option.

#### Scenario: Display candidates for user selection

- **WHEN** research succeeds with candidates
- **THEN** the page displays each candidate's title, summary, and up to 2 source domain labels
- **THEN** the page displays「我不确定，先广泛了解一下」as a distinct bottom option

#### Scenario: User selects a single focused direction

- **WHEN** the user selects one candidate and confirms
- **THEN** the app navigates to generating with `research_session_id` and that candidate's `selected_topic_id`

#### Scenario: User selects explore-all introductory path

- **WHEN** the user selects「我不确定，先广泛了解一下」and confirms
- **THEN** the app navigates with `selected_topic_id=__all__`

#### Scenario: Degraded mode banner

- **WHEN** research response has `degraded_mode` of `no_web_results`, `partial`, or `agent_timeout`
- **THEN** the confirmation page shows a non-blocking banner explaining that web materials were insufficient and quiz will rely mainly on user input

#### Scenario: Mock mode hint

- **WHEN** `mock_mode: true`
- **THEN** the page shows a development/mock banner

### Requirement: Loading copy reflects research steps

When web research is enabled, loading UI SHALL communicate progress stages.

#### Scenario: Generating page shows grounded pipeline steps

- **WHEN** the generating page runs after topic confirmation
- **THEN** loading subtitle indicates stages such as「联网检索」→「结构化知识」→「生成题目」
