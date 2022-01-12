from pytz import timezone

# Headers to avoid getting banned
"""hack_headers = {
        'user-agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        'accept-language' : "es-ES,es;q=0.9",
        'cache-control' : "no-cache",
        'sec-fetch-site': "cross-site"
    }
    """
hack_headers = {
        'accept-language': "en-US,en;q=0.9",
        'accept-encoding': "gzip, deflate, br",
        'accept': "*/*",
        'x-api-source': "pc",
        'user-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        'if-none-match-': "55b03-e2b4b3f247507f7c1a18fda4a09f1340",
        'x-requested-with': "XMLHttpRequest",
        'connection': "keep-alive",
        'host': "shopee.com.my"
        }

# Trading hours for Nasdaq: Eastern Time Zone
time_zone = timezone('EST')