from pytz import timezone

# Headers to avoid getting banned
"""
This only works locally, totally failed on Heroku and AWS
Nasdaq stops sending data
"""
hack_headers = {
        'user-agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        'accept-language' : "es-ES,es;q=0.9",
        'cache-control' : "no-cache",
        'sec-fetch-site': "cross-site"
    }

# Trading hours for Nasdaq: Eastern Time Zone
time_zone = timezone('EST')