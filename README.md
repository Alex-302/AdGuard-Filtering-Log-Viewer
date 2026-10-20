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
