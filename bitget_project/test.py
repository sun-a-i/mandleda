import ccxt
import time
import datetime



with open('API.txt') as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

binance = ccxt.bitget(config={
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
})#로그인 객체관리, 전역? 클래스 내부 ?


#markets = binance.fetch_tickers()



def getdata():#tr과 같음
    ticker = binance.fetch_ticker('BTC/USDT')
    for i,j in ticker.items():
        print(i,j)

def getbalance(): #call jango와 같음
    balance = binance.fetch_balance()
    print(balance['BTC'])


def getdata_while(): #못가져왔을때 오류처리 ?
    symbol = "BTC/USDT"
    while True:
        btc = binance.fetch_ticker(symbol)
        now = datetime.datetime.now()
        print(now, btc['last'])
        time.sleep(1)

def run():
    getbalance()
    getdata()
    getdata_while()
run()

#현재가 update 스레드
#자동매매 스레드
#main ui 스레드
#로그인 서버 거쳐서 로그인 플래그 확인
#단위?? USDT = 1$?
#그럼 한화로 계산해서 ? 아니면 불로 거래 ?
#확장성을 고려해야 하는지 ?

