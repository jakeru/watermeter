#!/usr/bin/env python3

import argparse
import datetime
import json
import logging
import socket

# pip install paho-mqtt
import paho.mqtt.client as mqtt

MQTT_CLIENT_ID = "watermeter"
MQTT_TOPIC = "watermeter/volume"
MQTT_DEFAULT_PORT=1883

def report(data, mqtt_host, mqtt_port=MQTT_DEFAULT_PORT):
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.connect(mqtt_host, mqtt_port)
    client.publish(MQTT_TOPIC, data, qos=1, retain=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Watermeter reporter")
    parser.add_argument("--verbose", help="Verbose mode", action="store_true")
    parser.add_argument("--mqtt", metavar="HOST", help="Connect and report to a MQTT server", default="localhost")
    parser.add_argument("--mqtt-port", metavar="PORT", help="MQTT Port", type=int, default=MQTT_DEFAULT_PORT)
    parser.add_argument("value", help="Value to report")

    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = '%(asctime)-15s %(levelname)-7s %(name)-6s %(message)s'
    logging.basicConfig(format=log_format, level=log_level)
    log = logging.getLogger()

    data = json.dumps({
        "time": str(datetime.datetime.now(datetime.timezone.utc)),
        "value": int(args.value),
        "host": socket.gethostbyaddr(socket.gethostname())[0]
    })

    log.debug("Reporting value: %s to MQTT server %s:%d for topic %s",
        data, args.mqtt, args.mqtt_port, MQTT_TOPIC)

    report(data, args.mqtt, args.mqtt_port)
