"""MQTT data source: receives readings from sensor nodes over Wi-Fi.

Subscribes to aq/+/reading and aq/+/status on the broker and passes each
reading to the same callback the serial reader and the simulator use.
Works with paho-mqtt 1.x and 2.x.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from config import MQTT_HOST, MQTT_PORT, MQTT_TOPIC_PREFIX

ReadingCallback = Callable[[Dict[str, Any]], Any]

node_status: Dict[str, str] = {}  # node_id -> "online" / "offline"


def handle_message(topic: str, payload: bytes, callback: ReadingCallback) -> Optional[Dict[str, Any]]:
    """Decode one MQTT message. Returns the reading passed to the callback, if any."""
    parts = topic.split('/')
    if len(parts) != 3 or parts[0] != MQTT_TOPIC_PREFIX:
        return None
    _, node_id, kind = parts

    try:
        data = json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        print(f"   ⚠️ Bad JSON on {topic}")
        return None

    if kind == 'status':
        status = data.get('status', 'unknown')
        node_status[node_id] = status
        print(f"   📶 Node {node_id} is {status}")
        return None

    if kind != 'reading' or data.get('type') != 'reading':
        return None

    # Readings sent late (after a Wi-Fi drop) carry their age, so date them
    # from when they were measured, not when they arrived.
    age_ms = data.pop('age_ms', 0) or 0
    data['timestamp'] = (datetime.now() - timedelta(milliseconds=age_ms)).isoformat()
    if age_ms > 0:
        measured = datetime.now(timezone.utc) - timedelta(milliseconds=age_ms)
        data['measured_at_utc'] = measured.strftime('%Y-%m-%d %H:%M:%S')  # SQLite format
    if age_ms > 60_000:
        print(f"   ⏪ Late reading #{data.get('reading_num')} from {node_id} ({age_ms / 1000:.0f} s old)")

    callback(data)
    return data


def _make_client():
    import paho.mqtt.client as mqtt
    try:  # paho-mqtt 2.x
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='aq-backend')
    except AttributeError:  # paho-mqtt 1.x
        return mqtt.Client(client_id='aq-backend')


def start(callback: ReadingCallback, host: str = MQTT_HOST, port: int = MQTT_PORT):
    """Connect in the background and keep retrying if the broker goes away."""
    client = _make_client()

    def on_connect(client, userdata, *args):
        client.subscribe(f'{MQTT_TOPIC_PREFIX}/+/reading', qos=0)
        client.subscribe(f'{MQTT_TOPIC_PREFIX}/+/status', qos=1)
        print(f"   ✅ MQTT connected to {host}:{port}")

    def on_disconnect(client, userdata, *args):
        print("   ⚠️ MQTT disconnected, retrying...")

    def on_message(client, userdata, msg):
        try:
            handle_message(msg.topic, msg.payload, callback)
        except Exception as e:  # one bad reading must not stop the client
            print(f"   ❌ Error processing {msg.topic}: {e}")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    print(f"📡 MQTT source starting (broker {host}:{port})...")
    client.connect_async(host, port, keepalive=60)
    client.loop_start()
    return client
