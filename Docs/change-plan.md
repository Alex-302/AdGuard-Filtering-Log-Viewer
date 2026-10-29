# Viewer feedback implementation plan

- **Date**: 2026-10-24
- **Status**: P0 is committed as `7e78c3d`. The follow-up fixes are
  uncommitted. Viewer tests, README, and Python CLI mapping are in place.
- **Design input**: `Docs/user-feedback.md` (local and gitignored)
- **Branch**: `feat/hide_filter`
- **Goal**: Fix the viewer behavior reported by the user and finish the
  table interaction model.
- **Manual prerequisite**: The user provided four Android logs and one
  Windows log. Sanitized samples are in `Docs/samples/`.

> Do not execute this plan before the user approves it.
> Do not add blocking or unblocking.
> Do not commit until the user asks.

## Constraints

- The viewer stays a log viewer. No block or unblock actions.
- Keep the left filters, hide list, unique URLs, search, and virtual
  list.
- Keep the raw log values as the source of truth.
- Do not add labels that are not in the log.
- Do not change parser semantics without a fixture.
- Time and URL columns are always visible.
- The merged App column is visible by default and hideable.
- Details hide App, Filter, and Method when they open.
- Docked details keep a 240 px table minimum until the user decides
  otherwise.
- Details are docked at 1200 px and wider.
- Below 1200 px details are a non-modal side or bottom panel.
- The table stays clickable below 1200 px.
- Filters are a column above 900 px. They are a drawer at 900 px and
  below.
- All new behavior gets a regression check.
- The plan is split into slices. Each slice is reviewed before the next
  one starts.

## Post-implementation status

The P0 slices are implemented in `filtering_log_viewer.html`.

- The new Android event names map to the old semantics.
- Content types are read for the new proxy events.
- Meta rows show `Tracking Protection`; content-only rows show
  `Cosmetic`.
- App and Process are merged into one raw App column.
- All columns except Time and URL are hideable.
- The header has visible separators and a larger resize handle.
- Double-click reset works.
- The whole header cell sorts.
- Cell popups are interactive, copyable, and capped at 30% width.
- `Ctrl-F` and `/` use a shared capture/focus path and work in Chrome.
- Hide list edits are a draft until `Save`.
- The hide list `Reset` clears the draft and enables `Save`.
- Domain lists are compacted above 15 domains.
- Tablet details are non-modal. Phone details are full-screen.
- Row colors match the legend marker backgrounds.
- Viewer tests live in `tests/viewer/` and run with `npm test`.
- `README.md` covers the table controls, App column, popups,
  shortcuts, and the hide list draft.
- The Python CLI uses the same Android event mapping and content types.

Remaining work:

- The Windows log parser is future work.
- Mobile cards, dark theme, and details tabs are future work.

Tests passed:

- Python: 24 OK, 1 skipped.
- Playwright: table, sorting, resize, double-click reset, tooltips,
  domain lists, Tracking Protection, new Android format, hide draft,
  responsive details, focus, colors.
- Chrome: `Ctrl-F` focuses the search from a focused row.
- Review fixes: contrast, 30% popup, content-only module, meta
  permissions, one domain count, slash overlays, tablet sidebar,
  `Reset`, resize tooltip, `appPath`, and 901 px focus.
- Viewer tests: 17 passed in `tests/viewer/` with `npm test`.
- No page errors or console errors.

## Follow-up status (2026-10-25)

Status: implemented. P0 is committed as `7e78c3d`. The follow-up fixes
are uncommitted.
Verification: Python 24 OK and 1 skipped. Viewer tests 17 passed.

- Details app badge: documented only. The badge shows the app initial.
  A real icon is possible only when the source log supplies one. The
  Android format has no icon field.
- `$app=` and `,app=` lists use middle truncation above 15 values. A
  rule with both a long domain list and a long app list compacts both in
  one pass.
- A click inside the cell popup does not close it. The base font is
  14 px, and the mono font is 13 px.
- Missing Source and Filter values are blank. Rule, App, Method, and
  HTTP code keep their existing fallbacks.
- Firewall strategy uses `FIREWALL_STRATEGY_LABELS`.
  `blockedByAppRuleOnWifi` is a placeholder mapping.
- Tracking Protection option badges use `+N Stealth`.
  `PERMISSIONS_RULE` is a regular rule reason and is not in the details
  Options list.
