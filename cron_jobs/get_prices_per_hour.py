from json import load
import time
import multiprocessing
import pandas as pd
import yfinance as yf
import cron_functions






def cron_get_prices(loading_success, name=""):
    start_time = time.time()
    print("\n\n")






    print(cron_functions.get_today_datetime_variations())

    """
    #time.sleep(6)
    print("\n\n")
    data = yf.download(tickers='AAPL AMD GOOGL', period='1d', interval='1h', prepost=True, group_by="ticket")
    loading_success.value=True
    d = {idx: gp.xs(idx, level=0, axis=1) for idx, gp in data.groupby(level=0, axis=1)}

    for index, row in d['AAPL'].iterrows():
        print(f'{index}: {row["Open"]}   -   {row["Close"]}   -   {row["High"]}   -    {row["Low"]}')
    
    print(d['AMD'].index[0])
    """
    

    loading_success.value=True          #REMOVE THIS WHEN DONE
    print("\n\nResponse in %s seconds" % (time.time() - start_time))



if __name__ == '__main__':
    max_time=5
    max_repeat=5
    manager=multiprocessing.Manager()
    loading_success=manager.Value('loading_success',False)

    tries=0
    while loading_success.value==False and tries<max_repeat:


        p = multiprocessing.Process(target=cron_get_prices, args=(loading_success,'loading_success'))
        p.start(); p.join(max_time)


        tries+=1
        if p.is_alive():
            print (f"running... let's kill it... {loading_success.value}")
            p.terminate(); p.kill(); p.join(); p.close()

            

    if not loading_success.value:
        print("Could not get prices")
        # Functions for notificacion here
    else:
        print("Successfully executed")







"""

if __name__ == '__main__':
    max_time=5
    max_repeat=5
    manager=multiprocessing.Manager()
    loading_success=manager.Value('loading_success',False)

    p = multiprocessing.Process(target=get_5d_prices_yfinance, args=(loading_success,'loading_success'))
    p.start()
    p.join(max_time)

    tries=0
    while loading_success.value==False and tries<max_repeat:
        tries+=1
        if p.is_alive():
            print(p.is_alive())

            print (f"running... let's kill it... {loading_success.value}")

            # Terminate - may not work if process is stuck for good
            p.terminate()
            # OR Kill - will work for sure, no chance for process to finish nicely however
            p.kill()
            p.join()
            p.close()

            if loading_success.value==False:
                p = multiprocessing.Process(target=get_5d_prices_yfinance, args=(loading_success,'loading_success'))

                p.start()
                p.join(max_time)





    p.terminate()
    p.kill()
    p.join()
    p.close()
    print("Terminated")
    print (f"Done:  {loading_success.value}")

"""


