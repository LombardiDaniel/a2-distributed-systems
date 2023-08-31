import asyncio
import json
import os
import random
from threading import Thread
from time import sleep
from uuid import uuid4

import paho.mqtt.client as mqtt

from utils.constants import Topics

CONTAINER_ID = os.getenv("HOSTNAME", "localhsot")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
CLIENT = mqtt.Client(f"SUPPLIER_{CONTAINER_ID}_{str(uuid4())}")

PRODUCTION_TIME = 10
DELIVERY_TIME = 5
DELIVERY_AMMOUNT_AVG = 1000
MAX_TASKS_CONCURRENT = 30

LOOP = asyncio.new_event_loop()
SEMAPHORE = asyncio.Semaphore(MAX_TASKS_CONCURRENT)

asyncio.set_event_loop(LOOP)


async def produce_part(part_num: int) -> int:
    await asyncio.sleep(PRODUCTION_TIME)

    add = random.randint(0, 1) % 2

    # podem vir peças com erro, entao qntd varia
    parts_count = DELIVERY_AMMOUNT_AVG
    rand_ = random.random() * part_num

    parts_count = int((parts_count + rand_) if add else (parts_count - rand_))

    await asyncio.sleep(DELIVERY_TIME)

    return parts_count


async def msg_callback_coroutine(msg):
    # print("starting callback routine")
    async with SEMAPHORE:
        if msg.topic == Topics.REQUEST_TO_SUPPLIER:
            payload = json.loads(msg.payload)
            requested_part_num = payload["partNum"]
            tgt = payload["src"]

            print(f"Recieved request for '{requested_part_num}'")

            parts_ammount = await produce_part(requested_part_num)

            print(f"Deliveried {requested_part_num}x '{parts_ammount}'")

            CLIENT.publish(
                Topics.RESPONSE_FROM_SUPPLIER,
                json.dumps(
                    {
                        "src": CONTAINER_ID,
                        "tgt": tgt,
                        "partNum": requested_part_num,
                        "count": parts_ammount,
                    }
                ),
            ).wait_for_publish()


def msg_callback(client, userdata, msg):
    asyncio.run_coroutine_threadsafe(msg_callback_coroutine(msg), loop=LOOP)
    # print("msg_callback done")


def main():
    Thread(target=LOOP.run_forever).start()
    CLIENT.on_message = msg_callback

    CLIENT.connect(MQTT_BROKER, 1883)

    CLIENT.subscribe("#")
    sleep(5)

    CLIENT.loop_forever()


if __name__ == "__main__":
    main()
