#!/bin/python3
import json
import bs4
import argparse
import shutil
import csv
import requests
import pdb

import html5lib
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

root = "https://api.coingecko.com/api/v3"
currency = "usd"
csv_header = ["id", "symbol", "name", "current_price", "market_cap", "market_cap_rank", "fully_diluted_valuation", "total_volume", "circulating_supply", "total_supply", "max_supply", "ath", "atl", "last_updated"]
g_ignore_symbol = []
g_ignore_name = []
notes = []
PAGINATION=300

def get_header():
    data = {}
    data['User-Agent'] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0"
    data['accept'] = "application/json"
    return data

def is_200(req):
    if req.status_code == 200:
        return True
    else:
        return False

def get_driver():
    options=Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    print("[*] Obtained driver")
    return driver

def request_page(url):
	print("Requesting: {}".format(url))
	req = requests.get(url)
	soup = bs4.BeautifulSoup(req.text, 'html.parser')
	return soup

def get(url, header=None):
    if not header:
        header = get_header()

    print(f"[-] {url}")
    req = requests.get(url, headers=header)
    return req

def ping():
    ep = "/ping"

    url = root + ep
    req = get(url)
    if is_200(req):
        print(req.json())

def organize_data(json_data):
    data = []
    if json_data['symbol'] in g_ignore_symbol:
        return None

    for name in g_ignore_name:
        if name.lower() in json_data['name'].lower():
            return None

    #Check if we have already seen this coin
    notes = check_notes(json_data['id'], json_data['symbol'])
    if notes:
        return notes

    for header in csv_header:
        data.append(json_data[header])
    
    return data

def load_ignore_symbol(filename="./ignoresymbol.txt"):
    data = []
    with open(filename) as f:
        data = f.readlines()
        data = [x.rstrip() for x in data]
        f.close()

    return data

def load_ignore_name(filename="./ignorename.txt"):
    data = []
    with open(filename) as f:
        data = f.readlines()
        data = [x.rstrip() for x in data]
        f.close()

    return data

def write_csv(coins: list):
    with open("./tmp_coingecko.csv", 'w') as f:
        csvwriter = csv.writer(f)
        try:
            keys = coins[0].keys()
            csvwriter.writerow(keys)
            #print("[-] Wrote: {}".format(keys))
            for coin in coins:
                if coin == 'status':
                    print("Likely rate limit hit")
                    continue
                try:
                    #clean_data = organize_data(coin)
                    #if clean_data:
                    data = []
                    for key in keys:
                        data.append(str(coin[key]))
                    csvwriter.writerow(data)
                    #print("[-] Wrote: {}".format(data))
                except Exception as e:
                    print(str(e))
                    print("[!] Ignoring {}".format(coin['id']))
                    pdb.set_trace()
        except Exception:
            print(str(e))
            pdb.set_trace()

def write_csv_header():
    #Overwrite any existing csv with a new one
    data = list(csv_header)
    data.append("notes")
    data.append("interesting")
    data.append("category")
    with open("./tmp_coingecko.csv", 'w+') as f:
        csvwriter = csv.writer(f)
        csvwriter.writerow(data)
        f.close()
    
def check_notes(id, symbol):
     with open("./coingecko.csv", encoding='ISO-8859-1') as f:
        csvreader = csv.reader(f)
        try:
            for line in csvreader:
                if line[0] == id and line[1] == symbol:
                    if line[len(csv_header)] != '':
                        pdb.set_trace()
                        return line
        except Exception:
            print("Check notes error")
            pdb.set_trace()

def save_notes():
    tmp = open("./tmp_coingecko.csv", 'a+')
    csvwriter = csv.writer(tmp)

    with open("./coingecko.csv", encoding='ISO-8859-1') as f:
        csvreader = csv.reader(f)
        try:
            for line in csvreader:
                if csvreader.line_num == 0:
                    continue
                if csvreader.line_num == 1:
                    #Skip the header
                    continue

                #This may always be true
                if len(line) > len(csv_header):
                    #There is a note, save it
                    if line[len(csv_header)] != '':
                        #Something is here, save it
                        csvwriter.writerow(line)
        except Exception as e:
            print("Error")
            pdb.set_trace()

        f.close()

    tmp.close()


def get_historical_price_api(coin_id, days):
    url = "https://api.coingecko.com/api/v3/coins/{}/ohlc?vs_currency=usd&days={}".format(coin_id, str(days))
    print(url)
    data = get(url, header={"accept":"application/json"}).json()
    pdb.set_trace()
    

def get_historical_price_driver(driver, coin, end_date="2023-05-09", start_date="2022-11-01"):
    url = "https://www.coingecko.com/en/coins/{}/historical_data?end_date={}&start_date={}#panel".format(coin, end_date, start_date)
    data = driver.get(url)
    pdb.set_trace()