- The Type column maximum width is 480 px.
- New fixtures: `rule-app-lists.json`, `firewall-strategy.json`,
  `type-long.json`, and `empty-source-filter.json`.

## Post-release fixes (2026-10-29)

- Opening details no longer resets the sort when the sort column is
  hidden by details. The list keeps its scroll position.
- An AdGuard settings export now shows a clear import error and points
  to `recent_activity.json`.
- New tests: sort/scroll stability and the settings export error.
- Viewer tests: 17 passed.

## Slice 0 - Reproduce and capture

- [x] **Task 0.1: Capture the user's real logs**
    - **Implements:** feedback 7, 9, 10, 11, 12.
    - **Input:** the four Android logs in
      `E:\Downloads\!Trash\recent_activity\`.
    - **Input:** the Windows log
      `windows_20261024_adguard_filtering_log_records.json`.
    - **Record:** `event` names, `resourceTypes`,
      `modifiedMetaReason`, `modifiedContentReasons`,
      `appliedStealthModeOptions`, `packageName`, `type`, and
      `mainRequestStatus`.
    - **Do not modify code.**
    - **Verify:** the counts and structure in `Docs/log-samples.md`.

- [x] **Task 0.2: Use the sanitized samples**
    - **Create `tests/fixtures/` from `Docs/samples/` when the parser
      tests start.**
    - **Samples:**
        - `android-old.json` - old event names.
        - `android-new.json` - new event names.
        - `android-connections.json` - no resource types.
        - `windows.json` - Windows `LogRecords` format.
    - **Verify:** each sample loads or fails with the expected error.

- [x] **Task 0.3: Confirm the new Android event mapping**
    - **Implements:** feedback 10 and 11.
    - **Map:**
        - `regularProxyRequest` -> normal web request.
        - `metaModifiedProxyRequest` -> meta modified web request.
        - `contentModifiedProxyRequest` -> content modified web
          request.
        - `blockedProxyRequest` -> blocked web request.
        - `allowedProxyRequest` -> allowed web request.
        - `failedProxyRequest` -> failed web request.
        - `regularDnsRequest`, `blockedDnsRequest`, and
          `allowedDnsRequest` -> DNS requests.
        - `blockedByNetworkRuleRequest` -> blocked network request.
    - **Verify:** the mapping is written in `Docs/log-samples.md` and
      confirmed by the product code or a field dictionary.

## Slice 1 - Correctness

- [x] **Task 1.0: Support the new Android event names**
    - **Implements:** feedback 10 and 11.
    - **Modify `filtering_log_viewer.html`**
        - `eventLabel(eventType, recordKind)` - map the new proxy and
          DNS event names. Do not humanize them.
        - `eventGroup(eventType, recordKind)` - return `web` for all
          proxy events and `dns` for all DNS events.
        - `kind(eventType, payload)` - keep the existing `type` and DNS
          type behavior.
        - `statusRaw(eventType, payload)` - read statuses from the new
          event names and `requestStatuses`.
        - `canonicalStatus(eventType, payload, raw)` - map the new
          event names to `NONE`, `BLOCKED`, `ALLOWED`, `FAILED`,
          `META_MODIFIED`, and `MODIFIED`.
        - `contentTypes(eventType, payload)` - read `resourceTypes` for
          every proxy event.
        - `filterSources` and `dnsFilterSources` - use DNS filter names
          for every DNS event.
        - `dnsType` - set it for every DNS event.
    - **Tests:**
        - `regularProxyRequest` is a web request.
        - `metaModifiedProxyRequest` is a web request with
          `META_MODIFIED`.
        - `contentModifiedProxyRequest` is a web request with
          `MODIFIED_CONTENT`.
        - `blockedProxyRequest` is blocked.
        - `allowedProxyRequest` is allowed.
        - `failedProxyRequest` is failed.
        - `regularDnsRequest`, `blockedDnsRequest`, and
          `allowedDnsRequest` are DNS.
        - `blockedByNetworkRuleRequest` is blocked.
        - No raw event name appears in the Event field.
        - Content types are read for all proxy events.
    - **Verify:** `Docs/samples/android-new.json` and the real
      `recent_activity1.json`.

- [x] **Task 1.1: Fix content type detection**
    - **Implements:** feedback 11.
    - **Modify `filtering_log_viewer.html`**
        - `contentTypes(eventType, payload)` - read `resourceTypes` for
          every new proxy event. Support the old key names as a
          fallback.
        - `buildRecord(item)` - store the normalized content list.
        - `recordTypeLabel(record)` - show the real type. Do not show
          `Other` when a known type exists.
    - **Modify `adguard_log_parser.py` only if the real log shows the
      same gap in the CLI.**
    - **Create tests in `tests/test_adguard_log_parser.py` only for the
      parser part.**
    - **Add viewer checks for:**
        - `HTML`, `Ajax`, `Image`, `Media`, `Ping`, `DNS`, and
          `Connection`.
        - A connections-only record shows `Connection`.
        - A new proxy event with `resourceTypes` shows the real type.
    - **Verify:** `Docs/samples/android-new.json`,
      `Docs/samples/android-connections.json`, and the real
      `recent_activity1.json`.

- [x] **Task 1.2: Map Tracking Protection**
    - **Implements:** feedback 9.
    - **Modify `filtering_log_viewer.html`**
        - `buildRecord` - derive `trackingProtection` from
          `modifiedMetaReason`, `modifiedContentReasons`, and
          `statusRaw`.
        - `category(record)` - return the cosmetic category when both
          Cosmetic and Stealth are present.
        - `recordFilterLabel(record)` - return `Tracking Protection`
          for meta rows and `Cosmetic` for content-only rows.
        - `recordRuleLabel(record)` - return `Stealth`, `Cosmetic`, or
          `Cosmetic / Stealth`.
        - `buildCell` - add the `+N` option count and the full popup.
        - `openDetails` - list the same options.
    - **Values:**
        - Stealth options come from `appliedStealthModeOptions`.
        - Labels: `Do Not Track`, `Remove X-Client-Data`, and the other
          known option names.
        - Both reasons: yellow row.
        - Stealth only: gray modified row.
        - Cosmetic only: yellow row.
    - **Tests:**
        - Meta Filter cell equals `Tracking Protection`.
        - Content-only Filter cell equals `Cosmetic`.
        - Rule cell equals `Stealth`, `Cosmetic`, or both.
        - `+N` equals the option count.
        - The popup lists every option.
        - The popup stays open while the pointer is over it.
        - The popup text can be selected.
        - Both reasons give the cosmetic category.
    - **Verify:** the fixture and the real log agree.

- [x] **Task 1.3: Consolidate App and Process**
    - **Implements:** feedback 2.
    - **Modify `filtering_log_viewer.html`**
        - `COLUMNS` - remove the `app` icon column.
        - Rename `process` to `app`.
        - `buildCell` - show the raw App value.
        - `recordAppLabel` - return the package name, process name, or
          macOS app name.
        - `openDetails` - keep the friendly name only in details.
        - Keep the merged App column visible by default.
        - Make it hideable.
    - **Data:**
        - Android: `record.app` package name.
        - Windows: `AppPath` from the Windows log, for example
          `chrome.exe`. The Windows parser is a later task.
        - macOS: application name if the log provides it.
    - **Tests:**
        - No duplicate App and Process columns.
        - Android shows `com.android.chrome`, not `Chrome`.
        - The details still show the friendly name.
        - Sorting uses the raw value.
    - **Verify:** `Docs/samples/android-new.json` and
      `Docs/samples/windows.json`.

- [x] **Task 1.4: Uniform cell tooltip**
    - **Implements:** feedback 7.
    - **Modify `filtering_log_viewer.html`**
        - `buildCell` - put the full value on every cell.
        - `cellHasTruncation` - measure the visible text node, not only
          a `.truncate` child.
        - `scheduleTooltip` and `showTooltip` - use one path for every
          cell.
        - Tooltip events - use `mouseenter` and `mouseleave` per cell or
          a robust delegated path.
    - **Tests:**
        - Type `Other, Ajax` cut to `Other, Aj...` shows a tooltip.
        - Source and App show a tooltip when cut.
        - URL, Rule, Filter, and App also show one.
        - A cell that fits shows no tooltip.
        - The tooltip hides on scroll, resize, click, and overlay open.
    - **Verify:** a narrow viewport check for every column.

- [x] **Task 1.5: Make Ctrl-F reliable**
    - **Implements:** feedback 8.
    - **Modify `filtering_log_viewer.html`**
        - Keydown handler - use capture, like a CodeMirror keymap.
        - Handle the key before the browser default.
        - Close the columns menu and blocking overlays before focus.
        - Add `/` as a fallback shortcut.
        - Show a shortcut hint in the search placeholder or title.
    - **Tests:**
        - `Ctrl-F` focuses the search field in Chrome.
        - The focus is on a log row before the key press.
        - The browser find does not open.
        - The same check in Firefox and Safari if available.
        - `/` works when the focus is not in an input.
    - **Verify:** manual Chrome check plus a Playwright check.

- [x] **Task 1.6: Hide list draft and Save**
    - **Implements:** feedback 12.
    - **Modify `filtering_log_viewer.html`**
        - Add saved and draft state for domains, URLs, and the enabled
          switch.
        - `saveHideList` - save only on `Save`.
        - `openHideModal` - copy saved state to draft.
        - `closeHideModal` - discard the draft and restore the saved
          state.
        - `importHideFile`, `addDomains`, `addUrlPatterns`,
          `setHideEnabled`, `setGroupEnabled`, `resetHideSelection`, and
          `clearHide` - edit the draft and update the preview.
        - The modal `Hide matching records` switch edits the draft.
        - The sidebar switch saves immediately.
        - `doneHide` - commit the draft and close.
        - `renderHideModal` - compute the dirty flag and disable `Save`
          when clean.
        - Rename the `Apply` button to `Save`.
        - Add a `Preview` or `Unsaved changes` label.
    - **Tests:**
        - Import changes the preview but not storage.
        - Close without Save restores the saved list.
        - Save saves and closes.
        - Save is disabled when clean.
        - Save is disabled after Save.
        - Reset clears the draft.
        - Reset enables Save when it is disabled.
        - Reset does not write storage.
    - **User answer:** Reset clears the fields and activates Save.
      It does not save immediately.

- [x] **Task 1.7: Compact domain lists in rules**
    - **Implements:** feedback 13.
    - **Modify `filtering_log_viewer.html`**
        - Add `formatRuleForCell(rule)` - return compact text, hidden
          domain count, and a truncated flag.
        - `buildCell` rule case - use the formatter.
        - The compact text includes the `+N` hidden-domain marker.
        - Do not add a second `+N` badge for the same domains.
        - Force the full-rule tooltip when the formatter truncates.
        - `openDetails` - keep the compact rule and the full copy button.
        - Tooltip or popup - show the full original rule.
    - **Behavior:**
        - `$domain=a|b|c` -> `rule$domain=a|...`.
        - `a,b,c##selector` -> `a,...##selector`.
        - `+N` counts the hidden domains.
        - More than 15 domains uses middle truncation.
        - Keep other modifiers after the domain list.
        - Handle `~domain` exceptions.
        - Keep the applied-rule count separate from the domain count.
        - The `+N` popup is hoverable and selectable.
    - **Tests:**
        - The two examples from the user.
        - A rule with more than 15 domains.
        - A rule with a `~domain` exception.
        - A rule with a modifier after `$domain`.
        - The tooltip shows the full rule.
        - The details show and copy the full rule.
        - The domain count is correct.
        - The applied-rule count is not confused.
    - **Verify:** a fixture with the two examples and a long list.

