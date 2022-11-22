import pandas as pd
import traceback

#====================logger=========================
import os
from logging.handlers import TimedRotatingFileHandler
import logging
from datetime import datetime
import traceback



if not os.path.exists('logFile'):
    os.makedirs('logFile')
nowDate = datetime.now()
filename = str("./logFile./" + nowDate.strftime("%Y-%m-%d_%H-%M") + "1.txt")
logger = logging.getLogger(__name__)

fileMaxByte = 10.24 * 1024 * 100
fileHandler = logging.handlers.TimedRotatingFileHandler(filename='./logFile/main.log', when='midnight', interval=1,
                                                        backupCount=10)

logger.addHandler(fileHandler)
fileHandler.suffix = "%Y-%m-%d_%H-%M1.log"

formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
fileHandler.setFormatter(formatter)

streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

logger.setLevel(level=10)
#====================logger=========================



# -----------------------------------------------------------------------------
# - Name : envelope
# - Desc : 엔벨로프 조회
# - Input
#   1) candle_data : 캔들 정보
#   2) 기간
#   3) percent
# - Output
#   1) 엔벨로프 하방 탈출 여부
# -----------------------------------------------------------------------------
def get_envelope(candle_datas, line, diff):
    try:

        # 엔벨로프 데이터 리턴용

        val1 = int(line)
        val2 = float(diff)

        df = pd.DataFrame(candle_datas)

        df2 = {}
        df2['ma20'] = df.rolling(window=val1).mean()  # 20일 이동평균

        val = float(df2['ma20'].iloc[-2]) - ((float(df2['ma20'].iloc[-2]) * val2) / 100)

        if (val > float(df.iloc[-2])) & (float(df.iloc[-2]) < float(df.iloc[-1])):
            return 'ok'
        else:
            return 'no'

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())

# -----------------------------------------------------------------------------
# - Name : Bollinger
# - Desc : 볼린저밴드 조회
# - Input
#   1) candle_data : 캔들 정보
#   2) 이동평균
#   3) 승수
# - Output
#   1) 볼린저밴드 하방 탈출 여부
# -----------------------------------------------------------------------------
def get_Bollinger(candle_datas, line, diff):
    try:
        # 볼린저밴드 데이터 리턴용

        val1 = int(line)
        val2 = int(diff)

        df = pd.DataFrame(candle_datas)
        df2 = {}
        df2['ma20'] = df.rolling(window=val1).mean()  # 20일 이동평균
        df2['stddev'] = df.rolling(window=val1).std()  # 20일 이동표준편차
        # df['upper'] = df['ma20'] + val2 * df['stddev']  # 상단밴드
        df2['lower'] = df2['ma20'] - val2 * df2['stddev']  # 하단밴드
        # df = df[19:]  # 20일 이동평균을 구했기 때문에 20번째 행부터 값이 들어가 있음

        if float(df2['lower'].iloc[-2]) > float(df.iloc[-2]):
            return 'ok'
        else:
            return 'no'

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())



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

        delta = df.diff()
        gains, declines = delta.copy(), delta.copy()
        gains[gains < 0] = 0
        declines[declines > 0] = 0
        _gain = gains.ewm(com=(period - 1), min_periods=period).mean()
        _loss = declines.abs().ewm(com=(period - 1), min_periods=period).mean()
        RS = _gain / _loss
        rsi = pd.DataFrame(100 - (100 / (1 + RS)))

        if (float(rsi.iloc[-2]) <= int(min)) & (float(rsi.iloc[-2]) <= float(rsi.iloc[-1])):
            return 'ok'
        else:
            return 'no'

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())

# -----------------------------------------------------------------------------
# - Name : get_line
# - Desc : 이동평균선 조회
# - Input
#   1) candle_data : 캔들 정보
# - Output
#   1) 이평선 유지 유무 값, ex)2봉 유지면 이전봉과 현재봉 비교
# -----------------------------------------------------------------------------
def get_line(candle_datas, stand, use):
    try:
        # logger.debug("%s %s", stand, use)

        stand = int(stand)
        use = int(use)

        df = pd.DataFrame(candle_datas)

        line_period = df.rolling(window=stand).mean()

        count = int(use) * -1
        break_flag = False
        for i in range(count, -1):
            if not float(line_period.iloc[i]) <= float(line_period.iloc[i + 1]):
                break_flag = True
                break

        if break_flag == False:
            return 'ok'
        else:
            return 'fail'

    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())

# -----------------------------------------------------------------------------
# - Name : get_cci
# - Desc : CCI 조회
# - Input
#   1) candle_data : 캔들 정보
#   2) loop_cnt : 조회 건수
# - Output
#   1) CCI 값
# -----------------------------------------------------------------------------
def get_cci(candle_data, len):
    try:
        len = int(len)

        df = pd.DataFrame(candle_data)

        # 계산식 : (Typical Price - Simple Moving Average) / (0.015 * Mean absolute Deviation)
        df['TP'] = (df['high'] + df['low'] + df['close']) / 3
        df['SMA'] = df['TP'].rolling(window=len).mean()
        df['MAD'] = df['TP'].rolling(window=len).apply(lambda x: pd.Series(x).mad())
        df['CCI'] = (df['TP'] - df['SMA']) / (0.015 * df['MAD'])

        # logger.debug("%s %s", df['CCI'][-3], df['CCI'][-2])
        # 개수만큼 조립
        if ((df['CCI'][-5] < -200) & (df['CCI'][-4] < -150) & (df['CCI'][-3] < -130) & (df['CCI'][-2] >= -130)):
            # logger.debug("1. %s %s %s", df['CCI'][-3], df['CCI'][-2], g1)
            return 'ok'


        return 'fail'
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())