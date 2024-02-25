from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import TimeoutException
from selenium.webdriver.chrome.options import Options

import os
import pandas as pd


class Scraper:
    def __init__(self, sticker_filter: bool):

        self.sticker_filter = sticker_filter
        self.special = ['holo', 'gold', 'foil']
        self.is_special = False
        self.is_first = True

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=chrome_options)

        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')

        self.service = Service(executable_path='chromedriver.exe')
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)

        # many page url
        #self.driver.get(
        #    "https://gamerpay.gg/?buffMax=105&priceMin=114.99999999999999&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&tournaments=Katowice+2014%2CCologne+2014%2CDreamHack+2014%2CKatowice+2015%2CCologne+2015%2CCluj-Napoca+2015%2CMLG+Columbus+2016%2CCologne+2016%2CAtlanta+2017&page=1&priceMax=2200&sortBy=deals&ascending=true")

        # alt
        self.driver.get(
            "https://gamerpay.gg/?buffMax=102&priceMin=148.4691995573589&wear=Battle-Scarred%2CField-Tested%2CMinimal"
            "+Wear%2CFactory+New&sortBy=deals&ascending=true&tournaments=Paris+2023%2CAntwerp+2022"
            "%2CStockholm+2021%2CKatowice+2019%2CLondon+2018%2CBoston+2018%2CKrakow+2017&page=1&priceMax=2766"
            ".506824050166")

        # # 2 item url
        # driver.get("https://gamerpay.gg/?buffMax=105&priceMin=115.37751522983201&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&tournaments=Katowice+2014%2CCologne+2014%2CDreamHack+2014%2CKatowice+2015%2CCologne+2015%2CCluj-Napoca+2015%2CMLG+Columbus+2016%2CCologne+2016%2CAtlanta+2017&page=1&priceMax=147.68321949418498&sortBy=deals&ascending=true")

        self.file_path = 'data_sh.csv'
        file_exists = os.path.exists(self.file_path)

        # initialize DataFrame and write header if file does not exist
        if not file_exists:
            df = pd.DataFrame(columns=['Listing Name', 'Wear', 'Float', 'Price', 'Stickers', 'Link'])
            df.to_csv(self.file_path, index=False)

        # read the CSV file into a DataFrame
        self.df = pd.read_csv(self.file_path)

        self.read_pages()

    def sticker_to_string(self, s: str):
        s = s.split('/')
        return s[-1].split('.')[0] + ' ' + s[-2]

    def format_stickers(self, stickers):
        all_stickers = []
        for s in stickers:
            sticker = self.sticker_to_string(s.find_element(By.TAG_NAME, "img").get_attribute('src'))
            all_stickers.append(sticker)
            if sticker and self.sticker_filter and (self.special[0] in sticker or self.special[1] in sticker or self.special[2] in sticker):
                self.is_special = True
        return all_stickers

    def read_page(self):
        # give 10 second for elements to show, else exit.
        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div[class^='ItemCardNew_wrapper']")))
        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "span[class^='ItemCardNewBody_name']")))
        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div[class^='ItemCardNewBody_wear']")))
        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "span[class^='ItemCardNewBody_float']")))

        listings = self.driver.find_elements(By.CSS_SELECTOR, "div[class^='ItemCardNew_wrapper']")

        for n in listings:
            if ' ' not in n.get_attribute('class'):
                link = n.find_element(By.TAG_NAME, "a").get_attribute('href')
                name = n.find_element(By.CSS_SELECTOR, "span[class^='ItemCardNewBody_name']").text
                wear = n.find_element(By.CSS_SELECTOR, "div[class^='ItemCardNewBody_wear']").text
                float_value = n.find_element(By.CSS_SELECTOR, "span[class^='ItemCardNewBody_float']").text
                price = n.find_element(By.CSS_SELECTOR, "div[class^='ItemCardNewBody_pricePrimary']").text[1:]

                stickers = n.find_elements(By.CSS_SELECTOR, "div[class^='Sticker_container']")
                self.is_special = False
                all_stickers = self.format_stickers(stickers)

                if link not in self.df['Link'].values and (self.is_special or not self.sticker_filter):
                    if self.is_first:
                        self.df = self.df._append({'Listing Name': 'NEW SCRAPE'}, ignore_index=True)
                        self.is_first = False

                    self.df = self.df._append(
                        {'Listing Name': name, 'Wear': wear, 'Float': float_value, 'Price': price,
                         'Stickers': all_stickers,
                         'Link': link}, ignore_index=True)

                    print([name, price, all_stickers, link])

        # Write DataFrame back to CSV file
        self.df.to_csv(self.file_path, index=False)

    def read_pages(self):
        while True:
            try:
                self.read_page()
                WebDriverWait(self.driver, 2).until(
                    expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[class^='Pager_next']"))).click()
            except TimeoutException as e:
                print("no next page, quitting.")
                self.driver.quit()
                break


Scraper(True)