## Slice 2 - Table UX

- [x] **Task 2.1: Unify status colors**
    - **Implements:** feedback 1.
    - **Modify `filtering_log_viewer.html`**
        - Define one background token per status.
        - Use it in `.chip.*` and `.category-*`.
        - Keep the border token darker.
    - **Reference:** the legend is above the search. The reference color
      is the marker background without the border.
    - **Tests:**
        - The row background equals the legend marker background.
        - The border is darker.
        - Text contrast is at least 4.5:1.
    - **Verify:** computed styles in the browser.

- [x] **Task 2.2: Column visibility**
    - **Implements:** feedback 3.
    - **Modify `filtering_log_viewer.html`**
        - `COLUMNS` - add `canHide` and `defaultVisible`.
        - `DEFAULT_COLUMN_VISIBILITY` - Time and URL fixed.
        - `visibleColumns` - apply the user choice and details
          auto-hide.
        - `renderHeader` and `renderWindow` - render only visible
          columns.
        - Columns menu - list every hideable column.
        - Header context menu - open the same menu at the pointer.
        - Reset columns - restore defaults.
    - **Tests:**
        - Every column except Time and URL can be hidden.
        - Time and URL cannot be hidden.
        - Right-click opens the menu.
        - Visibility persists.
        - Details auto-hide does not overwrite the user choice.
        - Hiding the active sort column resets the sort.
    - **Verify:** a Playwright check for each column.

