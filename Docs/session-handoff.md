# Session handoff

## Status

- Date: 2026-10-29.
- Branch: `master`.
- Changed files: `filtering_log_viewer.html`, `README.md`, the files in
  `Docs/`, `tests/viewer/run.js`, `tests/viewer/README.md`, and the new
  fixtures in `tests/fixtures/`.
- State: P0, the user's feedback, and the follow-up fixes are
  implemented.
- P0 is committed as `7e78c3d`. The follow-up fixes are uncommitted.
- Viewer tests, README, and Python CLI mapping are in place.
- Windows parser remains.

## App-list compaction follow-up (2026-10-29)

- All app-list forms (`$app=`, `$app=~`, `,app=`, `,app=~`) above 15
  values keep the first and last value with `…+N…`. `~` is preserved.
- `domain=` and cosmetic domain lists keep the first 3 and last 3 values.
- All rule compaction uses the ellipsis character `…`.
- The cell tooltip, details row, and Copy button keep the full rule.
- New fixture: `tests/fixtures/rule-app-long-lists.json`.
- New fixture cases: 15/16 boundary, `,app=~`, and a trailing
  modifier.
- Viewer tests: 19 passed. Python: 24 tests run, 23 passed, 1 skipped.

## What is already done

The card list is replaced with a compact virtual table.

- Row height is 32 px.
- Row background shows the status.
- The selected row has a border and a hover shade.
- Columns are resizable. Widths persist.
- Columns are sortable. The sort arrow is visible.
- Time format is `HH:MM:SS` or `HH:MM:SS DD.MM`.
- Cell tooltip is custom. It must appear only when text is cut.
- One click opens details. The second click on the same row closes them.
- `Esc` closes the top layer.
- `Up` and `Down` move the selection.
- `Ctrl-F` tries to focus the search field.
- `Enter` toggles details for the selected row.
- Details width is saved. It can grow to 75% of the window.
- The table keeps at least 240 px when details are docked.
- Details hide App, Filter, and Method columns.
- URL and Rule columns shrink when details open.
- The current code docks details above 1200 px.
- The current code uses a modal overlay below 1200 px.
- The plan changes the narrow layout to a non-modal panel.
- Filters are a column above 900 px. They are a drawer at 900 px and below.
- Source and Process columns are hidden by default.
- The `Columns` menu shows them.
- Keyboard focus, `inert`, `role=grid`, and ARIA values were added.
- No block or unblock action was added. The viewer stays a viewer.
- New Android events are mapped to the old semantics.
- Content types are read for all new proxy events.
- Tracking Protection appears in Filter and Rule.
- App and Process are one raw App column.
- All columns except Time and URL are hideable.
- The whole header cell sorts.
- The header has visible separators and a larger resize handle.
- Double-click reset works.
- Cell popups are interactive and copyable.
- `Ctrl-F` works in Chrome from a focused row.
- Hide list edits are a draft until `Save`.
- Domain lists are compacted above 15 domains. They keep the first 3
  and last 3 values.
- App lists compact above 15 values. All app-list forms (`$app=`,
  `$app=~`, `,app=`, `,app=~`) keep 1/1 with no `|` before the last
  value. `~` is preserved.
- A rule with both a long domain list and a long app list compacts both.
- Cell popups stay open on a click inside them. The tooltip font is
  14 px, and the mono font is 13 px.
- Empty `Source` and `Filter` cells are blank.
- Firewall strategy uses `FIREWALL_STRATEGY_LABELS`. The mapping is a
  placeholder.
- Tracking Protection option badges use `+N Stealth`.
- `PERMISSIONS_RULE` is not a Stealth option. A permissions-only row is
  not Tracking Protection.
- The `Type` column can grow to 480 px.
- Tablet details are non-modal. Phone details are full-screen.
- Row colors match the legend marker backgrounds.
- The details app badge shows an initial because the Android log has no
  app icon.
- Opening details keeps the current sort order and scroll position.
  Details auto-hide does not reset the sort.
- An AdGuard settings export shows a clear import error and points to
  `recent_activity.json`.

## Current files

- `filtering_log_viewer.html` - viewer UI, CSS, and JavaScript.
- `adguard_log_parser.py` - parser and CLI. Python mapping is complete.
- `filters-meta.js` and `dns-filters-meta.js` - filter names. Not changed.
- `README.md` - landing page.
- `Docs/session-handoff.md` - this file.
- `Docs/change-plan.md` - implementation plan and status.
- `Docs/user-feedback.md` - user remarks and their analysis. Local and
  gitignored. If the file is absent, the summary in this file is the
  source of truth.
- `Docs/log-samples.md` - log format analysis.
- `Docs/samples/` - sanitized Android and Windows samples.
- `tests/viewer/` - Playwright checks.
- `tests/fixtures/` - fixtures for the viewer tests.

