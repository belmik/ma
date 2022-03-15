import itertools
from collections import deque
from decimal import Decimal, getcontext
from json import JSONDecodeError
from os import environ
from time import sleep
from typing import Any

import requests

EXCHANGE_RATE_ENDPOINT_URL = environ.get("EXCHANGE_RATE_ENDPOINT_URL", "")
getcontext().prec = 8

if not EXCHANGE_RATE_ENDPOINT_URL:
    exit("EXCHANGE_RATE_ENDPOINT_URL is not set")


def get_new_data(url: str) -> Any:
    try:
        data = requests.get(url).json()
    except JSONDecodeError:
        print("Got no json or broken json answer from the endpoind.")
        return False
    except Exception as e:
        print(f"During call to the endpoind raised exception {e}")
        return False

    if "status" not in data:
        print("There is no status in the answer, don't know what to do.")
        return False

    if data["status"] == "error":
        print(f"Got error from server: {data['detail']}")

    return data["rates"]


def init_collection() -> dict[str, deque[Decimal]]:
    data = get_new_data(EXCHANGE_RATE_ENDPOINT_URL)
    pairs = {}

    for item in data:
        price_deque: deque[Decimal] = deque(maxlen=60)
        price_deque.append(Decimal(str(item["price"])))

        pair = {item["pair"]: price_deque}
        pairs.update(pair)

    return pairs


def update_collection(pairs: dict[str, deque[Decimal]]) -> dict[str, deque[Decimal]]:
    new_data = get_new_data(EXCHANGE_RATE_ENDPOINT_URL)

    for item in new_data:
        pairs[item["pair"]].append(Decimal(str(item["price"])))

    return pairs


def calculate_ma(prices: deque[Decimal], size: int) -> Decimal:
    prices_count = len(prices)
    if prices_count < size:
        return Decimal(0)
    tail = itertools.islice(prices, prices_count - size, None)
    return sum(tail) / Decimal(size)


if __name__ == "__main__":
    print("Starting gathering data, you need to wait at least one minute before ma starts to showing up.")
    pairs = init_collection()
    while True:
        sleep(5)
        pairs = update_collection(pairs)
        for pair, prices in pairs.items():
            ma_12 = calculate_ma(prices, 12)
            ma_60 = calculate_ma(prices, 60)
            print(f"{pair} - ma12:{ma_12}, ma60:{ma_60}")
