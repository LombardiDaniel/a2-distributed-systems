from queue import Queue
from typing import Mapping

from .constants import PART_TYPES_COUNT


class Stock:
    def __init__(self):
        self._d = {str(i): Queue() for i in range(PART_TYPES_COUNT)}
        # self._d = {
        #     "$PART_NUM": PART_LST
        # }

    def is_empty(self) -> bool:
        for k, v in self._d.items():
            if not v.empty():
                return False

        return True

    def is_full(self) -> bool:
        for k, v in self._d.items():
            if v.empty():
                return False

        return True

    def add(self, part: int, ammount: int) -> None:
        for _ in range(ammount):
            self._d[str(part)].put(0)

    def remove(self, part: int, ammount: int) -> None:
        for _ in range(ammount):
            self._d[str(part)].get()

    def get_stock(self) -> Mapping[str, int]:
        """
        Returns:
            d[part_num]: part_ammount
        """

        d = {}

        for k, v in self._d.items():
            d[str(k)] = v.qsize()

        return d

    def __repr__(self) -> str:
        d = self.get_stock()

        total = sum(d.values())

        return str(total)
