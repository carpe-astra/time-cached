from datetime import datetime, timedelta
from typing import Any, Dict, Hashable, List

from pydantic import BaseModel


class CacheObject(BaseModel):
    callable_id: str
    result: Any
    cached_at: datetime
    valid_for: timedelta
