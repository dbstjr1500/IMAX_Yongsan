import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
import telegram
import json

#########################################################
# 텔레그램 봇 토큰 
my_token = '1136456443:AAHnhXqpT-NqUZiK909_5017pah7wJ6LQ04'
bot = telegram.Bot(token = my_token)
#########################################################

########################################################
# 업비트 API 키
access_key = 'LALQz8Jetu9dDy0jfkCzWha5KMQYekN9xd67iYE7'
secret_key = '2xV8lJFw8xTUTqLGqb7r0BE6iZpCYbO4IAwAxxxq'
server_url = 'https://api.upbit.com'
########################################################

#########################################################
def getTradePrice(market):
	# 코인 현재 시장가 import
    url = server_url + "/v1/candles/minutes/1"

    querystring = {"market": market, "count": "1"}

    response = requests.request("GET", url, params=querystring)
    return response.json()[0]['trade_price']


def order_info(uuid):
	query = {
    'uuid': uuid,
	}
	query_string = urlencode(query).encode()

	m = hashlib.sha512()
	m.update(query_string)
	query_hash = m.hexdigest()

	payload = {
	    'access_key': access_key,
	    'nonce': uuid,
	    'query_hash': query_hash,
	    'query_hash_alg': 'SHA512',
	}

	jwt_token = jwt.encode(payload, secret_key).decode('utf-8')
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	res = requests.get(server_url + "/v1/order", params=query, headers=headers)

	return res.json()['trades'][0]['volume'], res.json()['price'], res.json()['trades'][0]['funds']


def buy_price(market, price) :
	'''
	시장가 매수
	market : 매수하고자 하는 코인 이름 (KRW-BTC 등)
	price : 매수하고자 하는 금액
	주문고유id, 체결평균가, 체결된 양 return
	'''
	query = {
    'market': market,
    'side': 'bid',
    'price': price,
    'ord_type': 'price',
	}
	query_string = urlencode(query).encode()

	m = hashlib.sha512()	
	m.update(query_string)
	query_hash = m.hexdigest()

	payload = {
	    'access_key': access_key,
	    'nonce': str(uuid.uuid4()),
	    'query_hash': query_hash,
	    'query_hash_alg': 'SHA512',
	}

	jwt_token = jwt.encode(payload, secret_key).decode('utf-8')
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	res = requests.post(server_url + "/v1/orders", params=query, headers=headers)
	print(res.json()['uuid'])

	print('Checking order info......')
	time.sleep(0.5)
	volume, trade_price, trash = order_info(res.json()['uuid'])

	return res.json()['uuid'], volume, trade_price


def sell_market(market, volume):
	'''
	시장가 매도 
	market : 매도하고자 하는 코인 이름 (KRW-BTC 등)
	volume : 매도하고자 하는 코인 수량
	주문고유id, 체결평균가, 체결된 양 return
	'''
	query = {
    'market': market,
    'side': 'ask',
    'volume': volume,
    'ord_type': 'market',
	}
	query_string = urlencode(query).encode()

	m = hashlib.sha512()	
	m.update(query_string)
	query_hash = m.hexdigest()

	payload = {
	    'access_key': access_key,
	    'nonce': str(uuid.uuid4()),
	    'query_hash': query_hash,
	    'query_hash_alg': 'SHA512',
	}

	jwt_token = jwt.encode(payload, secret_key).decode('utf-8')
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	res = requests.post(server_url + "/v1/orders", params=query, headers=headers)
	print(res.json()['uuid'])

	print('Checking order info......')
	time.sleep(0.5)
	volume, trash, trade_price = order_info(res.json()['uuid'])

	return res.json()['uuid'], volume, trade_price


def account_info():
	payload = {
	    'access_key': access_key,
	    'nonce': str(uuid.uuid4()),
	}

	jwt_token = jwt.encode(payload, secret_key).decode('utf-8')
	authorize_token = 'Bearer {}'.format(jwt_token)
	headers = {"Authorization": authorize_token}

	res = requests.get(server_url + "/v1/accounts", headers=headers)
	print(res.json())
	return res.json()


def get_BTC_balance():
	temp = account_info()
	for i in temp:
		if i['currency'] == 'BTC':
			return i['balance']


def get_KRW_balance():
	temp = account_info()
	for i in temp:
		if i['currency'] == 'KRW':
			return i['balance']


def rsi(ohlc: pd.DataFrame, period: int = 14) -> pd.Series:
    """See source https://github.com/peerchemist/finta
    and fix https://www.tradingview.com/wiki/Talk:Relative_Strength_Index_(RSI)
    Relative Strength Index (RSI) is a momentum oscillator that measures the speed and change of price movements.
    RSI oscillates between zero and 100. Traditionally, and according to Wilder, RSI is considered overbought when above 70 and oversold when below 30.
    Signals can also be generated by looking for divergences, failure swings and centerline crossovers.
    RSI can also be used to identify the general trend."""

    delta = ohlc["close"].diff()

    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()

    RS = _gain / _loss
    return pd.Series(100 - (100 / (1 + RS)), name="RSI")


