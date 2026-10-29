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
- `+N Stealth` for Tracking Protection rows and `+N` for cosmetic-only
  rows.
- `PERMISSIONS_RULE` as a regular rule reason.
- App column and `appPath`.
- Domain-list and app-list compaction. `domain=` lists keep 3/3. All
  app lists (`$app=`, `$app=~`, `,app=`, `,app=~`) keep 1/1 and
  preserve `~`. Compacted text uses `…`. A rule with both long lists
  compacts both.
- App-list boundaries: 15 values stay unchanged, 16 values compact.
  A modifier after the app list stays.
- Column visibility, sorting, resizing, and double-click reset.
- Opening details keeps the current sort order and scroll position.
- The Type column resize cap at 1600x900 and 1000x800.
- Interactive cell popups: click persistence, font sizes, and tooltips.
- Blank Source and Filter cells for DNS, firewall, tunnel, and network
  records without a filter source. Records with an applied rule keep the
  filter name.
- Firewall strategy mapping.
- An AdGuard settings export shows a clear import error and points to
  `recent_activity.json`.
- `Ctrl-F` and `/`.
- Hide list draft, import, Save, and Reset.
- Tablet, phone, and desktop details.
- Row colors and text contrast.

## Fixtures

- `android-old.json` - old Android event names.
- `android-new.json` - new Android event names and modules.
- `android-connections.json` - connections-only log.
- `app-path.json` - `appPath` in the App column.
- `rule-app-lists.json` - `$app=` and `,app=` lists.
- `rule-app-long-lists.json` - 342-value `$app=` and `$app=~` lists,
  a 346-value `$network,app=` list, 15/16 boundaries, a `,app=~` list,
  and a list with a trailing modifier.
- `empty-source-filter.json` - missing Source and Filter values.
- `firewall-strategy.json` - firewall strategy object.
- `type-long.json` - long content-type list.
- `long-list.json` - 200 records for sort and scroll stability.
- `settings-export.json` - AdGuard settings export, not a filtering log.
- `windows.json` - stored for the future Windows adapter.

The viewer does not parse the Windows `LogRecords` format yet.
