import random


def get_sleep_time(time_s: float | int, /) -> float:
    # Calculate the sleep time with a deviation of 10%
    average_sleep_time = time_s  # 5 seconds average
    deviation = 0.1  # 10% deviation

    # Calculate the minimum and maximum sleep times
    min_sleep_time = average_sleep_time - (average_sleep_time * deviation)
    max_sleep_time = average_sleep_time + (average_sleep_time * deviation)

    # Generate a random sleep time within the range
    sleep_time = random.uniform(min_sleep_time, max_sleep_time)

    return sleep_time