- [x] **Task 2.3: Visible column borders and resize affordance**
    - **Implements:** feedback 4 and 5.
    - **Modify `filtering_log_viewer.html`**
        - Header cells - add a visible right border.
        - `.col-resizer` - make the hit area at least 9 px.
        - Resizer - visible resting line, accent on hover.
        - Tooltip - `Drag to resize. Double-click to reset.`
        - Double-click - reset the column width.
        - Do not re-render the header on pointerup without movement.
          Otherwise the second click hits a new element and `dblclick`
          never fires.
        - Keyboard - `Left` and `Right` resize.
        - Focus ring - visible.
        - Details resizer - add a visible grip icon.
    - **Tests:**
        - A border is visible between header cells.
        - Double-click resets the width.
        - Keyboard resize works.
        - The handle is focusable.
        - The details grip is visible and draggable.
    - **Verify:** browser check at 1440 px and 800 px.

- [x] **Task 2.4: Sort by the whole header cell**
    - **Implements:** feedback 6.
    - **Modify `filtering_log_viewer.html`**
        - `renderHeader` - make the cell the sort target.
        - Header click - ignore `.col-resizer`.
        - CSS - pointer cursor and hover on the cell.
    - **Tests:**
        - A click in the cell padding sorts.
        - A click on the resizer does not sort.
        - The sort arrow stays.
        - Keyboard sorting stays.
        - Chrome with focus on a row: a header click sorts.
    - **Verify:** a Playwright click at the cell edge.

