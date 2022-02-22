import datetime


def time_filter(time_obj: datetime.time) -> str:
    if time_obj.second > 0:
        return str(time_obj)
    return time_obj.strftime("%H:%M")


_WEEKDAYS = {0: "So", 1: "Mo", 2: "Di", 3: "Mi", 4: "Do", 5: "Fr", 6: "Sa"}


def weekday_filter(number: int) -> str:
    return _WEEKDAYS[number]


FILTERS = {"time_format": time_filter, "weekday_format": weekday_filter}
