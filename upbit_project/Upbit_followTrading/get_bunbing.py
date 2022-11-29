import pickle
import time

import pyupbit
import requests

def get_bunbong(coin = 'KRW-BTC',time = '', count = 200 ,min = 1):
    #time 형식 : '2022-11-26 15:00:00'

    if time != '':
        time = time.replace(' ','%20')
        time = time.replace(':','%3A')
        time = '&to=' + time
    url = f"https://api.upbit.com/v1/candles/minutes/{min}?market={coin}{time}&count={count}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    ret = response.json()
    tmp = []
    for i in response.json():
        tmp.append(i['trade_price'])

    last_time = ret[-1]['candle_date_time_utc'].replace('T', ' ')

    #print('start time : ', ret[0]['candle_date_time_kst'])
    #print('end time   : ', ret[-1]['candle_date_time_kst'])
    return last_time, tmp


def get_10k_bunbong(coin = 'KRW-BTC', count = 250):

    last_time, data_200 = get_bunbong(coin = coin)
    tmp = []

    for i in range(count):
        tmp += data_200
        last_time, data_200 = get_bunbong(coin=coin, time = last_time)
        if len(data_200) != 200:
            print('데이터 200개 오류 !')
        time.sleep(0.11)
        #print(coin, i ,"/", count)
        #print(len(tmp))

    return tmp

#tickers = pyupbit.get_tickers(fiat='KRW')
tickers = ['KRW-BTC']
data_dic = {}

def get_all_tickers_data():
    global data_dic
    error = []
    idx = 0
    count = 250
    for i in tickers:
        try:
            idx += 1
            print(i, idx ,"/", len(tickers))
            #print(i, '작업 시작')
            data_dic[i] = get_10k_bunbong(coin = i,count = count)
            #print(i, '작업 끝')
            #print(i,'정보')
            #print('길이', len(data_dic[i]))

        except:
            print('에러 발생', i)
            error.append(i)

    #print(data_dic)
    print('코인 갯수', len(data_dic))

    for i in data_dic:
        print(i)
        print(len(data_dic[i]))
        if len(data_dic[i]) != count * 200:
            error.append(i)

    error = set(error)
    error = list(error)
    print('error 리스트 : ', error)




get_all_tickers_data()

with open('./DATA/BTC_coin_data.pickle', 'wb') as f:
    pickle.dump(data_dic, f)


with open('./DATA/all_coin_data.pickle', 'rb') as f:
    trade_list = pickle.load(f)

for i in trade_list:
    print(i,len(trade_list[i]))
    for j in range(15):
        print(trade_list[i][j])
    break