- [x] **Task 2.5: Make details non-modal below 1200 px**
    - **Implements:** feedback 14.
    - **Modify `filtering_log_viewer.html`**
        - Remove the details backdrop and the inert table below
          1200 px.
        - Use a side panel or a bottom panel that leaves the table
          visible.
        - Keep row clicks active.
        - Keep `Esc` and the close button.
        - Do not trap focus in details.
        - Keep the table selection when details open.
        - Confirm the phone layout separately.
    - **Tests:**
        - At 1000 px the table is clickable with details open.
        - A row click updates details.
        - No backdrop is visible.
        - The table is not inert.
        - `Esc` and the close button close details.
        - Focus can move between the table and details.
    - **Verify:** browser checks at 1000 px, 800 px, and 700 px.

## Slice 3 - Verification and cleanup

- [x] **Task 3.1: Add a viewer test harness**
    - **Create `tests/viewer/` with a small Playwright setup.**
    - **Copy the samples from `Docs/samples/` into
      `tests/fixtures/`.**
    - **Cover:**
        - Content types for old and new Android events.
        - Tracking Protection.
        - App column.
        - Column visibility.
        - Tooltips.
        - `Ctrl-F`.
        - Hide list draft.
        - Sorting and resizing.
    - **Verify:** the test command runs from a clean checkout.

- [x] **Task 3.2: Update the README**
    - **Modify `README.md`.**
    - Add the table controls, the App column, the hide list draft, and
      the shortcuts.
    - Keep the README a landing page. Put details in `Docs/`.

- [x] **Task 3.3: Final review**
    - Run the Python suite.
    - Run the viewer tests.
    - Run an independent review subagent.
    - Fix only confirmed issues.
    - Report the remaining risks.

## Future work - Windows format

The Windows log is a separate format.
Do not add it to the Android parser without a mapping review.

- Detect the top-level object with `ProtocolVersion` and `LogRecords`.
- Map `Time`, `Host`, `Url`, `AppPath`, `Method`, `StatusCode`, `Rule`,
  `Source`, `IsThirdParty`, `Dns*`, and `Tls*`.
- Decode `LogRecordType`, `Type`, `BlockType`, and
  `AppliedStealthModeOptions`.
- Use `Fired*Rules` for Tracking Protection.
- Add `Docs/samples/windows.json` as a fixture.
- Do not start until the field dictionary is confirmed.

Other future work:

- Show a real app icon in the details badge when the source log supplies
  one. The Android format has no icon field.
- Fill `FIREWALL_STRATEGY_LABELS` with human-readable labels. The
  current mapping is a placeholder.

## Open questions

1. Confirm the observed new Android event mapping with the product code
   or a field dictionary.
2. Decode the Windows `LogRecordType`, `Type`, `BlockType`, and
   `AppliedStealthModeOptions` values before the Windows adapter.

## Approval

Status: **Implemented (P0) and follow-up fixes**. The user approved the
work. Final review and documentation tasks remain.

