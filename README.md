# AdGuard Filtering Log Viewer

A browser and command-line tool for filter developers and advanced users
to review exported logs from AdGuard for Android.

## Description

The tool reads `recent_activity.json` exported from AdGuard for Android. It
is intended for filter developers and advanced users who need to inspect a
large or foreign log, including on a phone. The browser viewer provides
filters, search, request details, and a virtual list for large logs. The
command-line interface filters records, removes duplicates, and exports the
result.

## Getting Started

Open the hosted viewer:

https://alex-302.github.io/AdGuard-Filtering-Log-Viewer/

Drop `recent_activity.json` into the window or choose the file.

The input is the `recent_activity.json` file exported from AdGuard for
Android. Logs from other AdGuard products are not compatible.

The viewer processes the file locally. No data is sent to the network.

## Usage

### Viewer

- Use the sidebar to filter by app, status, event type, content type, and
  request side.
- Use the search field to find a domain, URL, app, or rule. Press
  `Ctrl-F` or `/` to focus it.
- Click any table header to sort. Drag the header edge to resize a
  column; double-click the edge to reset it. The keyboard arrows resize
  a focused edge. The `Type` column can be widened to show long content
  type lists.
- `Time` and `URL` are always visible. Use `Columns` or right-click the
  header to hide or show the other columns. `App` shows the raw package
  name, process name, or app path.
- Hover a cut cell to see the full value. The popup can be selected and
  copied, and it stays open while the pointer is over it. Clicking the
  popup text does not close it.
- Select a request to see its details. Details are docked on desktop,
  shown below the table on a tablet, and full-screen on a phone. The app
  badge in the details header shows the app initial. A real icon appears
  only when the source log supplies one; the Android log has no icon
  field.
- Rules with long `domain=` or `app=` lists are compacted in the middle.
  The cell shows the first three and last three values with `+N` hidden
  values. Hover shows the full rule.
- Modified requests show the `Tracking Protection` or `Cosmetic` module
  in the `Filter` column. Tracking Protection rows show the option count
  as `+N Stealth` in `Rule`. Cosmetic-only rows show `+N`.
- Empty `Source` and `Filter` cells stay blank. A missing value does not
  show a dash.
- Enable `Unique URLs only` to merge repeated requests.
- The viewer saves the selected filters and column layout for the next
  visit.

### Hide list

Use `Hide list` in the top bar to hide matching records from the log.
The list is stored in the browser. Use the `Hide matching records`
switch to turn hiding on or off. The switch in the sidebar applies
immediately. The switch in the `Hide list` window is part of the draft.

- A plain domain hides the domain and its subdomains.
- `*.example.com` and `.example.com` hide subdomains only.
- URL patterns use JavaScript regular expressions without `/.../`
  delimiters. Escape `/` as `\/`.
- Use `Text` mode for literal URL strings.
- Use `Enable all` to enable all domains and valid URL patterns.
- Use `Reset` to clear domains and URL patterns and turn hiding off.
- Edits are a preview. `Save` commits them; closing the window discards
  them. `Save` is disabled when there is nothing to save.
- Import a Fiddler `.ffx` file or an `.agfilters` file. Import replaces
  the draft; it does not save until `Save`.
- Export the current draft to `.agfilters`.
- Use `Export to Fiddler` to show the copy fields for the host list and
  the combined `REGEX:(...)` string.

The `.agfilters` format is JSON. Fiddler cannot import it - it uses
more options in the `.ffx` file.

For offline use, open `filtering_log_viewer.html` from the repository and
keep `filters-meta.js` and `dns-filters-meta.js` next to it.

### Command line

The command-line tool requires Python 3 and uses only the standard
library.

```bash
py -3 adguard_log_parser.py recent_activity.json
```

The default output is a table. The examples use the Windows Python
launcher. On macOS and Linux, use `python3`.

To export JSON:

```bash
py -3 adguard_log_parser.py recent_activity.json --format json
```

The command-line tool filters with `--event`, `--status`, `--side`,
`--app`, `--domain`, `--rule`, and `--search`. It uses the same Android
event mapping as the viewer. Use `--dedup` to remove duplicates. Use
`--format` to select `table`, `json`, `jsonl`, `csv`, or `html`.

Run `py -3 adguard_log_parser.py --help` for all options.

## Documentation

- [Log format and Android event mapping](Docs/log-samples.md)
- [Implementation plan and status](Docs/change-plan.md)
- [Viewer test setup](tests/viewer/README.md)

## License

MIT. See [LICENSE](LICENSE).

Copyright (c) 2026 Alex-302
