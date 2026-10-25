# Viewer tests

Playwright checks for `filtering_log_viewer.html`.
The tests load the viewer from `file://`, use the sanitized fixtures in
`tests/fixtures/`, and do not need a local server.

## Setup

```bash
cd tests/viewer
npm install
npx playwright install chromium
```

## Run

```bash
npm test
```

The command starts headless Chromium.
It fails on an assertion, a page error, or a console error.

## Coverage

- Old and new Android event names.
- Content types for every proxy event.
- Tracking Protection and Cosmetic modules.
- App column and `appPath`.
- Column visibility, sorting, resizing, and double-click reset.
- Interactive cell popups and tooltips.
- `Ctrl-F` and `/`.
- Hide list draft, import, Save, and Reset.
- Tablet, phone, and desktop details.
- Row colors and text contrast.

The Windows fixture is stored for the future Windows adapter.
The viewer does not parse the Windows `LogRecords` format yet.
