# Grounded Quiz Pipeline

## Purpose

Ground quiz generation on web research materials when the user confirms a topic, while preserving the legacy generate path when research fields are omitted.

## Requirements

### Requirement: Grounded content assembly for Task 1

When `research_session_id` and `selected_topic_id` are provided to `POST /api/v1/questions/generate`, Task 1 knowledge structuring SHALL use assembled grounding material instead of raw user text alone.

#### Scenario: Generate with confirmed single-topic focus

- **WHEN** generate is called with valid `research_session_id` and `selected_topic_id` matching a candidate id
- **THEN** the pipeline loads the selected candidate and associated `WebMaterial` items (from `tavily_search` and/or `tavily_extract`) from the research session
- **THEN** Task 1 receives a focused grounding document: user input + selected title/summary + material excerpts (truncated, max ~3500 chars of grounding text)
- **THEN** `grounding_mode` is `focused`

#### Scenario: Generate with explore-all introductory path

- **WHEN** generate is called with valid `research_session_id` and `selected_topic_id=__all__`
- **THEN** Task 1 receives an explore grounding document listing **all** candidates with their summaries plus merged `WebMaterial` excerpts (truncated by relevance/score, max ~3500 chars)
- **THEN** `grounding_mode` is `explore_all`

#### Scenario: Invalid or expired research reference

- **WHEN** `research_session_id` or `selected_topic_id` is missing, invalid, or expired
- **THEN** the system responds with HTTP 410 or 422 and does not invoke the LLM pipeline

#### Scenario: Legacy generate without research fields

- **WHEN** generate is called with only `content` and `questions_per_level` (no research fields)
- **THEN** behavior is identical to the current production pipeline

### Requirement: Grounding constraints in prompts

Task 1 and Task 2 prompts SHALL instruct the model to ground outputs exclusively in provided materials, with mode-specific objectives.

#### Scenario: Focused mode deepens one direction

- **WHEN** `grounding_mode` is `focused`
- **THEN** Task 1 extracts concepts, facts, and misconceptions for the selected direction only
- **THEN** Task 2 generates standard quiz questions deepening that direction

#### Scenario: Explore-all mode provides introductory overview

- **WHEN** `grounding_mode` is `explore_all`
- **THEN** Task 1 extracts per-direction introductory concepts and explicit distinctions between directions
- **THEN** Task 2 generates disambiguation questions (which direction matches a description) and at least one introductory fact question per candidate direction
- **THEN** Task 2 does NOT generate deep expert-level questions confined to a single direction

#### Scenario: Task 1 must not hallucinate beyond sources

- **WHEN** grounded Task 1 runs in either mode
- **THEN** the system prompt requires facts and concepts to be supported by the grounding document
- **THEN** if sources are insufficient, the model keeps `key_facts` minimal rather than inventing domain knowledge

### Requirement: Session stores grounding metadata

Quiz sessions created from grounded generation SHALL record provenance for debugging and future report context.

#### Scenario: Session includes research provenance

- **WHEN** a grounded quiz session is created
- **THEN** the session store saves `research_session_id`, `selected_topic_id`, `grounding_mode`, `grounding_sources` (url list), and `web_research_enabled: true`
- **THEN** the generate response MAY include `grounded: true` and `topic` from structured knowledge

### Requirement: Report generation compatibility

Task 3 report generation SHALL remain unchanged and operate on the quiz session's stored `StructuredKnowledge`.

#### Scenario: Report after focused grounded quiz

- **WHEN** the user completes a quiz with `grounding_mode=focused`
- **THEN** `POST /api/v1/report/generate` works without additional parameters
- **THEN** report content reflects the focused grounded knowledge

#### Scenario: Report after explore-all quiz suggests deeper dive

- **WHEN** the user completes a quiz with `grounding_mode=explore_all`
- **THEN** `POST /api/v1/report/generate` works without additional parameters
- **THEN** the report `suggestion` includes guidance to pick a specific direction for a deeper follow-up quiz
