import sys
import os
import time
from datetime import datetime,date

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


COVID19_URL = "https://en.wikipedia.org/wiki/Template:COVID-19_pandemic_data/Japan_medical_cases_chart"
#COVID19_URL = "https://en.wikipedia.org/wiki/Template:COVID-19_pandemic_data/United_States_medical_cases_chart"
CLICKING_ID_PREFIX = 'mw-customcollapsible-'
CLICKING_ID_PREFIX_CLASS = 'mw-customtoggle-'
MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'jul-l15']
clicking_ids = [CLICKING_ID_PREFIX + m for m in MONTHS]
LASTEST_DOWNLOADED_HTML_PATH = "./resources/last_downloaded.html"

def download_html_code():
    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0 Mobile/14C92')
    driver = webdriver.Chrome("./bin/chromedriver", options=options)
    driver.set_window_size(600,1000)
    driver.get(COVID19_URL)

    html_code = driver.page_source
    driver.close()
    driver.quit()

    return html_code

def remove_comma(text):
    return text.replace(',', '')

def check_date(date_text):
    try:
        datetime.strptime(date_text,"%Y-%m-%d")
        return True
    except ValueError:
        return False

def get_data_frame(html_code):
    soup = BeautifulSoup(html_code, "html.parser")
    df = pd.DataFrame(columns=["day", "new_case", "new_death"])
    previous_case = 0
    previous_death = 0

    for cid in clicking_ids:
        rows = soup.select('table tr[id="%s"]' % cid)

        for r in rows:
            day = r.select('td:nth-child(1)')[0]
            case = r.select('td:nth-child(3) span[class="cbs-ibr"]')[0]
            death = r.select('td:nth-child(4) span[class="cbs-ibr"]')[0]
            day = day.get_text()
            case = remove_comma(case.get_text())
            death =remove_comma(death.get_text())
            #print(type(day), type(case), type(death))
            #print(day, case, death)

            if not day or not case or not death:
                continue
            if not check_date(day):
                continue
            if not case.isdecimal():
                continue
            if not death.isdecimal():
                continue

            case, death  = float(case), float(death)
            new_case = case - previous_case
            new_death = death - previous_death
            day = datetime.strptime(day, "%Y-%m-%d")

            df = df.append({'day': day, 'new_case': new_case, 'new_death': new_death}, ignore_index=True)

            previous_case = case
            previous_death = death

    return df

def main():
    html_code = ""

    if os.path.exists(LASTEST_DOWNLOADED_HTML_PATH):
        with open(LASTEST_DOWNLOADED_HTML_PATH, 'r') as rf:
            html_code = rf.read()
    else:
        html_code = download_html_code()
        with open(LASTEST_DOWNLOADED_HTML_PATH, 'w') as wf:
            wf.write(html_code)

    df = get_data_frame(html_code)
    #print(df)

    df = df.resample(rule="M", on='day').sum()
    print(df)
    df.plot()

    df['case_fatality_rate(%)'] = 100 * df['new_death'] / df['new_case']
    df = df.drop("new_case", axis=1).drop("new_death", axis=1)
    print(df)
    df.plot()
    plt.show()


if __name__ == '__main__':
    main()
