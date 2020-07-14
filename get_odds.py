from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
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
    parser.add_argument('race',
                        action='store',
                        type=str,
                        help='race information (ex. 2回福島3日)')
    parser.add_argument('-n', '--number',
                        action='store',
                        type=int,
                        required=True,
                        help='race number')
    parser.add_argument('-i', '--interval',
                        action='store',
                        type=int,
                        default=116,
                        help='interval time to get odds > 10 s')
    parser.add_argument('-s', '--stop',
                        action='store_true',
                        help='stop if the last two odds sets are the same')
    parser.set_defaults(stop=False)
    args = parser.parse_args()
    return vars(args)

def mean_fukusho(str1, str2):
    return (float(str1) + float(str2) )/ 2.0

def waiting(driver, wait, xpath):
    try:
        wait.until(ec.element_to_be_clickable((By.XPATH, xpath)))
    except :
        print("Time out.")
        driver.save_screenshot("screenshot.png")
        quit()

def get_win_odds_list(race, number):
    url = "http://www.jra.go.jp/"
    pd.set_option('display.unicode.east_asian_width', True)
    user_agent = (
    "Chrome/83.0.4103.116"
    )
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = user_agent

    driver = webdriver.PhantomJS()
    wait = WebDriverWait(driver, 5)
    driver.get(url)

    oddspage_xpath = '//*[@id="quick_menu"]/div/ul/li[3]/a'
    waiting(driver, wait, oddspage_xpath)
    out = driver.find_element_by_xpath(oddspage_xpath)
    out.click()

    race_link_text = race
    wait.until(ec.presence_of_all_elements_located)
    out = driver.find_element_by_link_text(race_link_text)
    out.click()

    odds_xpath = '//table[@id="race_list"]/tbody/tr[{}]/th/a[1]'.format(number)
    waiting(driver, wait, odds_xpath)
    out = driver.find_element_by_xpath(odds_xpath)
    out.click()
    sleep(1)
    root = lxml.html.fromstring(driver.page_source)
    driver.save_screenshot("screenshot.png")

    mtx = []
    index = []

    for i in root.cssselect("table > tbody > tr"):
        if i.cssselect("td.num"):
            uno = int(i.cssselect("td.num")[0].text)
            name = i.cssselect("td.horse")[0].cssselect("a")[0].text
            _tansho = i.cssselect("td.odds_tan")[0]
            if _tansho.cssselect("strong"):
                tansho = float(_tansho.cssselect("strong")[0].text)
            else:
                tansho = _tansho.text
            _fukusho = i.cssselect("td.odds_fuku")[0]
            fukusho = mean_fukusho(_fukusho.cssselect("span > span")[0].text,
                                   _fukusho.cssselect("span > span")[2].text)
            index.append(uno)
            mtx.append([name, tansho, fukusho])
    df = pd.DataFrame(mtx, index=index, columns=["name", "tansho", "fukusho"])
    return df

def stack_df(tansho, fukusho, new, stop):
    dt_now = datetime.datetime.now().strftime("%H:%M:%S")
    new = new.loc[tansho.index, :]
    if stop:
        if (tansho.iloc[:, -1] - new["tansho"] == 0).all():
            print("odds change stopped")
            quit()
    tansho[dt_now] = new["tansho"]
    fukusho[dt_now] = new["fukusho"]
    return tansho, fukusho

def main(args):
    if args["interval"] < 10:
        raise ValueError("interval time must be > 10 seconds.")
    ID = "{}_{}R".format(args["race"], args["number"])
    if os.path.exists(ID + ".tansho.csv"):
        tansho = pd.read_csv(ID + ".tansho.csv", header=0, index_col=0)
        fukusho = pd.read_csv(ID + ".fukusho.csv", header=0, index_col=0)
        first = False
        if tansho.shape[0] < 4:
            first = True
            print("Renew the table...")
    else:
        first = True
        print("First time generating table...")
    try:
        while True:
            new = get_win_odds_list(args["race"], args["number"])
            if first:
                dt_now = datetime.datetime.now().strftime("%H:%M:%S")
                tansho = new.loc[:, ["name", "tansho"]]
                tansho.columns = ["name", dt_now]
                fukusho = new.loc[:, ["name", "fukusho"]]
                fukusho.columns = ["name", dt_now]
                first = False
            else:
                tansho, fukusho = stack_df(tansho, fukusho, new, args["stop"])
            tansho.to_csv(ID + ".tansho.csv")
            fukusho.to_csv(ID + ".fukusho.csv")
            sleep(args["interval"])
    except KeyboardInterrupt:
        print("\n Successfully ended.")
        
if __name__ == '__main__':
    main(parser_setting())