## Verification that passed

- `py -3 -m unittest discover -s tests -v` - 24 tests run, 23 passed,
  1 skipped because `recent_activity.json` is absent.
- In `tests/viewer/`: `npm install`, then
  `npx playwright install chromium`, then `npm test`.
  - 19 viewer tests passed.
- Playwright checks in Chromium:
  - Table, sorting, column resize, details resize.
  - Click toggle, `Esc`, `Up` and `Down`, `Enter`, `Ctrl-F`.
  - Hide list, unique URLs, search.
  - Column width persistence and details width persistence.
  - Empty state, responsive overlay, filters drawer.
  - Focus restoration and breakpoint focus.
  - App-list compaction for `,app=`, `,app=~`, `$app=`, and `$app=~`,
    including 15/16 boundaries and a trailing modifier.
  - Tooltip click persistence and font sizes.
  - Blank Source and Filter cells.
  - Firewall strategy mapping.
  - `+N Stealth` and the permissions-only row.
  - Type column resize cap.
  - Sort order and scroll position stay stable when details open.
  - The settings export error message.
- An independent review subagent checked the diff and ran the tests.
- Its findings were fixed:
  - Secondary row text contrast is 5.31:1 on blocked rows.
  - The popup stays at 30% width on narrow screens.
  - Content-only rows show the `Cosmetic` module.
  - Meta rows with only `PERMISSIONS_RULE` are regular rules, not
    Tracking Protection.
  - The domain hidden count appears once.
  - `/` closes overlays like `Ctrl-F`.
  - The tablet sidebar fills both grid rows.
  - `Reset` clears the hide list and turns hiding off.
  - The resize handle has a tooltip.
  - The details show `appPath` when present.
  - Focus leaves the hidden Filters toggle at 901 px.
- New Android format: real 10 000-record log.
- Content types for new proxy events.
- Tracking Protection for meta, Cosmetic for content-only, options,
  and yellow both-reason rows.
- Domain-list compaction with full popup and copy.
- App-list compaction with full popup and copy.
- Cell popup click persistence and larger fonts.
- Blank Source and Filter cells.
- Firewall strategy mapping.
- `+N Stealth` and the permissions-only row.
- Type column resize cap at 1600x900 and 1000x800.
- Opening details keeps the sort order and scroll position on a
  200-record list.
- An AdGuard settings export shows the expected import error.
- Hide list draft, Save, discard, import, and Reset.
- Column menu, right-click, all hideable columns.
- Double-click reset and whole-cell sorting.
- Tablet non-modal details and phone full-screen details.
- Row and legend color equality.
- Chrome `Ctrl-F` from a focused row.
- No page errors or console errors were seen.

## Important limitations of the verification

- The real user logs are outside the repo. They are analyzed in
  `Docs/log-samples.md`.
- The `RealLogTests` suite is skipped because no log is in the repo.
- The Windows `LogRecords` format is not supported yet.
- `blockedByNetworkRuleRequest` is always treated as blocked.
- The parser exposes `category` and `event_group`.
  Viewer `Filter`/`Rule` module labels are not separate fields.
- DNS request type stays in `content`; there is no `dns_type` field.
- The CLI `event_label` now uses viewer labels.
  Legacy `--event` aliases such as `proxy:web` still work.
- Mobile cards, dark theme, and details tabs are not implemented.
- Chromium and Chrome were tested. Firefox and WebKit were not.
- The Android log has only `packageName` and no app icon. The details
  badge shows the app initial. A real icon is a future path and works
  only when a source log supplies one.
- `FIREWALL_STRATEGY_LABELS` is a placeholder. The human-readable label
  equals the raw key until the mapping is filled.
- `PERMISSIONS_RULE` is not shown in the details Options list. It stays
  in the raw JSON.
- A rule with both a long domain list and a long app list compacts both
  in one pass. The formatter returns one combined hidden count.
- All rule compaction uses the ellipsis character `…`.

## User feedback status

The full text is in `Docs/user-feedback.md` (local and gitignored). If
the file is absent, the summary in this file is the source of truth.
The plan is in `Docs/change-plan.md`.

All items below are implemented except the Windows parser.
The 2026-10-25 follow-up items are also implemented.

Summary:

1. Row fill does not match the legend marker background.
2. App and Process show the same thing.
   Remove the App icon column.
   Rename Process to App.
   Show raw package names, `.exe` names, and macOS app names.
   The merged App column is visible by default and hideable.
3. All columns except Time and URL must be hideable.
   A right-click on the table header should open the column list.
4. Column borders are not visible in the header.
   Users cannot see that columns can be resized.
5. Double-click reset and keyboard resize were not understood.
   The user clicked the resize handle. The cursor changed. The reset
   did nothing. The header re-render on pointerup likely blocks
   `dblclick`.