def get_Rsi(market):
	url = server_url + '/v1/candles/minutes/1'
	querystring = {"market":market,"count":"200"}
	req = requests.request("GET", url, params=querystring)
	data   = req.json()
	result = []

	for i, candle in enumerate(data):
	    result.append({
	        'time'                 : data[i]["candle_date_time_kst"], 
	        'open'                 : data[i]["opening_price"],
	        'high'                 : data[i]["high_price"],
	        'low'                  : data[i]["low_price"],
	        'close'                : data[i]["trade_price"],
	        'Volume'               : data[i]["candle_acc_trade_volume"],
	        "candleAccTradePrice"  : data[i]["candle_acc_trade_price"]
	    })
	coin_data = pd.DataFrame(result)
	coin_data = coin_data.sort_values('time')

	temp = []
	for i in range(0,200):
		temp.append(i)

	coin_data['for_index'] = temp
	coin_data = coin_data.set_index('for_index')
	a = rsi(coin_data,14)
	coin_data['rsi'] = a
	#coin_data.to_csv(f'KRW_BTC_KRW_1min.csv')

	return coin_data['rsi'][199]
#########################################################

'''
get_Rsi를 실행해 정보 200개 불러와서 rsi 계산
이후 getTradePrice를 이용해 실시간 분봉 데이터 확인
매 분이 지날때마다 데이터 업데이트 후 다음 열로 이동
rsi 30이하일시 매수 rsi 70 이상일시 매도
'''


buy_status = False
balance_BTC = get_BTC_balance()
balance_KRW = get_KRW_balance()
if balance_BTC != None:
	buy_status = True
print(buy_status)
print(balance_BTC)
print(balance_KRW)
bot.sendMessage(chat_id = -1001320421761, text = "업비트 매매봇 작동시작!!") 

try:
	while True:
		current_RSI = get_Rsi('KRW-BTC')
		print(current_RSI)
		if current_RSI<30 and buy_status == False:
			uuid_order, executed_volume, avg_price = buy_price('KRW-BTC', 10000)
			buy_status = True 
			balance_BTC = get_BTC_balance()
			balance_KRW = get_KRW_balance()
			print("BTC %s개 매수! (평균가: %s, UUID: %s)" % (executed_volume, avg_price, uuid_order))
			bot.sendMessage(chat_id = -1001320421761, text = "BTC %s개 매수! (평균가: %s, UUID: %s)" % (executed_volume, avg_price, uuid_order))

			'''
			uuid, avg_price, executed_volume = buy_price('KRW-BTC', 10000)
			buy_status = True
			print(uuid, avg_price, executed_volume)
			balance_BTC = get_BTC_balance()
			balance_KRW = get_KRW_balance()
			print("BTC %f개 매수! (평균가: %f, UUID: %s)" % (executed_volume, avg_price, uuid))
			bot.sendMessage(chat_id = -1001299873599, text = "BTC %f개 매수! (평균가: %f, UUID: %s)" % (executed_volume, avg_price, uuid))
			'''

		elif current_RSI>70 and buy_status == True:
			uuid_order, executed_volume, avg_price = sell_market('KRW-BTC', balance_BTC)
			buy_status = False 
			balance_BTC = get_BTC_balance()
			balance_KRW = get_KRW_balance()
			print("BTC %s개 매도! (평균가: %s, UUID: %s)" % (executed_volume, avg_price, uuid_order))
			bot.sendMessage(chat_id = -1001320421761, text = "BTC %s개 매도! (평균가: %s, UUID: %s)" % (executed_volume, avg_price, uuid_order))

			'''
			uuid, avg_price, executed_volume = sell_market('KRW-BTC', balance_BTC)
			buy_status = False
			balance_BTC = get_BTC_balance()
			balance_KRW = get_KRW_balance()
			print("BTC %f개 매수! (평균가: %f, UUID: %s)" % (executed_volume, avg_price, uuid))
			bot.sendMessage(chat_id = -1001299873599, text = "BTC %f개 매수! (평균가: %f, UUID: %s)" % (executed_volume, avg_price, uuid))
			'''
		time.sleep(0.1)

except:
	print('ERROR')
	bot.sendMessage(chat_id = -1001320421761, text = "업비트 매매봇 고장!!") 





'''
i=0
while True:
	print(getTradePrice("KRW-BTC"))
	time.sleep(0.07)
'''








'''
url = "https://api.upbit.com/v1/candles/minutes/1"

querystring = {"market":"KRW-BTC","count":"200"}

response = requests.request("GET", url, params=querystring)

for i in range(0,200):
	print(response.json()[i]['trade_price'])
'''


