from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import lxml.html
import pandas as pd
from time import sleep
import sys
import os
import datetime
import argparse
import warnings
warnings.simplefilter('ignore', UserWarning)


def parser_setting():
    parser = argparse.ArgumentParser()
    parser.add_argument('url',
                        action='store',
                        type=str,
                        help='csv')
    parser.add_argument('-i', '--interval',
                        action='store',
                        type=int,
                        default=20,
                        help='interval time to get odds > 10 s')
    parser.set_defaults(ratio=False)
    args = parser.parse_args()
    return vars(args)

def mean_fukusho(string):
    v = string.split(" ")
    return (float(v[0]) + float(v[-1]) )/ 2.0

def get_win_odds_list(url):
    pd.set_option('display.unicode.east_asian_width', True)
    driver = webdriver.PhantomJS()                  # PhamtomJSのWebDriverオブジェクトを作成する。
    driver.get(url)                                 # オッズ表示画面を開く
    sleep(5)                                        # 負荷分散の為のsleep
    root = lxml.html.fromstring(driver.page_source) # 検索結果を表示し、lxmlで解析準備

    mtx = []
    index = []
    for i in root.cssselect("div"):
        if i.get("class", "") == "RaceOdds_HorseList Tanfuku":
            for j in i.cssselect("tr"):
                if j.get("id", False):
                    data = j.cssselect("span")
                    uno = int(data[0].text)
                    name = data[2].text
                    tansho = float(data[3].text)
                    fukusho = mean_fukusho(data[4].text)
                    index.append(uno)
                    mtx.append([name, tansho, fukusho])
    df = pd.DataFrame(mtx, index=index, columns=["name", "tansho", "fukusho"])
    return df

def stack_df(tansho, fukusho, new):
    dt_now = datetime.datetime.now().strftime("%H:%M:%S")
    new = new.loc[tansho.index, :]
    tansho[dt_now] = new["tansho"]
    fukusho[dt_now] = new["fukusho"]
    return tansho, fukusho

def main(args):
    if args["interval"] < 10:
        raise ValueError("interval time must be > 10 seconds.")
    ID = args["url"].split("=")[-1]
    if os.path.exists(ID + ".tansho.csv"):
        tansho = pd.read_csv(ID + ".tansho.csv", header=0, index_col=0)
        fukusho = pd.read_csv(ID + ".fukusho.csv", header=0, index_col=0)
        first = False
    else:
        first = True
    try:
        while True:
            new = get_win_odds_list(args["url"])
            if first:
                dt_now = datetime.datetime.now().strftime("%H:%M:%S")
                tansho = new.loc[:, ["name", "tansho"]]
                tansho.columns = ["name", dt_now]
                fukusho = new.loc[:, ["name", "fukusho"]]
                fukusho.columns = ["name", dt_now]
                first = False
            else:
                tansho, fukusho = stack_df(tansho, fukusho, new)
            tansho.to_csv(ID + ".tansho.csv")
            fukusho.to_csv(ID + ".fukusho.csv")
            sleep(args["interval"])
    except KeyboardInterrupt:
        print("\n Successfully ended.")
        
if __name__ == '__main__':
    main(parser_setting())
