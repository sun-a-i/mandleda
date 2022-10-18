import pyupbit

#UI에서 받아올 값
RSI_Length = 14
RSI_lower_val = 30

stock_RSI_strong_peoriod = 14
SmoothK = 3
SmoothD = 3
stock_RSI_lower_val = 20

#param1 : coin, param2:기준봉(1시간, 4시간, 1일)
def Check_Condition(coin, bunbong):
    try:

        con_fir = False
        con_sec = False

        if str(bunbong).isdigit(): #60 or 240만 있음
            df = pyupbit.get_ohlcv(coin, interval="minutes" + str(bunbong), count=200)
        else:
            df = pyupbit.get_ohlcv(coin, interval="day", count=200)

        #RSI calc - 1차 조건
        delta = df['close'].diff(1)
        delta = delta.dropna()
        up = delta.copy()
        down = delta.copy()
        up[ up < 0 ] = 0
        down[ down > 0 ] = 0
        time_period = RSI_Length
        AVG_Gain = up.ewm(com=time_period-1, min_periods=time_period).mean()
        AVG_Loss = abs(down.ewm(com=time_period-1, min_periods=time_period).mean())
        RS = AVG_Gain / AVG_Loss
        RSI = 100.0 - (100.0/(1.0 + RS))
        df['RSI'] = RSI

        if df['RSI'][-1] < RSI_lower_val:
            if df['RSI'][-3] >= df['RSI'][-2]:
                if df['RSI'][-2] < df['RSI'][-1]:
                    # 1차 부합 시 로그 & 텔레그램
                    con_fir = True
                    txt = "1차부합, coin : {}, RSI[1봉전] : {}, RSI[종가] : {}".format(coin, df['RSI'][-2],df['RSI'][-1])
                    print(txt)
                    #send_tel(txt)


        #stoch_RSI - 2차 조건
        min_val  = df['RSI'].rolling(window=stock_RSI_strong_peoriod, center=False ).min()
        max_val = df['RSI'].rolling(window=stock_RSI_strong_peoriod, center=False).max()
        stoch = ( (df['RSI'] - min_val) / (max_val - min_val) ) * 100
        K = stoch.rolling(window=SmoothK, center=False).mean()
        D = K.rolling(window=SmoothD, center=False).mean()
        df['K'], df['D'] = K, D

        if df['K'][-1] < stock_RSI_lower_val and df['D'][-1] < stock_RSI_lower_val:
            if df['K'][-2] < df['D'][-2]:
                if df['K'][-1] >= df['D'][-1]:
                    # 2차 부합 시 로그 & 텔레그램
                    con_sec = True
                    txt = "매수포착 coin:{}, stock[K]:{}, stock[D]:{}".format(coin, df['K'][-1], df['D'][-1])
                    print(txt)
                    # send_tel(txt)


        #1,2차 부합 시
        if con_fir == True and con_sec == True:
            return True
        else:
            return False

    except Exception as e:
        print(e)

Check_Condition('KRW-BTC', 10)