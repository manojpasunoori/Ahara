from datetime import datetime
from zoneinfo import ZoneInfo

def local_now(timezone: str, now: datetime | None = None) -> datetime:
    return (now or datetime.now(tz=ZoneInfo('UTC'))).astimezone(ZoneInfo(timezone))

def meal_period(value: datetime) -> str:
    total=value.hour*60+value.minute
    if total<300:return 'late-night'
    if total<630:return 'breakfast'
    if total<870:return 'lunch'
    if total<1050:return 'snacks'
    if total<1320:return 'dinner'
    return 'late-night'

