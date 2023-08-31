import asyncio
import datetime
import json
import os
from queue import Queue
from threading import Thread
from time import sleep
from uuid import uuid4

import paho.mqtt.client as mqtt

from utils import Stock
from utils.constants import PART_TYPES_COUNT, Topics

CONTAINER_ID = os.getenv("HOSTNAME", "localhsot")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
CLIENT = mqtt.Client(f"WAREHOUSE_{CONTAINER_ID}_{str(uuid4())}")

DELIVERY_TIME = 5
DELIVERY_AMMOUNT = 100

STOCK = Stock()
ON_ORDER_DICT = {str(i): False for i in range(PART_TYPES_COUNT)}

RED_KANBAN_MARK = 500

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)

ENABLE_DELTA = 30
START = datetime.datetime.now()


def stock_monitoring_rountine():
    while True:
        curr_stock = STOCK.get_stock()

        print(f"CURRENT STOCK: {STOCK}")
        # print(curr_stock)

        for k, v in curr_stock.items():
            if v < RED_KANBAN_MARK:
                if not ON_ORDER_DICT[k]:
                    ON_ORDER_DICT[k] = True
                    request_part(int(k))

        sleep(1)


def request_part(part_num: int):
    print(f"Requesting '{part_num}'")

    CLIENT.publish(
        Topics.REQUEST_TO_SUPPLIER,
        json.dumps(
            {
                "src": CONTAINER_ID,
                "partNum": part_num,
            }
        ),
    ).wait_for_publish()


async def deliver_part(part_num: int, tgt: str) -> None:
    # def deliver_part(part_num: int, tgt: str) -> None:
    # while not STOCK.is_full():
    #     sleep(1)

    STOCK.remove(part_num, DELIVERY_AMMOUNT)  # may hang

    print(f"Sending '{part_num}' to '{tgt}'.")

    await asyncio.sleep(DELIVERY_TIME)
    # sleep(DELIVERY_TIME)

    CLIENT.publish(
        Topics.RESPONSE_FROM_WAREHOUSE,
        json.dumps(
            {
                "src": CONTAINER_ID,
                "tgt": tgt,
                "partNum": part_num,
                "count": DELIVERY_AMMOUNT,
            }
        ),
    ).wait_for_publish()


async def msg_callback_coroutine(msg):
    if msg.topic == Topics.RESPONSE_FROM_SUPPLIER:
        print(msg.topic, msg.payload)
        payload = json.loads(msg.payload)
        recvd_part_num = payload["partNum"]
        recvd_ammount = payload["count"]

        print(f"Recieved {recvd_ammount}x '{recvd_part_num}'")
        STOCK.add(recvd_part_num, recvd_ammount)
        ON_ORDER_DICT[str(recvd_part_num)] = False

        return

    if msg.topic == Topics.REQUEST_TO_WAREHOUSE:
        print(msg.topic, msg.payload)
        payload = json.loads(msg.payload)
        recvd_part_num = payload["partNum"]
        tgt = payload["src"]

        await deliver_part(recvd_part_num, tgt)

        return


def msg_callback(client, userdata, msg):
    # Thread(target=msg_callback_coroutine, args=(msg,)).start()
    asyncio.run_coroutine_threadsafe(msg_callback_coroutine(msg), loop=LOOP)
    return


def main():
    Thread(target=LOOP.run_forever).start()

    CLIENT.on_message = msg_callback

    CLIENT.connect(MQTT_BROKER, 1883)

    Thread(target=stock_monitoring_rountine).start()

    CLIENT.subscribe("#")
    sleep(5)

    CLIENT.loop_forever()


if __name__ == "__main__":
    main()
