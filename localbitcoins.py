import hmac
import time
import hashlib
import json
import requests
import random
import urllib.parse

class Localbitcoins:
    def __init__(self, hmac_key, hmac_secret):
        self.HMAC_KEY = hmac_key
        self.HMAC_SECRET = hmac_secret

    def get_api_headers(self, endpoint, parameters = {}):
        nonce = int(time.time())
        params_urlencoded = urllib.parse.urlencode(parameters)
        message = str(nonce) + self.HMAC_KEY + endpoint + params_urlencoded
        message_bytes = message.encode('utf-8')
        signature = hmac.new(self.HMAC_SECRET.encode('utf-8'), msg=message_bytes, digestmod=hashlib.sha256).hexdigest().upper()
        return {'Apiauth-Key': self.HMAC_KEY, 'Apiauth-Nonce': str(nonce), 'Apiauth-Signature': signature}

    def get_url(self, endpoint):
        return 'https://localbitcoins.com' + endpoint

    def update_price(self, ad_id, new_price):
        endpoint = '/api/ad-equation/{:d}/'.format(ad_id)
        parameters = {'price_equation': float('%.2f' % new_price)}
        response = requests.post(self.get_url(endpoint), data=parameters, headers=self.get_api_headers(endpoint, parameters))
        return response.json()

    def get_selling_offers(self, currency):
        endpoint = '/buy-bitcoins-online/{:s}/.json'.format(currency)
        response = requests.get(self.get_url(endpoint))
        return response.json()

    def get_ads(self):
        endpoint ='/api/ads/'
        response = requests.get(self.get_url(endpoint), headers=self.get_api_headers(endpoint))
        return response.json()

    def get_notifications(self):
        endpoint = '/api/notifications/'
        response = requests.get(self.get_url(endpoint), headers=self.get_api_headers(endpoint))
        return response.json()
