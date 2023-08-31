"""
Inspects MQTT instance
"""

import json
import os
from pprint import pprint
from uuid import uuid4

import paho.mqtt.client as mqtt

from utils.constants import Topics

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")


def on_message(client, userdata, msg):
    """ """

    print("\n\nMSG RECIEVED:")
    print(f"TOPIC: '{str(msg.topic)}'")
    try:
        print(msg.payload)
        msg_str = msg.payload.decode()
        # print(msg_str)
        loaded = json.loads(msg_str)
        print("\n\nMSG RECIEVED:")
        pprint(loaded)
    except:
        pass


def main():
    client = mqtt.Client(f"inspector-{uuid4()}")
    client.on_message = on_message

    client.connect(MQTT_BROKER, 1883)

    # client.subscribe("#")
    client.subscribe(Topics.RESPONSE_FROM_SUPPLIER)

    client.loop_forever()


if __name__ == "__main__":
    main()
