import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import adguard_log_parser as parser  # noqa: E402


def proxy_record(
    record_id,
    *,
    kind="TunnelRequest",
    url="https://example.com",
    domain="example.com",
    third_party=False,
    resource_types=None,
    statuses=None,
    main_status="NONE",
    blocked_reason=None,
    failed_reason=None,
    modified_meta=None,
    modified_content=None,
    rules=None,
    creation_time=1700000000000,
):
    payload = {
        "packageName": "com.example.app",
        "type": kind,
        "sessionId": 1,
        "requestUrl": url,
        "domain": domain,
        "thirdPartyRequest": third_party,
        "modifiedMetaReason": modified_meta or [],
        "modifiedContentReasons": modified_content or [],
        "creationTime": creation_time,
        "elapsedTime": 10,
        "sent": 100,
        "received": 200,
        "resourceTypes": resource_types or [],
        "requestStatuses": statuses or [],
        "mainRequestStatus": main_status,
        "appliedRules": rules or {},
        "requestBlockedByBrowsingSecurityModule": False,
        "requestBlockedReason": blocked_reason or [],
        "requestFailedReason": failed_reason or [],
    }
    return {"id": record_id, "event": {"processedProxyRequest": payload}}


def dns_record(record_id=3):
    return {
        "id": record_id,
        "event": {
            "dnsRequest": {
                "packageName": "com.adguard.dns",
                "domain": "ads.example.",
                "requestUrl": "dns://ads.example./",
                "requestType": "A",
                "answer": "A, 0.0.0.0",
                "rules": {"1": ["||ads.example^"]},
                "elapsedTime": 1,
                "startTime": 1700000001000,
                "requestStatus": "BLOCKED",
                "sent": 0,
                "received": 0,
                "blockingReason": "QUERY_MATCHED_BY_RULE",
            }
        },
    }


def whitelist_record(record_id=4):
    return {
        "id": record_id,
        "event": {
            "whitelistedByNetworkRuleRequest": {
                "packageName": "com.example.app",
                "domain": "1.2.3.4:443",
                "requestUrl": "tcp://1.2.3.4:443",
                "creationTime": 1700000002000,
                "elapsedTime": 5,
                "sent": 0,
                "received": 0,
                "appliedRule": {
                    "type": "BASIC_EXCEPTIONS",
                    "filterListId": -1,
                    "isWhitelist": True,
                    "ruleText": "@@1.2.3.4:443$network,app=com.example.app",
                },
            }
        },
    }


