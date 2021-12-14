import hashlib
import inspect
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware, Serializer
from tinydb_serialization.serializers import DateTimeSerializer

from time_cached.models import CacheObject


class TimeDeltaSerializer(Serializer):
    OBJ_CLASS = timedelta  # The class this serializer handles

    def encode(self, obj):
        return str(obj.total_seconds())

    def decode(self, s):
        return self.OBJ_CLASS(seconds=float(s))


serialization = SerializationMiddleware(JSONStorage)
serialization.register_serializer(DateTimeSerializer(), "TinyDate")
serialization.register_serializer(TimeDeltaSerializer(), "TinyTimeDelta")
db = TinyDB("time-cached-db.json", storage=serialization)


def get_callable_id(func, *args, **kwargs) -> str:
    func_path = f"{inspect.getsourcefile(func)}.{func.__name__}"
    pickled_call = pickle.dumps((func_path, args, kwargs))
    return hashlib.sha256(pickled_call).hexdigest()


def timecache(
    days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
):
    """Caches the function result for the declared timedelta"""
    time_delta = timedelta(
        days=days,
        seconds=seconds,
        microseconds=microseconds,
        milliseconds=milliseconds,
        minutes=minutes,
        hours=hours,
        weeks=weeks,
    )
    if time_delta < timedelta():
        raise ValueError("Time cache must be zero or greater.")
    now = datetime.now()

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            callable_id = get_callable_id(func, *args, **kwargs)
            callable_dicts = db.search(Query().callable_id == callable_id)

            if len(callable_dicts) > 1:
                raise ValueError(
                    "Multiple values cached for this result. Clear the db and try again."
                )

            elif len(callable_dicts) == 1:
                cache_object = CacheObject(**callable_dicts[0])
                if now < cache_object.cached_at + cache_object.valid_for:
                    return cache_object.result
                else:
                    db.remove(doc_ids=(callable_dicts[0].doc_id,))

            result = func(*args, **kwargs)
            cache_object = CacheObject(
                callable_id=callable_id,
                result=result,
                cached_at=now,
                valid_for=time_delta,
            )
            db.insert(cache_object.dict())

            return result

        return wrapper

    return decorator
