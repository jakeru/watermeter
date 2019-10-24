#!/bin/bash
# Example script that fetches an image, reads the gauge values and
# reports them using MQTT.
set -e
IMAGE_URI=http://raspberrypi:8082/
IMAGE=/tmp/watermeter.jpg
PYTHON=./env/bin/python
MQTT_SERVER=atom
wget --output-document $IMAGE $IMAGE_URI
digits=$($PYTHON ./read_digits.py $IMAGE)
gauges=$($PYTHON ./read_gauges.py $IMAGE)
echo Reporting value: $digits$gauges
$PYTHON ./report.py --mqtt $MQTT_SERVER $digits$gauges
