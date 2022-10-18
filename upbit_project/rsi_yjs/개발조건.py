"""
#
1.전종목

# 기준봉 : 쓰레드로 설정 봉마다 코인 가격 획득
#현재시간 가져와서, 체크
1시간이면, min == 0 일때,
b = pyupbit.get_ohlcv('KRW-BTC', 'mintue60', 200)

4시간이면 h % 4 == 0 일때,
b = pyupbit.get_ohlcv('KRW-BTC', 'mintue240', 200)

일봉이면, h == 9 일때,
b = pyupbit.get_ohlcv('KRW-BTC', 'day', 200)

2. 1시간봉, 4시간봉, 일봉

□ RSI 값은 정확하지 않다.
3.RSI = (30) 미만에서 최저점 찾고 그 값보다 올랐을 때, 1차

4.스토캐스틱 RSI -> (20) 미만이면서  K 선이 D 선보다 위에 있을때, 2차

5.1,2차 조건 부합 시 매수

6.텔레그램 메시지 전송 -txt로 받아오기

7.매수 기능

8.금액설정 기능

9.실시간 로그

10.종목개수제한
"""



# -----------------------------------------------------------------------------
# - Name : rsi
# - Desc : rsi 조회
# - Input
#   1) candle_data : 캔들 정보
#   2) 기간
#   3) 하방 라인 값
# - Output
#   1) rsi -2는 30미만이면서 -1 값이 클경우
# -----------------------------------------------------------------------------
def get_rsi(candle_datas, period, min):
    try:
        df = pd.DataFrame(candle_datas)
        ohlc = df
        delta = ohlc["close"].diff()
        gains, declines = delta.copy(), delta.copy()
        gains[gains < 0] = 0
        declines[declines > 0] = 0
        _gain = gains.ewm(com=(period - 1), min_periods=period).mean()
        _loss = declines.abs().ewm(com=(period - 1), min_periods=period).mean()
        RS = _gain / _loss
        rsi = pd.Series(100 - (100 / (1 + RS)), name="RSI")

        if ((rsi.iloc[-2]) <= int(min)) & ((rsi.iloc[-2]) <= (rsi.iloc[-1])):
            return 'ok'
        else:
            return 'no'

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("error. %s", e)
        logger.debug(traceback.format_exc())


#스토캐스틱 구하는 공식
def stock_func(data):
    try:
        df = pd.DataFrame(data)

        period = 5
        smoothK = 10
        smoothD = 5

        # n일중 최고가
        ndays_high = df.high.rolling(window=period, min_periods=1).max()
        # n일중 최저가
        ndays_low = df.low.rolling(window=period, min_periods=1).min()
        # Fast%K 계산
        fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
        # Fast%D (=Slow%K)계산
        slow_k = fast_k.ewm(span=smoothK).mean()
        # Slow%D 계산
        slow_d = slow_k.ewm(span=smoothD).mean()
        # dataframe 에 컬럼 추가
        df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d)

        if slow_k[-1] > slow_d[-1]:
            logger.debug("slow k = {}, slow d= {}".format(slow_k[-1], slow_d[-1]))

            return True

    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())