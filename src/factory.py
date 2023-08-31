import asyncio
import json
import os
import random
from queue import Queue
from threading import Thread
from time import sleep
from uuid import uuid4

import paho.mqtt.client as mqtt

from utils import Stock, get_sleep_time
from utils.constants import PART_TYPES_COUNT, Topics

CONTAINER_ID = os.getenv("HOSTNAME", "localhsot")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
CLIENT = mqtt.Client(f"FACTORY_{CONTAINER_ID}_{str(uuid4())}")

STOCK = Stock()

RED_KANBAN_MARK = 100
N_LINHAS_PROD = 5
PRODUCTION_TIME_AVG = 5

ON_ORDER_DICT = {str(i): False for i in range(PART_TYPES_COUNT)}

TO_BE_PRODUCED_QUEUE = Queue()
ALREADY_PRODUCED_QUEUE = Queue()


PRODUCT_BLUEPRINTS = {
    str(num): random.sample(range(100 + 1), random.randint(20, 33)) for num in range(5)
}

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)


def clients():
    while True:
        sleep(get_sleep_time(20))
        product_id = random.randint(0, 4)
        ammount = random.randint(10, 20)
        print(f"CLIENT: requesting {ammount}x product_{product_id}")
        for _ in range(ammount):
            CLIENT.publish(
                Topics.REQUEST_TO_FACTORY,
                json.dumps({"src": CONTAINER_ID, "partNum": product_id}),
            ).wait_for_publish()


def delivery():
    while True:
        product_id = ALREADY_PRODUCED_QUEUE.get()  # may hang
        print(f"DELIVERY: 1x product_{product_id} OUT!")
        CLIENT.publish(
            Topics.RESPONSE_FROM_FACTORY,
            json.dumps(
                {
                    "src": CONTAINER_ID,
                    "tgt": "clientsGenericNotSpecified",
                    "partNum": product_id,
                    "count": 1,
                }
            ),
        ).wait_for_publish()


def linha_producao(i):
    while True:
        product_id = TO_BE_PRODUCED_QUEUE.get()  # may hang
        print(f"LINHA_{i} produzindo...product_{product_id}")

        parts_lst = PRODUCT_BLUEPRINTS[str(product_id)]
        parts = [STOCK.remove(part_id, 1) for part_id in parts_lst]  # hangs if needed
        sleep(get_sleep_time(PRODUCTION_TIME_AVG))
        del parts  # consumed parts
        print(f"LINHA_{i} product_{product_id} DONE!")
        ALREADY_PRODUCED_QUEUE.put(product_id)


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
    print(f"Requesting part num: '{part_num}'")
    CLIENT.publish(
        Topics.REQUEST_TO_WAREHOUSE,
        json.dumps(
            {
                "src": CONTAINER_ID,
                "partNum": part_num,
            }
        ),
    ).wait_for_publish()


async def msg_callback_coroutine(msg):
    if msg.topic == Topics.RESPONSE_FROM_WAREHOUSE:
        print(msg.topic, msg.payload)
        payload = json.loads(msg.payload)

        if payload["tgt"] != CONTAINER_ID:  # discard msgs for other factories
            return

        recvd_part_num = payload["partNum"]
        recvd_ammount = payload["count"]

        STOCK.add(recvd_part_num, recvd_ammount)
        ON_ORDER_DICT[str(recvd_part_num)] = False

        return

    if msg.topic == Topics.REQUEST_TO_FACTORY:
        TO_BE_PRODUCED_QUEUE.put(random.sample(range(5), 1)[0])
        print(f"QUEUE SIZE: '{TO_BE_PRODUCED_QUEUE.qsize()}'")

        return


def msg_callback(client, userdata, msg):
    asyncio.run_coroutine_threadsafe(msg_callback_coroutine(msg), loop=LOOP)


def main():
    sleep(60)
    Thread(target=LOOP.run_forever).start()

    CLIENT.on_message = msg_callback

    CLIENT.connect(MQTT_BROKER, 1883)

    CLIENT.subscribe("#")
    sleep(15)

    for i in range(N_LINHAS_PROD):
        Thread(target=linha_producao, args=(i,)).start()

    for routine in (delivery, clients, stock_monitoring_rountine):
        Thread(target=routine).start()

    CLIENT.loop_forever()


if __name__ == "__main__":
    main()
