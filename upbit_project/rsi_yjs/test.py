import pyupbit
import time
#
# #현재가 가져오기
# a = pyupbit.get_current_price('KRW-BTC')
# print(a)
#
# #ohlcv 가져오기 - 200개까지 제한적으로 가져올 수 있음
# #두번째 파라미터 : mintue5, 10, 15, 30, 60, 120, 240, day, week
# b = pyupbit.get_ohlcv('KRW-BTC', 'mintue5', 200)
#
# print(b)
# print(b['close'][-1]) #마지막 데이터가 최신
#
#
# #종목리스트 가져오기
c = pyupbit.get_tickers(fiat='KRW')
print(c)
print(len(c))

# #전 종목 가격 확인
# d = pyupbit.get_current_price(c)
# print(d)
#

# acess_key = 'ufHfT9rQjQqCpVFjXn7T8xvAsadFf1ix6ANIBtwG'
# scret_key = 'SaVPk0cWmXx1TSRxjEyxkrG5xxLRx1MPcIcK8oIN'
# #
# #로그인
# main_upbit = pyupbit.Upbit(acess_key, scret_key)
#
# #time.sleep(1)
# #로그인 확인 - 잔액 확인하는 방법 유일
# #단일 종목 잔고 확인
# balance = main_upbit.get_balance(ticker="KRW")
# #balance =main_upbit.get_amount('ALL')
# print(balance)

#전체 확인
# balances = main_upbit.get_balances()
# print(balances)
#
# for i in range(len(balances)):
#     if balances[i]['currency'] == 'KRW':
#         print('my cash : '.format(int(float(balances[i]['balance']))))
#     else:
#         print('코인별 잔액')

#매수 파라미터 - ([코인명], [얼만큼 살지])
#main_upbit.buy_market_order('KRW-BTC', '10000')

