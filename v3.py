from config import HMAC_KEY, HMAC_SECRET, TARGET_PRICE, MIN_PRICE
from localbitcoins import Localbitcoins
from subprocess import DEVNULL
from datetime import datetime
import subprocess
import colors
import pytz
import sys

api = Localbitcoins(HMAC_KEY, HMAC_SECRET)

def get_my_ad():
    json = api.get_ads()
    return {
        'id': json['data']['ad_list'][0]['data']['ad_id'],
        'price': float(json['data']['ad_list'][0]['data']['temp_price'])}


def get_market_ads():
    json = api.get_selling_offers('BRL')
    for ad in json['data']['ad_list']:
        if ad['data']['online_provider'] in ['NATIONAL_BANK', 'SPECIFIC_BANK']:
            yield {
                'id': ad['data']['ad_id'],
                'price': float(ad['data']['temp_price']),
                'user': ad['data']['profile']['username'],
                'min_amount': ad['data']['min_amount']}


def print_ads(my_ad, market_ads):
    my_ad_listed = False
    for i in range(0, len(market_ads)):
        ad = market_ads[i]
        min_amount = 0 if ad['min_amount'] == None else ad['min_amount']
        print('{:2d} {:5} {:30} {:,.2f} BRL {:12} Min: {:>5}'.format(i, '', ad['user'], ad['price'], '', min_amount))
        if my_ad['id'] == ad['id']:
            my_ad_listed = True
        if i >= 5 and my_ad_listed:
            break;

def print_notifications(notifications):
    print('\n{:s}\n'.format('-' * 80))
    for notification in notifications['data'][:3]:
        created_at = notification['created_at'][:22] + notification['created_at'][23:]
        utc = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S%z')
        sao_paulo = pytz.timezone('America/Sao_Paulo')
        timestamp = utc.astimezone(sao_paulo).strftime('%Y-%m-%d %H:%M:%S')
        line = '[{:s}] {:s}\n'
        if not notification['read']:
            line = colors.RED + line + colors.RESET
        print(line.format(timestamp, notification['msg']))
    print('{:s}\n'.format('-' * 80))


def alert_new_notification(notifications):
    unread = list(filter(lambda x: not x['read'], notifications['data']))
    if len(unread) > 0:
        subprocess.run(['mpg123', '-q', 'chaching.mp3'], stdout=DEVNULL)


def get_current_position(my_ad, market_ads):
    ids = list(map(lambda x: x['id'], market_ads))
    return ids.index(my_ad['id'])


def update_price(id, new_price):
    response = api.update_price(id, new_price)
    print(response['data'])


def print_change_position(my_ad, market_ads, new):
    position = get_current_position(my_ad, market_ads)
    print('- Moving from #{:d} to #{:d}'.format(position, new))

def hold_position(my_ad, market_ads, n):
    if market_ads[n]['price'] < MIN_PRICE:
        if my_ad['price'] != MIN_PRICE:
            print('- Setting min price')
            update_price(my_ad['id'], MIN_PRICE)
        return True

    elif n == 0:
        if my_ad['id'] != market_ads[0]['id']:
            new_price = market_ads[0]['price'] - random.random()
            print_change_position(my_ad, market_ads, 0)
            update_price(my_ad['id'], new_price)
        elif market_ads[1]['price'] - 10 > my_ad['price']:
            new_price = market_ads[1]['price'] - random.random()
            print('- Increasing price, keeping position #0')
            update_price(my_ad['id'], new_price)
        return True

    elif market_ads[n]['price'] < TARGET_PRICE:
        if my_ad['id'] != market_ads[n]['id']:
            new_price = 1e9
            ids = list(map(lambda x: x['id'], market_ads))
            if my_ad['id'] in ids[:n]:
                new_price = (market_ads[n]['price'] + market_ads[n+1]['price']) / 2
                if new_price > TARGET_PRICE:
                    new_price = (market_ads[n]['price'] + TARGET_PRICE) / 2
            else:
                new_price = (market_ads[n]['price'] + market_ads[n-1]['price']) / 2
            print_change_position(my_ad, market_ads, n)
            update_price(my_ad['id'], new_price)
        return True

    else:
        return False


def main():
    my_ad = get_my_ad()
    market_ads = list(get_market_ads())
    print_ads(my_ad, market_ads)

    notifications = api.get_notifications()
    print_notifications(notifications)
    if not '-silent' in sys.argv:
        alert_new_notification(notifications)

    position = 4
    while not hold_position(my_ad, market_ads, position): position -= 1

if __name__ == "__main__": main()
