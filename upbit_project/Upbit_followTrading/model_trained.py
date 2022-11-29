
import matplotlib.pyplot as plt
#from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
from keras.models import load_model
import pyupbit
from sklearn.preprocessing import MinMaxScaler
sc = MinMaxScaler(feature_range=(0, 1))

def init_coin_list():
    print("init_coin_dic start")
    global coin_list
    df = pyupbit.get_ohlcv('KRW-BTC', 'minute5', 200)
    return df['close'].to_list()


coin_list = init_coin_list()

print(coin_list)

X = range(len(coin_list))
y = coin_list
#plt.plot(X, y)
#plt.show()

all_data = coin_list

def ts_train_test_normalize(all_data, time_steps, for_periods):
    """
    input:
        data: dataframe with dates and price data
    output:
        X_train, y_train: data from 2013/1/1-2018/12/31
        X_test : data from 2019-
        sc :     insantiated MinMaxScaler object fit to the training data
    """
    from sklearn.preprocessing import MinMaxScaler
    sc = MinMaxScaler(feature_range=(0, 1))

    inputs = pd.concat((all_data["Adj Close"][:'2018'], all_data["Adj Close"]['2019':]), axis=0).values
    inputs = inputs[len(inputs) - len(30) - time_steps:]
    inputs = inputs.reshape(-1, 1)
    inputs = sc.transform(inputs)
    # Preparing X_test
    X_test = []
    for i in range(time_steps, 30 + time_steps - for_periods):
        X_test.append(inputs[i - time_steps:i, 0])

    X_test = np.array(X_test)
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

    return X_test, sc

#X_test, sc = ts_train_test_normalize(all_data, 5,2)
inputs = coin_list[:5]
for i in range(5):
    inputs[i] = int(inputs[i])
print(inputs)
inputs = pd.Series( inputs)
print(type(inputs))
inputs = inputs.values
print((inputs))
inputs = inputs.reshape(-1,1)

inputs = sc.fit_transform(inputs)

X_test = []

X_test.append(inputs)
X_test = np.array(X_test)
print(X_test.shape)
X_test = np.reshape(X_test, (1, 5, 1))

my_LSTM_model = load_model('lstm_model.h5')
LSTM_prediction = my_LSTM_model.predict(X_test)
print("X_test : ", X_test)
print('LSTM_prediction : ', LSTM_prediction)
#LSTM_prediction = sc.inverse_transform(LSTM_prediction)