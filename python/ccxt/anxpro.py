# -*- coding: utf-8 -*-

from ccxt.base.exchange import Exchange
import base64
import hashlib
from ccxt.base.errors import ExchangeError


class anxpro (Exchange):

    def describe(self):
        return self.deep_extend(super(anxpro, self).describe(), {
            'id': 'anxpro',
            'name': 'ANXPro',
            'countries': ['JP', 'SG', 'HK', 'NZ'],
            'version': '2',
            'rateLimit': 1500,
            'hasCORS': False,
            'hasFetchTrades': False,
            'hasWithdraw': True,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27765983-fd8595da-5ec9-11e7-82e3-adb3ab8c2612.jpg',
                'api': 'https://anxpro.com/api',
                'www': 'https://anxpro.com',
                'doc': [
                    'http://docs.anxv2.apiary.io',
                    'https://anxpro.com/pages/api',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        '{currency_pair}/money/ticker',
                        '{currency_pair}/money/depth/full',
                        '{currency_pair}/money/trade/fetch',  # disabled by ANXPro
                    ],
                },
                'private': {
                    'post': [
                        '{currency_pair}/money/order/add',
                        '{currency_pair}/money/order/cancel',
                        '{currency_pair}/money/order/quote',
                        '{currency_pair}/money/order/result',
                        '{currency_pair}/money/orders',
                        'money/{currency}/address',
                        'money/{currency}/send_simple',
                        'money/info',
                        'money/trade/list',
                        'money/wallet/history',
                    ],
                },
            },
            'markets': {
                'BTC/USD': {'id': 'BTCUSD', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD', 'multiplier': 100000},
                'BTC/HKD': {'id': 'BTCHKD', 'symbol': 'BTC/HKD', 'base': 'BTC', 'quote': 'HKD', 'multiplier': 100000},
                'BTC/EUR': {'id': 'BTCEUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR', 'multiplier': 100000},
                'BTC/CAD': {'id': 'BTCCAD', 'symbol': 'BTC/CAD', 'base': 'BTC', 'quote': 'CAD', 'multiplier': 100000},
                'BTC/AUD': {'id': 'BTCAUD', 'symbol': 'BTC/AUD', 'base': 'BTC', 'quote': 'AUD', 'multiplier': 100000},
                'BTC/SGD': {'id': 'BTCSGD', 'symbol': 'BTC/SGD', 'base': 'BTC', 'quote': 'SGD', 'multiplier': 100000},
                'BTC/JPY': {'id': 'BTCJPY', 'symbol': 'BTC/JPY', 'base': 'BTC', 'quote': 'JPY', 'multiplier': 100000},
                'BTC/GBP': {'id': 'BTCGBP', 'symbol': 'BTC/GBP', 'base': 'BTC', 'quote': 'GBP', 'multiplier': 100000},
                'BTC/NZD': {'id': 'BTCNZD', 'symbol': 'BTC/NZD', 'base': 'BTC', 'quote': 'NZD', 'multiplier': 100000},
                'LTC/BTC': {'id': 'LTCBTC', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC', 'multiplier': 100000},
                'STR/BTC': {'id': 'STRBTC', 'symbol': 'STR/BTC', 'base': 'STR', 'quote': 'BTC', 'multiplier': 100000000},
                'XRP/BTC': {'id': 'XRPBTC', 'symbol': 'XRP/BTC', 'base': 'XRP', 'quote': 'BTC', 'multiplier': 100000000},
                'DOGE/BTC': {'id': 'DOGEBTC', 'symbol': 'DOGE/BTC', 'base': 'DOGE', 'quote': 'BTC', 'multiplier': 100000000},
            },
            'fees': {
                'trading': {
                    'maker': 0.3 / 100,
                    'taker': 0.6 / 100,
                },
            },
        })

    def fetch_balance(self, params={}):
        response = self.privatePostMoneyInfo()
        balance = response['data']
        currencies = list(balance['Wallets'].keys())
        result = {'info': balance}
        for c in range(0, len(currencies)):
            currency = currencies[c]
            account = self.account()
            if currency in balance['Wallets']:
                wallet = balance['Wallets'][currency]
                account['free'] = float(wallet['Available_Balance']['value'])
                account['total'] = float(wallet['Balance']['value'])
                account['used'] = account['total'] - account['free']
            result[currency] = account
        return self.parse_balance(result)

    def fetch_order_book(self, symbol, params={}):
        response = self.publicGetCurrencyPairMoneyDepthFull(self.extend({
            'currency_pair': self.market_id(symbol),
        }, params))
        orderbook = response['data']
        t = int(orderbook['dataUpdateTime'])
        timestamp = int(t / 1000)
        return self.parse_order_book(orderbook, timestamp, 'bids', 'asks', 'price', 'amount')

    def fetch_ticker(self, symbol, params={}):
        response = self.publicGetCurrencyPairMoneyTicker(self.extend({
            'currency_pair': self.market_id(symbol),
        }, params))
        ticker = response['data']
        t = int(ticker['dataUpdateTime'])
        timestamp = int(t / 1000)
        bid = self.safe_float(ticker['buy'], 'value')
        ask = self.safe_float(ticker['sell'], 'value')
        vwap = float(ticker['vwap']['value'])
        baseVolume = float(ticker['vol']['value'])
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': float(ticker['high']['value']),
            'low': float(ticker['low']['value']),
            'bid': bid,
            'ask': ask,
            'vwap': vwap,
            'open': None,
            'close': None,
            'first': None,
            'last': float(ticker['last']['value']),
            'change': None,
            'percentage': None,
            'average': float(ticker['avg']['value']),
            'baseVolume': baseVolume,
            'quoteVolume': baseVolume * vwap,
            'info': ticker,
        }

    def fetch_trades(self, symbol, since=None, limit=None, params={}):
        raise ExchangeError(self.id + ' switched off the trades endpoint, see their docs at http://docs.anxv2.apiary.io/reference/market-data/currencypairmoneytradefetch-disabled')
        return self.publicGetCurrencyPairMoneyTradeFetch(self.extend({
            'currency_pair': self.market_id(symbol),
        }, params))

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        market = self.market(symbol)
        order = {
            'currency_pair': market['id'],
            'amount_int': int(amount * 100000000),  # 10^8
        }
        if type == 'limit':
            order['price_int'] = int(price * market['multiplier'])  # 10^5 or 10^8
        order['type'] = 'bid' if (side == 'buy') else 'ask'
        result = self.privatePostCurrencyPairMoneyOrderAdd(self.extend(order, params))
        return {
            'info': result,
            'id': result['data'],
        }

    def cancel_order(self, id, symbol=None, params={}):
        return self.privatePostCurrencyPairMoneyOrderCancel({'oid': id})

    def get_amount_multiplier(self, currency):
        if currency == 'BTC':
            return 100000000
        elif currency == 'LTC':
            return 100000000
        elif currency == 'STR':
            return 100000000
        elif currency == 'XRP':
            return 100000000
        elif currency == 'DOGE':
            return 100000000
        return 100

    def withdraw(self, currency, amount, address, params={}):
        self.load_markets()
        multiplier = self.get_amount_multiplier(currency)
        response = self.privatePostMoneyCurrencySendSimple(self.extend({
            'currency': currency,
            'amount_int': int(amount * multiplier),
            'address': address,
        }, params))
        return {
            'info': response,
            'id': response['data']['transactionId'],
        }

    def nonce(self):
        return self.milliseconds()

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        request = self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        url = self.urls['api'] + '/' + self.version + '/' + request
        if api == 'public':
            if query:
                url += '?' + self.urlencode(query)
        else:
            self.check_required_credentials()
            nonce = self.nonce()
            body = self.urlencode(self.extend({'nonce': nonce}, query))
            secret = base64.b64decode(self.secret)
            auth = request + "\0" + body
            signature = self.hmac(self.encode(auth), secret, hashlib.sha512, 'base64')
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Rest-Key': self.apiKey,
                'Rest-Sign': self.decode(signature),
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = self.fetch2(path, api, method, params, headers, body)
        if 'result' in response:
            if response['result'] == 'success':
                return response
        raise ExchangeError(self.id + ' ' + self.json(response))
