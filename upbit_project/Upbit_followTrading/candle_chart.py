
import pyupbit
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mpdates

df = pyupbit.get_ohlcv('KRW-BTC', 'minute1', 200)
"""
styles = ['binance',
          'blueskies',
          'brasil',
          'charles',
          'checkers',
          'classic',
          'default',
          'ibd',
          'kenan',
          'mike',
          'nightclouds',
          'sas',
          'starsandstripes',
          'yahoo']

fig = mpf.figure(figsize=(50, 20))
for i in range(len(styles)):
    ax = fig.add_subplot(5, 3, i + 1, style=styles[i])
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    mpf.plot(df, type='candle', ax=ax, axtitle=styles[i])
    print(styles[i])

mpf.show()

mpf.plot(df, type='candle', style='charles',
         title='KRW-BTC',
         ylabel='stock price',
         ylabel_lower='volume',
         volume=True,
         mav=(5, 10, 60)
         )"""

def plot_coin():
    name = '005930.KS'
    df = pyupbit.get_ohlcv('KRW-BTC', "minute5", 200)
    df_show = df.copy()
    df_show['Date'] = df_show.index
    #df_show.info()
    df_show['Date'] = df_show['Date'].map(mpdates.date2num)
    #df_show.info()
    df_show = df_show[['Date', 'open', 'high', 'low','close']]

    fig, ax = plt.subplots()
    candlestick_ohlc(ax, df_show.values, width=0.0001, colordown='b', colorup='r', alpha=1)
    ax.grid(True)

    date_format = mpdates.DateFormatter('%Y/%m/%d %H:%M')

    years = mpdates.YearLocator()
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(date_format)

    fig.tight_layout()


import finplot as fplt
def fplt_plot():
    ax = fplt.create_plot(init_zoom_periods=100)  # pygtgraph.graphicsItems.PlotItem
    #axo = ax.overlay()  # pygtgraph.graphicsItems.PlotItem
    #axs = [ax]  # finplot requres this property

    #self.gridLayout.addWidget(ax.vb.win, 0, 0)  # ax.vb     (finplot.FinViewBox)

    fplt.candle_bull_color = "#FF0000"
    fplt.candle_bull_body_color = "#FF0000"
    fplt.candle_bear_color = "#0000FF"

    df = pyupbit.get_ohlcv('KRW-BTC', "minute5", 200)
    fplt.candlestick_ochl(df[['open', 'close', 'high', 'low']])
    fplt.show()




fplt_plot()