# Log samples and format notes

## Purpose

This document records the log formats seen in the user's files.
It explains the humanized event names and the old `Other` content
type fallback.
It also records a first scan of the Windows log format.

The raw logs stay outside the repository.
The sanitized samples are in `Docs/samples/`.

## Inventory

| File | Size | Records | Format |
| --- | --- | --- | --- |
| `recent_activity.json` | 1.2 MB | 1 165 | Android old |
| `recent_activity1.json` | 14.4 MB | 10 000 | Android new |
| `recent_activity2.json` | 0.9 MB | 624 | Android old |
| `recent_activity3.json` | 0.1 MB | 165 | Android new, connections |
| Windows log | 17.7 MB | 10 000 | `LogRecords` |

The Windows file is
`windows_20261024_adguard_filtering_log_records.json`.

## Android old format

The top level is an array.
The viewer already handles these events:

- `processedProxyRequest`
- `dnsRequest`
- `whitelistedByNetworkRuleRequest`
- `bypassedRequest`
- `blockedByFirewallRequest`
- `blockedGQuicRequest`

The payload has `mainRequestStatus` and `requestStatuses`.
It has `resourceTypes` for proxy requests.
It has `packageName`, `domain`, `requestUrl`, `creationTime`,
`appliedRules`, `modifiedMetaReason`, and `modifiedContentReasons`.

Sample: `Docs/samples/android-old.json`.

## Android new format

The top level is still an array.
The event names changed:

- `regularProxyRequest`
- `metaModifiedProxyRequest`
- `contentModifiedProxyRequest`
- `blockedProxyRequest`
- `allowedProxyRequest`
- `failedProxyRequest`
- `regularDnsRequest`
- `blockedDnsRequest`
- `allowedDnsRequest`
- `blockedByNetworkRuleRequest`
- `bypassedRequest`
- `blockedByFirewallRequest`

The new payload has `protocol`.
It has no `mainRequestStatus`.
The status is encoded in the event name and in `requestStatuses`.
It still has `resourceTypes`, `modifiedMetaReason`,
`modifiedContentReasons`, `appliedStealthModeOptions`, and
`appliedRules`.

Sample: `Docs/samples/android-new.json`.

### Why the viewer shows the two long event names

`eventLabel()` calls `humanizeEvent()` for an unknown event name.
`metaModifiedProxyRequest` becomes `Meta Modified Proxy Request`.
`contentModifiedProxyRequest` becomes `Content Modified Proxy Request`.

These labels are not invented. They come from the new log event names.
The viewer should map the new names to the normal event labels.

### Why content types used to become `Other`

The old viewer read resource types only for
`processedProxyRequest`.
The new proxy events were not in that condition.
`eventGroup()` also returned `other` for the new proxy events.
The table then fell back to `Other`.

The viewer now reads `resourceTypes` for every proxy event.
It maps a connection to `Connection` and a tunnel to `Tunnel`.
`Other` remains only for a web request with no known resource type.

`recent_activity3.json` has no `resourceTypes` at all.
All 165 records are connections.
The table shows `Connection` for the connection records.

`recent_activity1.json` has 3 407 records with resource types.
Those types are now read.

### New Android event mapping

- `regularProxyRequest` - normal proxy request.
  Old: `processedProxyRequest` with `NONE`.
- `metaModifiedProxyRequest` - meta modified request.
  Old: `processedProxyRequest` with `META_MODIFIED`.
- `contentModifiedProxyRequest` - content modified request.
  Old: `processedProxyRequest` with `MODIFIED_CONTENT`.
- `blockedProxyRequest` - blocked request.
  Old: `processedProxyRequest` with `BLOCKED`.
- `allowedProxyRequest` - allowed request.
  Old: `processedProxyRequest` with `ALLOWED`.
- `failedProxyRequest` - failed request.
  Old: `processedProxyRequest` with `FAILED`.
- `regularDnsRequest` - normal DNS request.
  Old: `dnsRequest`.
- `blockedDnsRequest` - blocked DNS request.
  Old: `dnsRequest` with `BLOCKED`.
- `allowedDnsRequest` - allowed DNS request.
  Old: `dnsRequest` with `ALLOWED`.
- `blockedByNetworkRuleRequest` - blocked by a network rule.
  No old equivalent.
- `bypassedRequest` - bypassed request.
  Old: `bypassedRequest`.
- `blockedByFirewallRequest` - firewall block.
  Old: `blockedByFirewallRequest`.

The viewer and the Python CLI implement this mapping.
Confirm it with the product code or the log documentation before
changing the mapping again.

## Android connections-only log

`recent_activity3.json` has these events:

- `blockedProxyRequest` - 55
- `bypassedRequest` - 41
- `regularProxyRequest` - 35
- `regularDnsRequest` - 34

All 165 records have an empty `resourceTypes`.
The table shows `Connection` for the connection records.
`bypassedRequest` shows `Bypassed request`, and DNS records show `DNS`.

Sample: `Docs/samples/android-connections.json`.

