import multiprocessing as mp
import pyupbit

from time import sleep
if __name__ == "__main__":
    queue = mp.Queue()

    tickers = pyupbit.get_tickers(fiat='KRW')

    proc = mp.Process(
        target=pyupbit.WebSocketClient,
        args=('ticker', tickers, queue),
        daemon=True
    )
    proc.start()

    while True:
        data = queue.get()
        print(data)
        sleep(3)