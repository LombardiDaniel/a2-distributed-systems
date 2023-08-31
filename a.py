from queue import Queue
from threading import Thread
from time import sleep

Q = Queue()


def add():
    sleep(5)
    Q.put(0)


def main():
    Thread(target=add).start()
    a = Q.get()
    print("done")
    print(a)


if __name__ == "__main__":
    main()
