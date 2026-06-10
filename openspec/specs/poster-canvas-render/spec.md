# Poster Canvas Render

## Purpose

Compose the share poster entirely on the client using Canvas 2D, including QR code and export to a local image file.

## Requirements

### Requirement: Render poster on client Canvas

The share page SHALL compose the share poster entirely on the client using Canvas 2D.

#### Scenario: Draw poster from report data

- **WHEN** the share page loads with valid `report` and `session` in store
- **THEN** the client SHALL render a poster canvas at 750×1334 pixels
- **AND** the poster SHALL include brand, outcome badge, accuracy score, topic, duration stats, up to 3 concept/weak tags, `shareTagline`, and footer copy aligned with prototype screen 11

#### Scenario: Embed URL QR code on canvas

- **WHEN** the poster canvas is rendered
- **THEN** the client SHALL generate a scannable QR code using a frontend QR library (not a CSS placeholder)
- **AND** the QR payload SHALL encode `{POSTER_SHARE_LANDING_URL}?from=poster&session_id={sessionId}`
- **AND** the QR bitmap SHALL be drawn into the poster footer area

#### Scenario: Export poster to local file

- **WHEN** canvas drawing completes successfully
- **THEN** the client SHALL call `Taro.canvasToTempFilePath` to obtain a local PNG temp path
- **AND** SHALL display the exported image in the share page preview

#### Scenario: Canvas draw failure

- **WHEN** canvas rendering or export fails
- **THEN** the page SHALL show an error state with a retry action
- **AND** save/share actions SHALL remain disabled until export succeeds