def sample_data():
    return [
        proxy_record(1),
        proxy_record(
            2,
            kind="WebRequest",
            url="https://cdn.example.com/video.mp4",
            domain="cdn.example.com",
            third_party=True,
            resource_types=["MEDIA"],
            statuses=["MODIFIED_META"],
            main_status="MODIFIED_META",
            modified_meta=["STEALTHMODE"],
        ),
        dns_record(),
        whitelist_record(),
    ]


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.records, self.skipped = parser.parse_records(sample_data())
        self.by_id = {record.id: record for record in self.records}

    def ids(self, **filters):
        query = parser.Filters(**filters)
        return [record.id for record in self.records if query.matches(record)]

    def test_parse(self):
        self.assertEqual(len(self.records), 4)
        self.assertEqual(self.skipped, 0)

        tunnel = self.by_id[1]
        self.assertEqual(tunnel.event_label, "proxy:tunnel")
        self.assertEqual(tunnel.status, "NONE")
        self.assertEqual(tunnel.side, "1p")
        self.assertEqual(tunnel.content, [])

        web = self.by_id[2]
        self.assertEqual(web.event_label, "proxy:web")
        self.assertEqual(web.status, "META_MODIFIED")
        self.assertEqual(web.side, "3p")
        self.assertEqual(web.content, ["MEDIA"])

        dns = self.by_id[3]
        self.assertEqual(dns.status, "BLOCKED")
        self.assertEqual(dns.content, ["A"])
        self.assertEqual(dns.rules, ["||ads.example^"])

        whitelist = self.by_id[4]
        self.assertEqual(whitelist.status, "WHITELISTED")
        self.assertEqual(
            whitelist.rules, ["@@1.2.3.4:443$network,app=com.example.app"]
        )

    def test_parse_skips_malformed(self):
        records, skipped = parser.parse_records(
            [
                {"id": 1},
                {"id": 2, "event": None},
                {"id": 3, "event": {"dnsRequest": {}}},
            ]
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(skipped, 2)
        self.assertEqual(records[0].status, "NONE")

    def test_new_event_types(self):
        data = [
            {
                "id": 10,
                "event": {
                    "bypassedRequest": {
                        "packageName": "com.example.app",
                        "domain": "1.2.3.4:443",
                        "requestUrl": "tcp://1.2.3.4:443",
                        "creationTime": 1700000000000,
                    }
                },
            },
            {
                "id": 11,
                "event": {
                    "blockedByFirewallRequest": {
                        "packageName": "com.example.app",
                        "domain": "5.6.7.8:443",
                        "requestUrl": "tcp://5.6.7.8:443",
                        "creationTime": 1700000001000,
                        "firewallBlockingStrategy": {
                            "blockedByAppRuleOnWifi": {"networkType": "WiFi"}
                        },
                    }
                },
            },
        ]
        records, _ = parser.parse_records(data)
        self.assertEqual(records[0].status, "BYPASSED")
        self.assertEqual(records[0].event_label, "bypass")
        self.assertEqual(records[1].status, "BLOCKED")
        self.assertEqual(records[1].event_label, "firewall")

        bypass_filter = parser.Filters(events=["bypassed"])
        firewall_filter = parser.Filters(events=["firewall"])
        self.assertEqual(
            [record.id for record in records if bypass_filter.matches(record)],
            [10],
        )
        self.assertEqual(
            [record.id for record in records if firewall_filter.matches(record)],
            [11],
        )

    def test_event_filter(self):
        self.assertEqual(self.ids(events=["dns"]), [3])
        self.assertEqual(self.ids(events=["tunnel"]), [1])
        self.assertEqual(self.ids(events=["web"]), [2])
        self.assertEqual(self.ids(events=["whitelist"]), [4])
        self.assertEqual(self.ids(events=["proxy"]), [1, 2])
        self.assertEqual(self.ids(events=["dnsRequest"]), [3])
        self.assertEqual(self.ids(events=["proxy:web"]), [2])

    def test_content_filter(self):
        self.assertEqual(self.ids(content_types=["media"]), [2])
        self.assertEqual(self.ids(content_types=["A"]), [3])
        self.assertEqual(self.ids(content_types=["none"]), [1, 4])
        self.assertEqual(self.ids(content_types=["xhr"]), [])

    def test_status_filter(self):
        self.assertEqual(self.ids(statuses=["blocked"]), [3])
        self.assertEqual(self.ids(statuses=["modified"]), [])
        self.assertEqual(self.ids(statuses=["modified_meta"]), [2])
        self.assertEqual(self.ids(statuses=["meta_modified"]), [2])
        self.assertEqual(self.ids(statuses=["whitelisted"]), [4])
        self.assertEqual(self.ids(statuses=["none"]), [1])
        self.assertEqual(self.ids(statuses=["processed"]), [1])
        self.assertEqual(self.ids(statuses=["allowed"]), [4])
        self.assertEqual(self.ids(statuses=["query_matched_by_rule"]), [3])

    def test_side_filter(self):
        self.assertEqual(self.ids(sides=["1p"]), [1])
        self.assertEqual(self.ids(sides=["3p"]), [2])
        self.assertEqual(self.ids(sides=["unknown"]), [3, 4])

    def test_text_filters(self):
        self.assertEqual(self.ids(apps=["example"]), [1, 2, 4])
        self.assertEqual(self.ids(domains=["example.com"]), [1, 2])
        self.assertEqual(self.ids(rules=["ads.example"]), [3])
        self.assertEqual(self.ids(search="tcp://"), [4])

    def test_combined_filters(self):
        self.assertEqual(self.ids(events=["dns"], statuses=["blocked"]), [3])
        self.assertEqual(self.ids(events=["proxy"], sides=["1p"]), [1])
        self.assertEqual(
            self.ids(
                events=["proxy"],
                content_types=["media"],
                statuses=["meta_modified"],
            ),
            [2],
        )

    def test_deduplication(self):
        data = sample_data()
        duplicate = json.loads(json.dumps(data[0]))
        duplicate["id"] = 5
        duplicate["event"]["processedProxyRequest"]["creationTime"] += 1000
        data.append(duplicate)
        duplicate = json.loads(json.dumps(data[0]))
        duplicate["id"] = 6
        duplicate["event"]["processedProxyRequest"]["creationTime"] += 2000
        data.append(duplicate)

        records, _ = parser.parse_records(data)
        unique = parser.deduplicate(records, parser.DEFAULT_DEDUP_FIELDS)
        self.assertEqual(len(unique), 4)
        tunnel = [
            record
            for record in unique
            if record.event_label == "proxy:tunnel"
        ][0]
        self.assertEqual(tunnel.count, 3)
        self.assertEqual(tunnel.id, 1)

        unique_last = parser.deduplicate(
            records, parser.DEFAULT_DEDUP_FIELDS, keep="last"
        )
        tunnel_last = [
            record
            for record in unique_last
            if record.event_label == "proxy:tunnel"
        ][0]
        self.assertEqual(tunnel_last.count, 3)
        self.assertEqual(tunnel_last.id, 6)

    def test_rendering(self):
        table = parser.render_table(
            self.records, ["id", "status", "content", "side"], 48
        )
        self.assertIn("BLOCKED", table)
        self.assertIn("proxy:web", parser.render_table(
            self.records, ["event_label"], 48
        ))

        csv_text = parser.render_csv(self.records, ["id", "status", "rules"])
        self.assertIn("||ads.example^", csv_text)

        json_rows = json.loads(
            parser.render_json(self.records, ["id", "status"], False)
        )
        self.assertEqual(json_rows[2], {"id": 3, "status": "BLOCKED"})

    def test_html_rendering(self):
        template = (ROOT / "filtering_log_viewer.html").read_text(
            encoding="utf-8"
        )
        html_text = parser.render_html(self.records, template, "test.json")
        self.assertIn("const PRELOADED_DATA = [", html_text)
        self.assertIn('const PRELOADED_SOURCE = "test.json";', html_text)
        self.assertIn("BLOCKED", html_text)
        self.assertNotIn("const PRELOADED_DATA = null;", html_text)


class RealLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "recent_activity.json"
        if not cls.path.exists():
            raise unittest.SkipTest("recent_activity.json not found")

    def test_real_log_counts(self):
        records, skipped = parser.load_records(str(self.path))
        self.assertEqual(len(records), 82)
        self.assertEqual(skipped, 0)
        self.assertEqual(
            sum(record.status == "BLOCKED" for record in records), 4
        )
        self.assertEqual(
            sum(record.status == "META_MODIFIED" for record in records), 2
        )
        self.assertEqual(
            sum(record.status == "WHITELISTED" for record in records), 6
        )

        unique = parser.deduplicate(records, parser.DEFAULT_DEDUP_FIELDS)
        self.assertEqual(len(unique), 44)
        self.assertEqual(sum(record.count for record in unique), 82)

    def test_cli(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "adguard_log_parser.py"),
                str(self.path),
                "--event",
                "dns",
                "--status",
                "blocked",
                "--format",
                "json",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["event_label"] == "dns" for row in rows))
        self.assertTrue(all(row["status"] == "BLOCKED" for row in rows))

    def test_cli_html(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "filtering_log.html"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "adguard_log_parser.py"),
                    str(self.path),
                    "--event",
                    "dns",
                    "--status",
                    "blocked",
                    "--format",
                    "html",
                    "--output",
                    str(output),
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            html_text = output.read_text(encoding="utf-8")
            self.assertIn("const PRELOADED_DATA = [", html_text)
            self.assertNotIn("const PRELOADED_DATA = null;", html_text)
            self.assertIn("AdGuard Filtering Log", html_text)
            self.assertIn("BLOCKED", html_text)


if __name__ == "__main__":
    unittest.main()
