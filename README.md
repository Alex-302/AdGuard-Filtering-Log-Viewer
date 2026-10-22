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
- Use the search field to find a domain, URL, app, or rule.
- Select a request to see its details and applied rules.
- Enable `Unique URLs only` to merge repeated requests.
- The viewer saves the selected filters for the next visit.

### Hide list

Use `Hide list` in the top bar to hide matching records from the log.
The list is saved in the browser. Use the `Hide matching records` switch
to turn hiding on or off.

- A plain domain hides the domain and its subdomains.
- `*.example.com` and `.example.com` hide subdomains only.
- URL patterns use JavaScript regular expressions without `/.../`
  delimiters. Escape `/` as `\/`.
- Use `Text` mode for literal URL strings.
- Use `Reset selection` to enable all domains and valid URL patterns.
- Import a Fiddler `.ffx` file or an `.agfilters` file. Import replaces
  the current list.
- Export the list to `.agfilters`.
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
`--app`, `--domain`, `--rule`, and `--search`. Use `--dedup` to remove
duplicates. Use `--format` to select `table`, `json`, `jsonl`, `csv`, or
`html`.

Run `py -3 adguard_log_parser.py --help` for all options.

## License

MIT. See [LICENSE](LICENSE).

Copyright (c) 2026 Alex-302
