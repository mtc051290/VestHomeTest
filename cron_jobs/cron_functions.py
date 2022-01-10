from datetime import datetime
from pytz import timezone


def get_today_datetime_variations():
    now = datetime.now(timezone('EST'))
    today_variations = {
        "time_as_of"        : now.strftime("%b %d, %Y"),
        "time_as_of_long"   : now.strftime("DATA AS OF %b %d, %Y"),
        "datetime"          : now.strftime("%I:%M:%S %p ET")
    }
    return today_variations