## Windows format

The top level is an object:

```json
{
  "ProtocolVersion": 1,
  "LogRecords": []
}
```

The viewer cannot load this object. `parseLog()` looks for
`events`, `activity`, `records`, `data`, or `items`.

### Fields

- `Time` - ISO 8601 string with an offset.
- `Host` - domain or address.
- `Url` - full URL.
- `AppPath` - process or application name.
- `ProcessId` - process ID.
- `Type` - resource type bitmask.
- `ProtocolType` - `Tcp`, `Dns`, `Quic`, or `None`.
- `Method` - HTTP method or null.
- `StatusCode`, `StatusDescription` - HTTP status.
- `Rule`, `Source` - rule and source.
- `IsThirdParty` - first-party or third-party.
- `LogRecordType` - event class.
- `BlockType` - block reason class.
- `Fired*Rules` - content, cookie, stealth, permissions, and other
  rules.
- `RequestHeaders`, `ResponseHeaders` - header maps.
- `FiredFilterId` - filter list ID.
- `AppliedStealthModeOptions` - bitmask.
- `DnsAnswer`, `DnsUpstream`, `DnsType`, `DnsStatus`.
- `TlsVersion`, `Cipher`, `CertificateIssuer`, `HasTlsInfo`.
- `ResponseSizeBytes`, `RequestSizeBytes`.
- `ProcessRequestElapsedMs`.

### First scan

- `LogRecordType`: 5 (4 835), 0 (3 414), 3 (1 718), 2 (22), 1 (11).
- `Type`: 2 048 (7 050), 32 (1 686), 33 (450), 8 192 (435),
  2 (139), 1 (63), 608 (48), 4 (43), 34 (37), 64 (15), 256 (14),
  4 096 (13), 8 (5), 512 (1), 128 (1).
- `BlockType`: 0 (8 347), 3 (1 651), 4 (2).
- `ProtocolType`: `Tcp` 9 521, `Dns` 435, `None` 36, `Quic` 8.
- `StatusCode`: 0 (7 524), 200 (2 058), 204 (277), 400 (70),
  401 (15), 101 (14), 302 (13), 301 (12), 304 (10), 404 (6),
  403 (1).
- `AppliedStealthModeOptions`: 16 384, 0, 185, 24, 57, 16, 8, 104,
  41, 40, 7 736, 7 737, 56, 9.
- Non-empty rule groups: content 7, cookie 13, stealth 6,
  basic content 1, permissions 63.

### Candidate field mapping

| Windows field | Viewer field |
| --- | --- |
| `Time` | `timeMs` |
| `Host` | `domain` |
| `Url` | `url` |
| `AppPath` | `app` or process |
| `Method` | `method` |
| `StatusCode` | `httpCode` |
| `Rule` | `rules` |
| `Source` | `referer` |
| `IsThirdParty` | `side` (`3p` or `1p`) |
| `Type` | content type |
| `LogRecordType` | event group and status |
| `BlockType` | block reason |
| `Fired*Rules` | rules, filter sources, Tracking Protection |
| `AppliedStealthModeOptions` | stealth options |
| `Dns*` | DNS fields |
| `Tls*` | TLS fields |

Do not implement this mapping before the product code or a field
dictionary confirms the bit values.

Sample: `Docs/samples/windows.json`.

## Test implications

- Add the Android old sample as a regression fixture.
- Add the Android new sample as a regression fixture.
- Add the connections-only sample as a regression fixture.
- Add the Windows sample only after the parser adapter is designed.
- Test both Android formats with the same viewer.
- Test the new event names in the sidebar filters.
- Test content types for the new proxy events.
- Test the humanized labels are gone after mapping.

## Domain-list samples

`Docs/samples/android-new.json` has four extra records:

- Record 7 has a `$domain=` list with 20 domains.
- Record 8 has a cosmetic domain list with 20 domains.
- Record 9 is meta modified with only `PERMISSIONS_RULE`.
- Record 10 is content-only cosmetic.

The viewer compacts both domain lists:

- `/cookieconsent.$domain=qrcodemonkey.net|...|jagadzet.pl`
  becomes `...qrcodemonkey.net|wedos.com|scssoft.com...+14...|...`.
- `a.com,b.com,c.com,...,t.com##.ad-banner`
  becomes `a.com,b.com,c.com,...+14...r.com,s.com,t.com##.ad-banner`.

The full rule is available in the cell popup and in the details.
The copy button copies the full rule.

Record 9 shows `Filter = Tracking Protection`, `Rule = Stealth`,
and a gray row.
Record 10 shows `Filter = Cosmetic`, `Rule = Cosmetic`, and a yellow
row.

## Open questions

- What are the exact meanings of `LogRecordType`, `Type`, and
  `BlockType`?
- How does the Windows bitmask `AppliedStealthModeOptions` decode?
- Is `blockedByNetworkRuleRequest` always blocked, or can it be a
  whitelist?
- Should the viewer support the Windows format in the same parser or in
  a separate adapter?
