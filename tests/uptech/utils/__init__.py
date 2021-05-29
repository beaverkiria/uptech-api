from datetime import datetime


def dt_to_timestamp(dt: datetime) -> int:
    return int(dt.strftime("%s"))
