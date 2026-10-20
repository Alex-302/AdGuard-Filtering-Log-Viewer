#!/usr/bin/env python3
"""AdGuard Filtering Log Viewer.

Parse an AdGuard for Android filtering log. The input is the
``recent_activity.json`` export. The script uses only the Python standard
library. It can filter records and remove duplicates.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter, OrderedDict
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

__version__ = "1.0.0"

PROXY_EVENT = "processedProxyRequest"
DNS_EVENT = "dnsRequest"
WHITELIST_EVENT = "whitelistedByNetworkRuleRequest"

TEMPLATE_PATH = Path(__file__).with_name("filtering_log_viewer.html")

DEFAULT_TABLE_FIELDS = [
    "id",
    "time",
    "event_label",
    "status",
    "side",
    "content",
    "app",
    "domain",
]

DEFAULT_CSV_FIELDS = [
    "id",
    "time",
    "time_ms",
    "event",
    "event_label",
    "kind",
    "app",
    "domain",
    "url",
    "method",
    "content",
    "status",
    "status_raw",
    "side",
    "rules",
    "sent",
    "received",
    "elapsed",
    "count",
]

DEFAULT_DEDUP_FIELDS = [
    "event",
    "kind",
    "app",
    "domain",
    "url",
    "method",
    "content",
    "status",
    "side",
    "rules",
]

FIELD_ALIASES = {
    "id": "id",
    "time": "time",
    "timems": "time_ms",
    "timestamp": "time_ms",
    "event": "event",
    "eventtype": "event",
    "eventlabel": "event_label",
    "kind": "kind",
    "type": "kind",
    "app": "app",
    "package": "app",
    "packagename": "app",
    "domain": "domain",
    "host": "domain",
    "url": "url",
    "method": "method",
    "content": "content",
    "contenttype": "content",
    "resourcetype": "content",
    "status": "status",
    "statusraw": "status_raw",
    "side": "side",
    "thirdparty": "side",
    "rule": "rules",
    "rules": "rules",
    "sent": "sent",
    "received": "received",
    "elapsed": "elapsed",
    "elapsedms": "elapsed",
    "count": "count",
}

FIELD_LABELS = {
    "id": "ID",
    "time": "TIME",
    "time_ms": "TIME_MS",
    "event": "EVENT_RAW",
    "event_label": "EVENT",
    "kind": "KIND",
    "app": "APP",
    "domain": "DOMAIN",
    "url": "URL",
    "method": "METHOD",
    "content": "CONTENT",
    "status": "STATUS",
    "status_raw": "STATUS_RAW",
    "side": "SIDE",
    "rules": "RULE",
    "sent": "SENT",
    "received": "RECEIVED",
    "elapsed": "MS",
    "count": "COUNT",
}

CONTENT_ALIASES = {
    "xhr": "xmlhttprequest",
    "xmlhttprequest": "xmlhttprequest",
    "css": "stylesheet",
    "stylesheet": "stylesheet",
    "js": "script",
    "script": "script",
    "doc": "document",
    "document": "document",
    "subdoc": "subdocument",
    "subdocument": "subdocument",
    "img": "image",
    "image": "image",
    "media": "media",
    "font": "font",
    "ws": "websocket",
    "websocket": "websocket",
    "object": "object",
    "other": "other",
}

STATUS_ALIASES = {
    "allowed": "WHITELISTED",
    "allow": "WHITELISTED",
    "passed": "NONE",
    "ok": "NONE",
    "none": "NONE",
    "processed": "NONE",
    "block": "BLOCKED",
    "blocked": "BLOCKED",
    "modified": "MODIFIED",
    "mod": "MODIFIED",
    "modified_meta": "META_MODIFIED",
    "meta_modified": "META_MODIFIED",
    "failed": "FAILED",
    "failure": "FAILED",
    "error": "FAILED",
    "whitelist": "WHITELISTED",
    "whitelisted": "WHITELISTED",
    "exception": "WHITELISTED",
    "bypass": "BYPASSED",
    "bypassed": "BYPASSED",
    "unknown": "UNKNOWN",
}


def _norm(value: str) -> str:
    """Normalize a value for case-insensitive matching."""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item not in (None, "")]
    if isinstance(value, str):
        return [value] if value else []
    return [str(value)]


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _dedupe_strings(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = text.upper()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _split_values(values: Iterable[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                result.append(part)
    return result


def _parse_field_list(raw: str) -> list[str]:
    fields: list[str] = []
    for part in _split_values([raw]):
        key = FIELD_ALIASES.get(_norm(part))
        if key is None:
            allowed = ", ".join(sorted(set(FIELD_ALIASES.values())))
            raise ValueError(
                f"unknown field: {part}. Allowed fields: {allowed}"
            )
        if key not in fields:
            fields.append(key)
    if not fields:
        raise ValueError("field list is empty")
    return fields


def _local_time(time_ms: int) -> datetime | None:
    if time_ms <= 0:
        return None
    try:
        return datetime.fromtimestamp(time_ms / 1000).astimezone()
    except (OSError, OverflowError, ValueError):
        return None


def _timestamp(value: Any) -> int:
    timestamp = _as_int(value)
    if 0 < timestamp < 100_000_000_000:
        timestamp *= 1000
    return timestamp


def _collect_rules(value: Any) -> list[str]:
    if isinstance(value, dict):
        if isinstance(value.get("ruleText"), str):
            text = value["ruleText"].strip()
            return [text] if text else []
        result: list[str] = []
        for item in value.values():
            result.extend(_collect_rules(item))
        return result
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            result.extend(_collect_rules(item))
        return result
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    return []


def _extract_rules(payload: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("appliedRules", "rules", "appliedRule"):
        values.extend(_collect_rules(payload.get(key)))
    return _dedupe_strings(values)


def _content_types(event_type: str, payload: dict[str, Any]) -> list[str]:
    if event_type == PROXY_EVENT:
        return _dedupe_strings(_as_list(payload.get("resourceTypes")))
    if event_type == DNS_EVENT:
        return _dedupe_strings(_as_list(payload.get("requestType")))
    return []


def _side(payload: dict[str, Any]) -> str:
    for key in ("thirdPartyRequest", "thirdParty", "isThirdParty"):
        if key not in payload:
            continue
        value = payload[key]
        if isinstance(value, bool):
            return "3p" if value else "1p"
        if isinstance(value, str) and value.lower() in {"true", "false"}:
            return "3p" if value.lower() == "true" else "1p"
    return ""


def _kind(event_type: str, payload: dict[str, Any]) -> str:
    if event_type == PROXY_EVENT:
        return str(payload.get("type") or "")
    if event_type == DNS_EVENT:
        request_type = str(payload.get("requestType") or "")
        return f"DNS {request_type}".strip()
    if event_type == WHITELIST_EVENT:
        return "network"
    if event_type == "bypassedRequest":
        return "network"
    if event_type == "blockedByFirewallRequest":
        return "firewall"
    return str(payload.get("type") or "")


def _status_raw(event_type: str, payload: dict[str, Any]) -> list[str]:
    values: list[str] = []
    if event_type == PROXY_EVENT:
        values.extend(_as_list(payload.get("requestStatuses")))
        values.extend(_as_list(payload.get("mainRequestStatus")))
        values.extend(_as_list(payload.get("requestBlockedReason")))
        values.extend(_as_list(payload.get("requestFailedReason")))
        values.extend(_as_list(payload.get("modifiedMetaReason")))
        values.extend(_as_list(payload.get("modifiedContentReasons")))
        if payload.get("requestBlockedByBrowsingSecurityModule"):
            values.append("BROWSING_SECURITY")
    elif event_type == DNS_EVENT:
        values.extend(_as_list(payload.get("requestStatus")))
        values.extend(_as_list(payload.get("blockingReason")))
    elif event_type == WHITELIST_EVENT:
        values.append("WHITELISTED")
    elif event_type == "bypassedRequest":
        values.append("BYPASSED")
    elif event_type == "blockedByFirewallRequest":
        values.append("FIREWALL")
    else:
        for key in (
            "status",
            "requestStatus",
            "requestStatuses",
            "blockingReason",
            "requestBlockedReason",
            "requestFailedReason",
        ):
            values.extend(_as_list(payload.get(key)))
        if payload.get("blocked") is True:
            values.append("BLOCKED")
        if payload.get("allowed") is True:
            values.append("ALLOWED")
        if payload.get("bypassed") is True:
            values.append("BYPASSED")
        if payload.get("failed") is True:
            values.append("FAILED")
    return _dedupe_strings(values)


def _canonical_status(
    event_type: str, payload: dict[str, Any], status_raw: Sequence[str]
) -> str:
    if event_type == WHITELIST_EVENT:
        return "WHITELISTED"
    if event_type == "bypassedRequest":
        return "BYPASSED"
    if event_type == "blockedByFirewallRequest":
        return "BLOCKED"

    if payload.get("requestBlockedByBrowsingSecurityModule"):
        return "BLOCKED"

    if event_type == DNS_EVENT:
        reason = str(payload.get("blockingReason") or "").upper()
        if reason and reason != "NONE":
            return "BLOCKED"

    if event_type == PROXY_EVENT:
        if _as_list(payload.get("requestBlockedReason")):
            return "BLOCKED"
        if _as_list(payload.get("requestFailedReason")):
            return "FAILED"

    joined = " ".join(status_raw).upper()
    if "BLOCK" in joined:
        return "BLOCKED"
    if "FAIL" in joined or "ERROR" in joined:
        return "FAILED"

    stealth_options = _as_list(payload.get("appliedStealthModeOptions"))
    has_stealth = (
        "STEALTHMODE" in joined
        or "TRACKING_PROTECTION" in joined
        or bool(stealth_options)
    )
    has_cosmetic = any(
        token in joined
        for token in (
            "COSMETIC",
            "SCRIPTLET",
            "PERMISSION",
            "HTML_ELEM_REMOVED",
            "COOKIE_RULE",
        )
    )
    if has_stealth:
        return "META_MODIFIED"
    if has_cosmetic:
        return "MODIFIED"
    if "MODIFIED_META" in joined:
        return "META_MODIFIED"
    if "MODIFIED_CONTENT" in joined:
        return "MODIFIED"
    if "MODIF" in joined:
        return "MODIFIED"
    if "ALLOWED" in joined:
        return "WHITELISTED"
    if "BYPASSED" in joined:
        return "BYPASSED"
    if "WHITELISTED" in joined:
        return "WHITELISTED"

    if not status_raw:
        lower = event_type.lower()
        if "block" in lower:
            return "BLOCKED"
        if "bypass" in lower:
            return "BYPASSED"
        if "allow" in lower:
            return "WHITELISTED"
        if "fail" in lower:
            return "FAILED"
        if any(
            token in lower
            for token in (
                "modif",
                "cosmetic",
                "scriptlet",
                "permission",
                "removed",
                "cookie",
            )
        ):
            return "MODIFIED"
        return "NONE"
    return "NONE"


@dataclass
class LogRecord:
    id: Any
    time_ms: int
    event: str
    kind: str
    app: str
    domain: str
    url: str
    method: str
    content: list[str] = field(default_factory=list)
    status: str = "UNKNOWN"
    status_raw: list[str] = field(default_factory=list)
    side: str = ""
    rules: list[str] = field(default_factory=list)
    sent: int = 0
    received: int = 0
    elapsed: int = 0
    count: int = 1
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def event_label(self) -> str:
        if self.event == PROXY_EVENT:
            kind = self.kind.lower()
            if kind == "tunnelrequest":
                return "proxy:tunnel"
            if kind == "webrequest":
                return "proxy:web"
            if kind == "connection":
                return "proxy:connection"
            return "proxy"
        if self.event == DNS_EVENT:
            return "dns"
        if self.event == WHITELIST_EVENT:
            return "whitelist"
        if self.event == "bypassedRequest":
            return "bypass"
        if self.event == "blockedByFirewallRequest":
            return "firewall"
        if "quic" in self.event.lower():
            return "quic"
        return self.event

    @property
    def time_compact(self) -> str:
        value = _local_time(self.time_ms)
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""

    @property
    def time_iso(self) -> str:
        value = _local_time(self.time_ms)
        return value.isoformat(timespec="seconds") if value else ""

    def field_value(self, name: str, *, compact_time: bool = False) -> Any:
        if name == "id":
            return self.id
        if name == "time":
            return self.time_compact if compact_time else self.time_iso
        if name == "time_ms":
            return self.time_ms
        if name == "event":
            return self.event
        if name == "event_label":
            return self.event_label
        if name == "kind":
            return self.kind
        if name == "app":
            return self.app
        if name == "domain":
            return self.domain
        if name == "url":
            return self.url
        if name == "method":
            return self.method
        if name == "content":
            return self.content
        if name == "status":
            return self.status
        if name == "status_raw":
            return self.status_raw
        if name == "side":
            return self.side
        if name == "rules":
            return self.rules
        if name == "sent":
            return self.sent
        if name == "received":
            return self.received
        if name == "elapsed":
            return self.elapsed
        if name == "count":
            return self.count
        raise KeyError(name)

    def dedup_key(self, fields: Sequence[str]) -> tuple[Any, ...]:
        values: list[Any] = []
        for name in fields:
            value = self.field_value(name)
            if isinstance(value, list):
                value = tuple(value)
            values.append(value)
        return tuple(values)

    def to_dict(self, *, include_raw: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "time": self.time_iso,
            "time_ms": self.time_ms,
            "event": self.event,
            "event_label": self.event_label,
            "kind": self.kind,
            "app": self.app,
            "domain": self.domain,
            "url": self.url,
            "method": self.method,
            "content": list(self.content),
            "status": self.status,
            "status_raw": list(self.status_raw),
            "side": self.side,
            "rules": list(self.rules),
            "sent": self.sent,
            "received": self.received,
            "elapsed": self.elapsed,
            "count": self.count,
        }
        if include_raw:
            data["raw"] = self.raw
        return data


def _build_record(record_id: Any, event_type: str, payload: dict[str, Any]) -> LogRecord:
    domain = str(payload.get("domain") or "")
    if domain.endswith("."):
        domain = domain[:-1]

    status_raw = _status_raw(event_type, payload)
    return LogRecord(
        id=record_id,
        time_ms=_timestamp(payload.get("creationTime") or payload.get("startTime")),
        event=event_type,
        kind=_kind(event_type, payload),
        app=str(payload.get("packageName") or ""),
        domain=domain,
        url=str(payload.get("requestUrl") or ""),
        method=str(payload.get("httpMethod") or ""),
        content=_content_types(event_type, payload),
        status=_canonical_status(event_type, payload, status_raw),
        status_raw=status_raw,
        side=_side(payload),
        rules=_extract_rules(payload),
        sent=_as_int(payload.get("sent")),
        received=_as_int(payload.get("received")),
        elapsed=_as_int(payload.get("elapsedTime")),
        raw=payload,
    )


def _parse_item(item: Any) -> LogRecord | None:
    if not isinstance(item, dict):
        return None
    event = item.get("event")
    if not isinstance(event, dict) or not event:
        return None
    event_type, payload = next(iter(event.items()))
    if not isinstance(payload, dict):
        return None
    return _build_record(item.get("id", ""), event_type, payload)


def parse_records(data: Any) -> tuple[list[LogRecord], int]:
    """Convert decoded JSON data to records. Return records and skipped count."""
    if isinstance(data, dict):
        for key in ("events", "activity", "records", "data", "items"):
            value = data.get(key)
            if isinstance(value, list):
                data = value
                break
        else:
            raise ValueError("JSON does not contain an array of records")
    if not isinstance(data, list):
        raise ValueError("JSON must contain an array of records")

    records: list[LogRecord] = []
    skipped = 0
    for item in data:
        record = _parse_item(item)
        if record is None:
            skipped += 1
        else:
            records.append(record)
    return records, skipped


def load_records(path: str) -> tuple[list[LogRecord], int]:
    if path == "-":
        text = sys.stdin.read()
    else:
        text = Path(path).read_text(encoding="utf-8-sig")
    if not text.strip():
        raise ValueError("input file is empty")
    return parse_records(json.loads(text))


def _match_event(record: LogRecord, value: str) -> bool:
    normalized = _norm(value)
    kind = record.kind.lower()
    if normalized in {"proxy", "proxied"}:
        return record.event == PROXY_EVENT
    if normalized in {"tunnel", "tunnelrequest"}:
        return kind == "tunnelrequest"
    if normalized in {"web", "webrequest"}:
        return kind == "webrequest"
    if normalized in {"connection", "proxyconnection"}:
        return record.event == PROXY_EVENT and kind == "connection"
    if normalized in {"dns", "dnsrequest"}:
        return record.event == DNS_EVENT
    if normalized in {"bypass", "bypassed", "bypassedrequest"}:
        return record.event == "bypassedRequest"
    if normalized in {"firewall", "blockedbyfirewallrequest"}:
        return record.event == "blockedByFirewallRequest"
    if normalized == "quic":
        return "quic" in record.event.lower()
    if normalized in {
        "whitelist",
        "whitelisted",
        "whitelistedbynetworkrulerequest",
        "network",
    }:
        return record.event == WHITELIST_EVENT
    keys = {_norm(record.event), _norm(record.event_label), _norm(record.kind)}
    return normalized in keys


def _match_content(record: LogRecord, value: str) -> bool:
    normalized = _norm(value)
    if normalized in {"any", "all"} or value.strip() == "*":
        return True
    if normalized in {"none", "empty", "na"} or value.strip() == "-":
        return not record.content
    target = CONTENT_ALIASES.get(normalized, normalized)
    return any(_norm(item) == target for item in record.content)


def _match_status(record: LogRecord, value: str) -> bool:
    normalized = _norm(value)
    target = STATUS_ALIASES.get(normalized)
    if target:
        return record.status == target
    if normalized == _norm(record.status):
        return True
    return any(normalized in _norm(item) for item in record.status_raw)


def _match_side(record: LogRecord, value: str) -> bool:
    normalized = _norm(value)
    if normalized in {"any", "all"} or value.strip() == "*":
        return True
    if normalized in {"1p", "1", "firstparty", "first", "own"}:
        return record.side == "1p"
    if normalized in {"3p", "3", "thirdparty", "third", "foreign"}:
        return record.side == "3p"
    if not normalized or normalized in {"unknown", "none", "na", "empty"}:
        return record.side == ""
    return _norm(record.side) == normalized


def _contains_any(value: str, needles: Sequence[str]) -> bool:
    text = value.lower()
    return any(needle.lower() in text for needle in needles)


@dataclass
class Filters:
    events: list[str] = field(default_factory=list)
    content_types: list[str] = field(default_factory=list)
    statuses: list[str] = field(default_factory=list)
    sides: list[str] = field(default_factory=list)
    apps: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    search: str = ""

    def matches(self, record: LogRecord) -> bool:
        if self.events and not any(
            _match_event(record, value) for value in self.events
        ):
            return False
        if self.content_types and not any(
            _match_content(record, value) for value in self.content_types
        ):
            return False
        if self.statuses and not any(
            _match_status(record, value) for value in self.statuses
        ):
            return False
        if self.sides and not any(
            _match_side(record, value) for value in self.sides
        ):
            return False
        if self.apps and not _contains_any(record.app, self.apps):
            return False
        if self.domains and not _contains_any(record.domain, self.domains):
            return False
        if self.rules:
            if not any(
                _contains_any(rule, self.rules) for rule in record.rules
            ):
                return False
        if self.search:
            haystack = " ".join(
                [record.url, record.domain, record.app, record.method, *record.rules]
            ).lower()
            if self.search.lower() not in haystack:
                return False
        return True


def deduplicate(
    records: Sequence[LogRecord],
    fields: Sequence[str],
    keep: str = "first",
) -> list[LogRecord]:
    groups: "OrderedDict[tuple[Any, ...], list[LogRecord]]" = OrderedDict()
    for record in records:
        groups.setdefault(record.dedup_key(fields), []).append(record)

    result: list[LogRecord] = []
    for items in groups.values():
        chosen = items[0] if keep == "first" else items[-1]
        result.append(replace(chosen, count=len(items)))
    return result


def _format_cell(field_name: str, value: Any) -> str:
    if isinstance(value, list):
        separator = " | " if field_name == "rules" else ", "
        value = separator.join(str(item) for item in value)
    if value is None or value == "":
        return "-"
    return str(value).replace("\r", " ").replace("\n", " ")


def _truncate(text: str, width: int) -> str:
    if width <= 0 or len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def render_table(
    records: Sequence[LogRecord],
    fields: Sequence[str],
    max_width: int,
) -> str:
    if not records:
        return "(no records)"

    headers = [FIELD_LABELS.get(name, name.upper()) for name in fields]
    rows: list[list[str]] = []
    for record in records:
        rows.append(
            [
                _format_cell(name, record.field_value(name, compact_time=True))
                for name in fields
            ]
        )

    widths: list[int] = []
    for index, header in enumerate(headers):
        width = max(len(header), *(len(row[index]) for row in rows))
        if max_width and width > max_width:
            width = max_width
        widths.append(width)

    lines = [
        "  ".join(
            _truncate(header, widths[index]).ljust(widths[index])
            for index, header in enumerate(headers)
        ).rstrip()
    ]
    for row in rows:
        lines.append(
            "  ".join(
                _truncate(cell, widths[index]).ljust(widths[index])
                for index, cell in enumerate(row)
            ).rstrip()
        )
    return "\n".join(lines)


def _flatten_for_csv(field_name: str, value: Any) -> Any:
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if value is None:
        return ""
    return value


def render_csv(records: Sequence[LogRecord], fields: Sequence[str]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=list(fields), lineterminator="\n", extrasaction="ignore"
    )
    writer.writeheader()
    for record in records:
        row = {
            name: _flatten_for_csv(name, record.field_value(name))
            for name in fields
        }
        writer.writerow(row)
    return buffer.getvalue()


def _record_json(
    record: LogRecord,
    fields: Sequence[str] | None,
    include_raw: bool,
) -> dict[str, Any]:
    data = record.to_dict(include_raw=include_raw)
    if fields is not None:
        selected = {name: data.get(name) for name in fields}
        if include_raw:
            selected["raw"] = record.raw
        data = selected
    return data


def render_json(
    records: Sequence[LogRecord],
    fields: Sequence[str] | None,
    include_raw: bool,
) -> str:
    rows = [_record_json(record, fields, include_raw) for record in records]
    return json.dumps(rows, ensure_ascii=False, indent=2)


def render_jsonl(
    records: Sequence[LogRecord],
    fields: Sequence[str] | None,
    include_raw: bool,
) -> str:
    return "\n".join(
        json.dumps(
            _record_json(record, fields, include_raw),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        for record in records
    )


def render_overview(records: Sequence[LogRecord]) -> str:
    lines = [f"Total records: {len(records)}"]
    if not records:
        return "\n".join(lines)

    def add_counter(title: str, counter: Counter[str]) -> None:
        lines.append("")
        lines.append(f"{title}:")
        width = max((len(name) for name in counter), default=0)
        for name, count in sorted(
            counter.items(), key=lambda item: (-item[1], item[0].lower())
        ):
            lines.append(f"  {name:<{width}}  {count}")

    content: Counter[str] = Counter()
    for record in records:
        if record.content:
            for item in record.content:
                content[item] += 1
        else:
            content["(none)"] += 1

    add_counter("Event type", Counter(record.event_label for record in records))
    add_counter("Content type", content)
    add_counter("Status", Counter(record.status for record in records))
    add_counter("Request side", Counter(record.side or "(none)" for record in records))
    add_counter("App", Counter(record.app or "(none)" for record in records))
    return "\n".join(lines)


def render_html(
    records: Sequence[LogRecord],
    template: str,
    source: str,
) -> str:
    payload = [
        {"id": record.id, "event": {record.event: record.raw}}
        for record in records
    ]
    payload_text = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    )
    payload_text = (
        payload_text.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    source_text = json.dumps(source, ensure_ascii=False)
    source_text = (
        source_text.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

    data_marker = "const PRELOADED_DATA = null;"
    source_marker = "const PRELOADED_SOURCE = null;"
    if data_marker not in template or source_marker not in template:
        raise ValueError("the HTML template has no data placeholders")

    result = template.replace(
        data_marker, f"const PRELOADED_DATA = {payload_text};"
    )
    result = result.replace(
        source_marker, f"const PRELOADED_SOURCE = {source_text};"
    )
    return result


def write_output(text: str, path: str | None) -> None:
    if not text.endswith("\n"):
        text += "\n"
    if path in (None, "-"):
        sys.stdout.write(text)
        sys.stdout.flush()
    else:
        Path(path).write_text(text, encoding="utf-8")


def _configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass


def build_parser() -> argparse.ArgumentParser:
    examples = """Examples:
  py -3 adguard_log_parser.py --format html
  py -3 adguard_log_parser.py --list
  py -3 adguard_log_parser.py --event dns --status blocked
  py -3 adguard_log_parser.py --content-type media --format json
  py -3 adguard_log_parser.py --side 3p --dedup
  py -3 adguard_log_parser.py --dedup --dedup-by domain,status --fields id,status,domain,count
  py -3 adguard_log_parser.py recent_activity.json --event tunnel --app instagram