6. Sorting works only on the header word, not on the whole header cell.
7. Cell tooltip is missing for Type, Source, and Process.
8. `Ctrl-F` did not work for the user.
9. `modified meta` must show the Tracking Protection module.
   Filter column: `Tracking Protection`.
   Rule column: `Stealth`, `Cosmetic`, or both, with `+N`.
   Tooltip lists the options.
   A row with both Cosmetic and Stealth is yellow.
10. The labels `Meta Modified Proxy Request` and
    `Content Modified Proxy Request` come from the new Android event
    names. `humanizeEvent` turns `metaModifiedProxyRequest` and
    `contentModifiedProxyRequest` into these labels.
11. Content type detection regressed in the new Android format.
    The new proxy event names are now mapped and their `resourceTypes`
    are read. `recent_activity3.json` is connections-only; the table
    shows `Connection` for those records.
12. Hide list changes save immediately after import.
    The user wants a draft mode with live preview.
    The button is renamed `Save`.
    `Save` must be gray when there is nothing to save.
    Reset clears the draft and enables `Save`. It does not save.
13. Rules with domain lists must be compacted.
    `$domain=a|b|c` shows the first domain and `|…`.
    `a,b,c##selector` shows `a,…##selector`.
    A `+N` badge counts hidden domains.
    The cell counts as truncated and shows the full rule on hover.
    More than 7 domains use middle truncation.
14. Details must not be a modal overlay below 1200 px.
    The table stays clickable.
    A row click updates details.
    Use a side or bottom panel on a tablet.

Follow-up items from 2026-10-25:

15. The details app badge must show a real icon only when the source log
    supplies one. The Android log has no icon field.
16. Long app lists keep the first and last value. All app-list forms
    use 1/1.
17. A click inside a cell popup must not close it. The popup font is
    larger.
18. Missing Source and Filter values must be blank, not a dash.
19. Firewall strategy uses a readable mapping. The first mapping is a
    placeholder.
20. Tracking Protection option badges use `+N Stealth`.
    `PERMISSIONS_RULE` is not Stealth.
21. The Type column must widen enough for long content-type lists.

## Decisions that must not be lost

- The viewer must not add blocking or unblocking.
- Keep the left filters, hide list, unique URLs, search, and virtual list.
- Keep the raw log data as the source of truth.
- Do not add a label that is not present in the log.
- Ask before changing parser semantics.
- Do not commit until the user approves the plan.

## Open questions

- Confirm the observed Android event mapping with the product code or a
  field dictionary.
- Decode the Windows `LogRecordType`, `Type`, `BlockType`, and
  `AppliedStealthModeOptions` values before the Windows adapter.
- Confirm the raw App value for Windows and macOS when the parser is
  extended.

Resolved decisions:

- `Ctrl-F` works in Chrome with the capture listener.
- Domain lists use middle truncation above 15 domains.
- The first 3 and last 3 domains are kept.
- `+N` counts hidden domains.
- The phone uses full-screen details.
- The legend reference is the marker background above the search.
- Reset clears the draft and enables Save.
- The details 240 px table minimum is accepted for now.
- App lists compact above 15 values. All app-list forms (`$app=`,
  `$app=~`, `,app=`, `,app=~`) keep 1/1 with no `|` before the last
  value. `~` is preserved.
- A rule with both long lists compacts both in one pass.
- Rule compaction uses the ellipsis character `…`.
- The cell popup stays open while the pointer is over it. A click does
  not close it.
- Empty Source and Filter cells are blank.
- `+N Stealth` is used only for Tracking Protection/Stealth rows.
  Cosmetic-only rows keep `+N`.
- `PERMISSIONS_RULE` is a regular rule reason, not Stealth.
- The Type column maximum width is 480 px.
- The firewall strategy label equals the raw key until the mapping is
  filled.
- The details badge uses the app initial until a log supplies an icon.

## How to continue

1. Read `Docs/user-feedback.md` if it exists. The file is local and
   gitignored. If the file is absent, the summary in this file is the
   source of truth.
2. Read `Docs/log-samples.md`.
3. Read `Docs/change-plan.md`.
4. Run `py -3 -m unittest discover -s tests -v`.
5. Run `npm test` in `tests/viewer/`.
6. Start the Windows parser only after the bitmask dictionary is
   confirmed.
7. Keep the follow-up changes uncommitted until the user asks for a
   commit.

## Ready-to-paste prompt for a new session

> Read `Docs/session-handoff.md`, `Docs/log-samples.md`, and
> `Docs/change-plan.md`. Read `Docs/user-feedback.md` if it exists. The
> file is local and gitignored. If the file is absent, the summary in
> `Docs/session-handoff.md` is the source of truth. The P0 and the
> follow-up fixes are implemented. Review the diff and run the Python and
> viewer tests. Start the Windows parser only after the remaining format
> questions are confirmed. Do not commit without the user's request.
