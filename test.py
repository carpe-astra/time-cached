import time

from time_cached import timecache


@timecache(seconds=10)
def f(x):
    """Squares something"""
    time.sleep(10)
    return x * x


print(f(2))
