# Poster Share Tagline

## Purpose

Extend report generation with a short share tagline for poster display, without adding extra API calls.

## Requirements

### Requirement: Report includes share tagline

The system SHALL extend Report Task 3 output with a `shareTagline` field generated in the same LLM invocation as `summary` and `suggestion`.

#### Scenario: Successful report with tagline

- **WHEN** the client calls `POST /api/v1/report/generate` with valid session and answers
- **THEN** the response SHALL include `shareTagline` as a non-empty string
- **AND** `shareTagline` SHALL be at most 20 Chinese characters (or equivalent length)
- **AND** the tone SHALL reflect alchemy/gamification style appropriate to quiz outcome (success vs failed)

#### Scenario: Tagline references learning context

- **WHEN** the report is generated with known `topic`, `accuracy`, and `weakPoints`
- **THEN** `shareTagline` SHOULD incorporate the topic or at most one weak concept name when relevant

#### Scenario: Tagline fallback when LLM output invalid

- **WHEN** the LLM returns an empty, missing, or over-length `shareTagline`
- **THEN** the system SHALL substitute a rule-based fallback tagline based on `quiz_status` and `accuracy`
- **AND** the report response SHALL still succeed with a usable `shareTagline`

### Requirement: Share tagline does not add API calls

The system SHALL NOT introduce a separate endpoint or LLM call solely for poster copy.

#### Scenario: Share page uses cached report

- **WHEN** the user opens the share page after viewing the report
- **THEN** the client SHALL read `shareTagline` from the existing report in session store
- **AND** SHALL NOT request additional LLM or poster-copy APIs
