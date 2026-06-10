## ADDED Requirements

### Requirement: Share page displays exported poster

The share page SHALL replace the Phase 1 placeholder DOM preview with the Canvas-exported poster image.

#### Scenario: Enter share page after quiz

- **WHEN** the user navigates to the share page from the report page with valid report and session in store
- **THEN** the page SHALL show a brief loading state while Canvas renders and exports
- **AND** upon success SHALL display the exported poster via `<Image>` within the comic layout
- **AND** the placeholder hint text "Phase 1 占位" SHALL be removed

#### Scenario: Missing report data

- **WHEN** the share page loads without report or session data
- **THEN** the page SHALL redirect to the home tab

### Requirement: Save poster to photo album

The share page SHALL allow users to save the Canvas-exported poster to the device photo album.

#### Scenario: Save with permission granted

- **WHEN** the user taps "保存相册" and `scope.writePhotosAlbum` is authorized
- **THEN** the app SHALL call `Taro.saveImageToPhotosAlbum` with the local canvas temp file path
- **AND** show a success toast on completion

#### Scenario: Save without permission

- **WHEN** the user taps "保存相册" without album write permission
- **THEN** the app SHALL prompt authorization via `Taro.authorize({ scope: 'scope.writePhotosAlbum' })` or open settings on denial
- **AND** SHALL NOT silently fail

### Requirement: Share poster via WeChat menu

The share page SHALL open the WeChat native share-image menu for the exported poster.

#### Scenario: Share poster button

- **WHEN** the user taps "分享海报" and a canvas temp file path is available
- **THEN** the app SHALL invoke `wx.showShareImageMenu` (or Taro equivalent) with the local poster path
- **AND** the user SHALL be able to send to friends, share to moments, or save from the native sheet (aligned with prototype screen 12)

#### Scenario: Share before poster ready

- **WHEN** the user taps "分享海报" while Canvas export is in progress or failed
- **THEN** the app SHALL disable the action or show a toast indicating the poster is not ready
