"""Tests for MQTT message handling (no broker needed).

Run from backend/:  python -m unittest discover tests
"""
import json
import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mqtt_source  # noqa: E402

READING = {"type": "reading", "node_id": "n1", "location": "Room", "temperature": 21.5,
           "humidity": 45.0, "pressure": 1012.0, "gas_resistance": 95000, "aqi": 55,
           "reading_num": 1}


def payload(d):
    return json.dumps(d).encode()


class HandleMessageTest(unittest.TestCase):
    def setUp(self):
        self.got = []

    def handle(self, topic, body):
        return mqtt_source.handle_message(topic, body, self.got.append)

    def test_live_reading_is_passed_on(self):
        self.handle('aq/n1/reading', payload({**READING, "age_ms": 0}))
        self.assertEqual(len(self.got), 1)
        self.assertNotIn('age_ms', self.got[0])
        self.assertNotIn('measured_at_utc', self.got[0])  # database uses arrival time

    def test_late_reading_is_dated_when_measured(self):
        self.handle('aq/n1/reading', payload({**READING, "age_ms": 300_000}))
        stamp = datetime.fromisoformat(self.got[0]['timestamp'])
        self.assertAlmostEqual((datetime.now() - stamp).total_seconds(), 300, delta=5)
        self.assertIn('measured_at_utc', self.got[0])

    def test_status_updates_node_state(self):
        self.handle('aq/n1/status', payload({"status": "offline"}))
        self.assertEqual(mqtt_source.node_status['n1'], 'offline')
        self.assertEqual(self.got, [])

    def test_bad_input_is_ignored(self):
        self.handle('aq/n1/reading', b'{not json')
        self.handle('other/n1/reading', payload(READING))
        self.handle('aq/n1/reply', payload({"type": "pong"}))
        self.assertEqual(self.got, [])


if __name__ == '__main__':
    unittest.main()
