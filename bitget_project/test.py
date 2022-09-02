import ccxt

binance = ccxt.bitget()
markets = binance.fetch_tickers()


for i in markets.keys():
    #print(i)
    pass


ticker = binance.fetch_ticker('BTC/USDT')

for i,j in ticker.items():
    print(i,j)