"""
    parser = argparse.ArgumentParser(
        prog="adguard_log_parser.py",
        description=(
            "AdGuard Filtering Log Viewer. "
            "Parses an AdGuard for Android filtering log. "
            "Filters records by event, content, status, and request side."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples,
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="recent_activity.json",
        help="input JSON (default: recent_activity.json, - for stdin)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "output file (default: stdout, "
            "for HTML — filtering_log_report.html)"
        ),
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("table", "json", "jsonl", "csv", "html"),
        default="table",
        help="output format (default: table)",
    )
    parser.add_argument(
        "--event",
        action="append",
        metavar="TYPE",
        help=(
            "event type: proxy, tunnel, web, dns, whitelist, or the original name; "
            "repeat the option or use commas"
        ),
    )
    parser.add_argument(
        "--content-type",
        action="append",
        metavar="TYPE",
        help=(
            "content type: MEDIA, IMAGE, SCRIPT, A, etc.; "
            "none — records without a type"
        ),
    )
    parser.add_argument(
        "--status",
        action="append",
        metavar="STATUS",
        help=(
            "status: processed, blocked, modified, failed, allowed, bypassed; "
            "raw statuses such as MODIFIED_META are also accepted"
        ),
    )
    parser.add_argument(
        "--side",
        action="append",
        metavar="SIDE",
        help="request side: 1p, 3p, unknown",
    )
    parser.add_argument(
        "--app",
        action="append",
        metavar="TEXT",
        help="package name substring",
    )
    parser.add_argument(
        "--domain",
        action="append",
        metavar="TEXT",
        help="domain substring",
    )
    parser.add_argument(
        "--rule",
        action="append",
        metavar="TEXT",
        help="rule text substring",
    )
    parser.add_argument(
        "--search",
        metavar="TEXT",
        help="substring in URL, domain, app, method, or rule",
    )
    parser.add_argument(
        "--dedup",
        action="store_true",
        help="remove duplicates by the default key",
    )
    parser.add_argument(
        "--dedup-by",
        metavar="FIELDS",
        help=(
            "comma-separated deduplication key fields; "
            "enables deduplication"
        ),
    )
    parser.add_argument(
        "--dedup-keep",
        choices=("first", "last"),
        default="first",
        help="keep the first or last record in each group (default: first)",
    )
    parser.add_argument(
        "--fields",
        metavar="FIELDS",
        help="comma-separated table, CSV, or JSON fields",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=48,
        metavar="N",
        help="maximum table column width; 0 — no limit",
    )
    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="output at most N records",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="show value distribution and exit",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="include the original event object in JSON",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="do not print the summary line",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configure_streams()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        fields = _parse_field_list(args.fields) if args.fields else None
        dedup_fields = (
            _parse_field_list(args.dedup_by) if args.dedup_by else None
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.max_width < 0:
        parser.error("--max-width cannot be less than 0")
    if args.limit is not None and args.limit < 0:
        parser.error("--limit cannot be less than 0")

    try:
        records, skipped = load_records(args.input)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if skipped and not args.quiet:
        print(
            f"Warning: skipped records: {skipped}",
            file=sys.stderr,
        )

    filters = Filters(
        events=_split_values(args.event),
        content_types=_split_values(args.content_type),
        statuses=_split_values(args.status),
        sides=_split_values(args.side),
        apps=_split_values(args.app),
        domains=_split_values(args.domain),
        rules=_split_values(args.rule),
        search=args.search or "",
    )
    filtered = [record for record in records if filters.matches(record)]
    do_dedup = bool(args.dedup or dedup_fields)

    if args.list:
        try:
            write_output(render_overview(filtered), args.output)
        except OSError as exc:
            print(f"Error: could not write file: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.format == "html":
        output_path = args.output or "filtering_log_report.html"
        try:
            template = TEMPLATE_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            print(
                f"Error: could not read the HTML template: {exc}",
                file=sys.stderr,
            )
            return 1
        html_records = (
            filtered[: args.limit] if args.limit is not None else filtered
        )
        try:
            output = render_html(html_records, template, args.input)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        try:
            write_output(output, output_path)
        except OSError as exc:
            print(f"Error: could not write file: {exc}", file=sys.stderr)
            return 1
        if not args.quiet:
            print(f"HTML: {output_path}", file=sys.stderr)
        return 0

    if do_dedup:
        key_fields = dedup_fields or DEFAULT_DEDUP_FIELDS
        result = deduplicate(filtered, key_fields, args.dedup_keep)
    else:
        result = filtered

    if args.limit is not None:
        result = result[: args.limit]

    if fields is None:
        if args.format == "table":
            fields = DEFAULT_TABLE_FIELDS + (["count"] if do_dedup else [])
        elif args.format == "csv":
            fields = DEFAULT_CSV_FIELDS
        else:
            fields = None

    if args.format == "table":
        output = render_table(result, fields or DEFAULT_TABLE_FIELDS, args.max_width)
    elif args.format == "csv":
        output = render_csv(result, fields or DEFAULT_CSV_FIELDS)
    elif args.format == "json":
        output = render_json(result, fields, args.raw)
    else:
        output = render_jsonl(result, fields, args.raw)

    try:
        write_output(output, args.output)
    except OSError as exc:
        print(f"Error: could not write file: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        parts = [f"Records: {len(records)}"]
        has_filters = any(
            (
                filters.events,
                filters.content_types,
                filters.statuses,
                filters.sides,
                filters.apps,
                filters.domains,
                filters.rules,
                filters.search,
            )
        )
        if has_filters:
            parts.append(f"After filter: {len(filtered)}")
        if do_dedup:
            parts.append(f"After deduplication: {len(result)}")
        print("; ".join(parts), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