def get_historical_price(coin, end_date="2022-08-18", start_date="2022-05-17"):
    url = "https://www.coingecko.com/en/coins/{}/historical_data?end_date={}&start_date={}#panel".format(coin, end_date, start_date)
    soup = request_page(url)
    pdb.set_trace()
    try:
        table = soup.find_all('table', {'class':'table table-striped text-sm text-lg-normal'})[0]
    except Exception as e:
        print(str(e))
        print("Skipping: {}".format(coin))
        return coin, -1

    pdb.set_trace()
    high_open = []
    low_close = []

    rows = table.find_all('tr')
    for row in rows:
        if "Volume" in row.text:
            continue

        open_price, close_price = row.text.replace('\n\n','\n').replace('\n\n', '\n').strip().split('\n')[-2:]

        if open_price == 'N/A':
            continue
        else:
            open_price = open_price.replace('$', '').replace(',','')
            if open_price == ' ' or open_price == '':
                continue
            else:
                high_open.append(int(float(open_price)))

        if close_price == 'N/A':
            continue
        else:
            close_price = close_price.replace('$', '').replace(',','')
            if close_price == 'N/A':
                continue
    
            else:
                try:
                    low_close.append(int(float(close_price)))
                except ValueError:
                    continue
    
    high_open.sort()
    low_close.sort()

    try:
        high_price = high_open[-1]
        low_price = low_close[0]
    except IndexError:
        return coin, -1

    

    try:
        delta = (high_price - low_price) / low_price * 100
    except ZeroDivisionError:
        return coin, -1

    return coin, delta

def get_markets(driver, page: int):

    data = []
    order = "market_cap_desc"
    ep = f"/coins/markets?vs_currency={currency}&order={order}&per_page={PAGINATION}&page={int(page)}&sparkline=false"

    url = root + ep
    req = get(url)

    coins = []
    coins_data = req.json()
    return coins_data

def get_cap(cap: str, volume: str):
    url = "https://www.coingecko.com/en/coins/all?utf8=%E2%9C%93&filter_market_cap=5&filter_24h_volume=5&filter_price=&filter_24h_change=&filter_category=&filter_market=&filter_asset_platform=&filter_hashing_algorithm=&commit=Search"

    req = get(url)
    pdb.set_trace()

def sort_by_circulating_supply(driver, start_page: int, end_page: int):
    curr_page = start_page

    coins = []
    while curr_page <= end_page:
        curr_coins = get_markets(driver, curr_page)
        coins += curr_coins
        
        curr_page += 1

#    for coin in coins:
        #if not coin["max_supply"]:
            #coins.remove(coin)
            #print(coin)
#        if not coin["total_supply"]:
#            coins.remove(coin)
#            print(coin)
#        elif not coin["circulating_supply"]:
#            coins.remove(coin)
#            print(coin)

    #coins.sort(key=lambda x:x['circulating_supply'] / x['max_supply'], reverse=True)
    #pdb.set_trace()`
    #coins.sort(key=lambda x:x['circulating_supply'] / x['total_supply'], reverse=True)


        pdb.set_trace()
    write_csv(coins)
    #pdb.set_trace()

def trading_volume(coins, volume_percent):
    '''
    Only return the coins that have a 24 hr trading volume that is <volume_percent> of the market cap
    '''

    for coin in coins:
        if coin == 'status':
            print("Likely rate limit hit")
            pdb.set_trace()
            continue
        try:
            if coin['total_volume'] / coin['market_cap'] * 100 >= volume_percent:
                print(coin['name'])
                write_csv(coins)
        except TypeError:
            print("Type Error: {}".format(str(e)))
            pdb.set_trace()

def get_pages(driver, start_page, end_page):
    coins = []

    page = start_page
    while (page < end_page):
        tmp = get_markets(driver, page)
   
        coins += tmp
        page += 1

    trading_volume(coins, 10)

if __name__ == "__main__":
    #ping()
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start_page", default=1, type=int, help="Coingecko start page", required=True)
    parser.add_argument("-e", "--end_page", type=int, help="Coingecko end page", required=True)
    parser.add_argument("--supply", help="Sort coins by circulating supply percentage", action="store_true")
    parser.add_argument("--fdv", help="Sort coins by circulating FDV", action="store_true")
    parser.add_argument("-c", "--cap", type=str, help="Market cap type (5)")
    parser.add_argument("-v", "--volume", type=str, help="Volume type (5)")

    g_ignore_symbol = load_ignore_symbol()
    g_ignore_name = load_ignore_name()
    
    args = parser.parse_args()

    if args.cap:
        cap = args.cap
    
        if args.volume:
            volume = args.volume

        else:
            print("[!] Need volume")
            exit(-1)

        get_cap(cap, volume)

    elif args.supply:
        driver = get_driver()
        sort_by_circulating_supply(driver, args.start_page, args.end_page)

    elif args.fdv:
        #fully_diluted_valuation
        pass
    else:
        driver = get_driver()
        #get_page(str(args.start_page), driver)
        #pdb.set_trace()
        coins = get_pages(driver, args.start_page, args.end_page)
        #coins = get_pages(driver, 1, 2)
        #save_notes()
        #shutil.move("./tmp_coingecko.csv", "./coingecko.csv")

    print("[!] Done")
