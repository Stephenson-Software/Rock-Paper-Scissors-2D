"""Tests for the usage-reporting wiring: the settings block, the one-time notice, the
opt-outs, and the startup event arriving at a loopback stub. Nothing here contacts the
real service."""
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import usage_reporting  # noqa: E402
from usage_reporting import (  # noqa: E402
    APPLICATION,
    DEFAULT_ENDPOINT,
    DEFAULT_KEY,
    DETAILS_URL,
    FIRST_RUN_NOTICE,
    FIRST_RUN_NOTICE_OFF_BY_ENVIRONMENT,
    SETTINGS_FILE,
    VERSION,
    buildClient,
    loadSettings,
    startUsageReporting,
)

_ENV_VARS = ("TRACE_USAGE_REPORTING", "DO_NOT_TRACK")


def _scrubEnvironment(test):
    """The machine running the tests may itself have opted out of usage reporting; every
    test starts from a clean environment and sets what it needs."""
    scrubbed = {k: v for k, v in os.environ.items() if k not in _ENV_VARS}
    patcher = patch.dict(os.environ, scrubbed, clear=True)
    patcher.start()
    test.addCleanup(patcher.stop)


def _stubServer(requests, arrived):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            requests.append({
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "body": json.loads(self.rfile.read(length).decode("utf-8")),
            })
            self.send_response(201)
            self.send_header("Content-Length", "0")
            self.end_headers()
            arrived.set()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class TestUsageReportingSettings(unittest.TestCase):
    def setUp(self):
        _scrubEnvironment(self)
        self.tempDir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempDir.cleanup)
        self.settingsFile = os.path.join(self.tempDir.name, "settings.json")
        self.logged = []

    def log(self, message):
        self.logged.append(message)

    def readSettingsFile(self):
        with open(self.settingsFile, "r") as f:
            return json.load(f)

    def test_application_name_and_shipped_key(self):
        self.assertEqual("Rock-Paper-Scissors-2D", APPLICATION)
        self.assertEqual(43, len(DEFAULT_KEY))
        self.assertEqual("https://trace.danielstephenson.dev", DEFAULT_ENDPOINT)

    def test_settings_file_is_settings_json_at_the_repository_root(self):
        self.assertEqual(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json"), SETTINGS_FILE)

    def test_first_run_writes_defaults_and_shows_the_notice_once(self):
        section = loadSettings(self.settingsFile, self.log)

        self.assertEqual({"enabled": True, "endpoint": DEFAULT_ENDPOINT, "key": DEFAULT_KEY}, section)
        self.assertEqual([FIRST_RUN_NOTICE], self.logged)
        self.assertEqual({"usage_reporting": section}, self.readSettingsFile())

        self.logged.clear()
        self.assertEqual(section, loadSettings(self.settingsFile, self.log))
        self.assertEqual([], self.logged, "the notice must not be shown on the second run")

    def test_notice_says_it_is_on_and_names_every_opt_out(self):
        self.assertTrue(FIRST_RUN_NOTICE.startswith("Usage reporting is on: Rock-Paper-Scissors-2D sends"))
        self.assertIn("https://trace.danielstephenson.dev", FIRST_RUN_NOTICE)
        self.assertIn('"enabled": false', FIRST_RUN_NOTICE)
        self.assertIn("TRACE_USAGE_REPORTING=off", FIRST_RUN_NOTICE)
        self.assertIn(DETAILS_URL, FIRST_RUN_NOTICE)
        self.assertEqual("https://github.com/Stephenson-Software/trace#usage-reporting", DETAILS_URL)
        self.assertNotIn("\n", FIRST_RUN_NOTICE)

    def test_first_run_under_an_environment_opt_out_says_reporting_is_off(self):
        with patch.dict(os.environ, {"DO_NOT_TRACK": "1"}):
            loadSettings(self.settingsFile, self.log)

        self.assertEqual([FIRST_RUN_NOTICE_OFF_BY_ENVIRONMENT], self.logged)
        self.assertIn(DETAILS_URL, FIRST_RUN_NOTICE_OFF_BY_ENVIRONMENT)

    def test_existing_settings_without_the_block_are_preserved(self):
        with open(self.settingsFile, "w") as f:
            json.dump({"other": {"kept": 1}}, f)

        loadSettings(self.settingsFile, self.log)

        written = self.readSettingsFile()
        self.assertEqual({"kept": 1}, written["other"])
        self.assertTrue(written["usage_reporting"]["enabled"])

    def test_opt_out_is_respected_and_not_rewritten(self):
        with open(self.settingsFile, "w") as f:
            json.dump({"usage_reporting": {"enabled": False}}, f)

        client = buildClient(loadSettings(self.settingsFile, self.log))

        self.assertFalse(client.enabled)
        self.assertEqual("config", client.disabled_reason)
        self.assertEqual([], self.logged)
        self.assertEqual({"usage_reporting": {"enabled": False}}, self.readSettingsFile())

    def test_unreadable_settings_file_disables_reporting_without_raising(self):
        with open(self.settingsFile, "w") as f:
            f.write("{not json")

        section = loadSettings(self.settingsFile, self.log)

        self.assertIsNone(section)
        self.assertFalse(buildClient(section).enabled)
        self.assertIn("usage reporting is off", self.logged[0])
        with open(self.settingsFile, "r") as f:
            self.assertEqual("{not json", f.read(), "a broken settings file must not be overwritten")

    def test_missing_endpoint_and_key_fall_back_to_the_shipped_defaults(self):
        client = buildClient({"enabled": True})

        self.assertTrue(client.enabled)
        self.assertEqual(DEFAULT_ENDPOINT + "/api/metrics", client._endpoint)
        self.assertEqual(DEFAULT_KEY, client._key)
        client.close()  # nothing was reported, so nothing is sent


class TestStartupEvent(unittest.TestCase):
    def setUp(self):
        _scrubEnvironment(self)
        self.tempDir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempDir.cleanup)
        self.settingsFile = os.path.join(self.tempDir.name, "settings.json")
        self.requests = []
        self.arrived = threading.Event()
        self.server = _stubServer(self.requests, self.arrived)
        self.addCleanup(self.server.shutdown)
        self.endpoint = "http://127.0.0.1:%d" % self.server.server_address[1]

    def writeSettings(self, enabled):
        with open(self.settingsFile, "w") as f:
            json.dump({"usage_reporting": {"enabled": enabled, "endpoint": self.endpoint, "key": "test-key"}}, f)

    def test_startup_event_reaches_the_configured_endpoint_with_name_and_version(self):
        self.writeSettings(True)

        with patch("usage_reporting.atexit"):
            client = startUsageReporting(self.settingsFile, lambda message: None)
        self.addCleanup(client.close)

        self.assertTrue(self.arrived.wait(5), "the startup event should reach the stub server")
        request = self.requests[0]
        self.assertEqual("/api/metrics", request["path"])
        self.assertEqual("Bearer test-key", request["authorization"])
        self.assertEqual({"application": "Rock-Paper-Scissors-2D", "name": "startup", "tags": {"version": VERSION}},
                         request["body"])

    def test_opted_out_startup_sends_nothing(self):
        self.writeSettings(False)

        with patch("usage_reporting.atexit"):
            client = startUsageReporting(self.settingsFile, lambda message: None)

        self.assertFalse(client.enabled)
        self.assertFalse(self.arrived.wait(0.3))

    def test_environment_opt_out_wins_over_enabled_settings(self):
        self.writeSettings(True)

        for variable, value in (("DO_NOT_TRACK", "1"), ("TRACE_USAGE_REPORTING", "off")):
            with self.subTest(variable=variable):
                with patch("usage_reporting.atexit"), patch.dict(os.environ, {variable: value}):
                    client = startUsageReporting(self.settingsFile, lambda message: None)

                self.assertFalse(client.enabled)
                self.assertEqual("environment", client.disabled_reason)
                self.assertFalse(self.arrived.wait(0.3))
                self.assertEqual([], self.requests)

    def test_start_never_raises_even_if_settings_loading_fails(self):
        with patch("usage_reporting.loadSettings", side_effect=RuntimeError("boom")):
            client = startUsageReporting(self.settingsFile, lambda message: None)

        self.assertFalse(client.enabled)


if __name__ == "__main__":
    unittest.main()
