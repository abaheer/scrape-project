from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import TimeoutException
from selenium.webdriver.chrome.options import Options

from tabulate import tabulate
import os
import pandas as pd


class Scraper:
    def __init__(self, items: list):
        self.sticker_filter = False
        self.special = ['holo', 'gold', 'foil']
        self.avoid = ['rmr', 'sig']
        self.is_special = False
        self.first_load = True
        self.count = 0
        self.is_first = True
        self.df = None
        self.file_path = ''
        self.output = []

        chrome_options = Options()
        #chrome_options.add_argument("--headless=new")
        # need to specify user_agent; otherwise blocked when headless
        #user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        #chrome_options.add_argument(f'user-agent={user_agent}')

        self.service = Service(executable_path='chromedriver.exe')
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)

        self.items = items
        self.load_page()

    def sticker_to_string(self, s: str):
        if s:
            s = s.split('/')
            return s[-1].split('.')[0] + ' ' + s[-2]

    def format_stickers(self, stickers):
        all_stickers = []
        self.is_special = False
        for s in stickers:
            sticker = self.sticker_to_string(s.find_element(By.TAG_NAME, "img").get_attribute('src'))
            all_stickers.append(sticker)
            if sticker and self.sticker_filter and (self.special[0] in sticker or self.special[1] in sticker or
                                                    self.special[2] in sticker) and (self.avoid[0] not in sticker and
                                                                                     self.avoid[1] not in sticker):
                self.is_special = True
        return all_stickers

    def load_page(self):
        for item in self.items:
            print('loading page: ', item[0])
            self.driver.get(item[0])
            self.file_path = item[1]
            self.sticker_filter = item[2]

            file_exists = os.path.exists(self.file_path)

            if not file_exists:
                df = pd.DataFrame(columns=['Listing Name', 'Wear', 'Float', 'Price', 'Stickers', 'Link'])
                df.to_csv(self.file_path, index=False)

            self.df = pd.read_csv(self.file_path)
            self.read_pages()
        print('\n')
        print(tabulate(self.output, headers=["name", "price", "buff_price", "stickers", "link"]))

    def read_page(self):
        # on first visit to website
        if self.first_load:
            # accept cookies before proceeding as we will need to click some things
            WebDriverWait(self.driver, 10).until(
                expected_conditions.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))).click()
            self.first_load = False

        # compare to buff market price instead of steam market price
        WebDriverWait(self.driver, 5).until(
            expected_conditions.element_to_be_clickable((By.XPATH, '//img[@src="/img/price_plus@2x.png"]'))).click()
        comparison = self.driver.find_element(By.CSS_SELECTOR, "div[class^='ItemCardNewBody_marketFilterRow']")
        WebDriverWait(comparison, 5).until(
            expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "div[class^='FilterRadio_checkbox']"))).click()

        # wait for buff prices to load
        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "span[class^='ItemCardNewBody_buffPrice']")))

        listings = self.driver.find_elements(By.CSS_SELECTOR, "div[class^='ItemCardNew_wrapper']")

        for n in listings:
            if ' ' not in n.get_attribute('class'):

                buff_price = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "span[class^='ItemCardNewBody_buffPrice']"))).text[7:]

                link = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('href')

                name = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "span[class^='ItemCardNewBody_name']"))).text

                wear = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div[class^='ItemCardNewBody_wear']"))).text

                float_value = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "span[class^='ItemCardNewBody_float']"))).text

                price = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div[class^='ItemCardNewBody_pricePrimary']"))).text[1:]

                try:
                    price = round(float(price)*1.09, 2)
                    buff_price = round(float(buff_price)*1.09, 2)

                    stickers = WebDriverWait(n, 1).until(
                        expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class^='Sticker_container']")))
                    self.is_special = False
                    all_stickers = self.format_stickers(stickers)

                    print([name, price, buff_price, all_stickers, link])

                    if link not in self.df['Link'].values and (self.is_special or not self.sticker_filter):
                        if self.is_first:
                            self.df = self.df._append({'Listing Name': 'NEW SCRAPE'}, ignore_index=True)
                            self.is_first = False

                        self.df = self.df._append(
                            {'Listing Name': name, 'Wear': wear, 'Float': float_value, 'Price': price,
                             'Stickers': all_stickers,
                             'Link': link}, ignore_index=True)

                    self.output.append([name, price, buff_price, all_stickers, link])

                except TimeoutException as e:
                    print('listing does not contain stickers')
                except TypeError as e:
                    print("prices did not load as expected")

        self.df.to_csv(self.file_path, index=False)

    def read_pages(self):
        self.read_page()
        WebDriverWait(self.driver, 2).until(
            expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[class^='Pager_next']"))).click()
        # while True:
        #     try:
        #         self.read_page()
        #         WebDriverWait(self.driver, 2).until(
        #             expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[class^='Pager_next']"))).click()
        #     except TimeoutException as e:
        #         print(e)
        #         self.count += 1
        #         if self.count < len(self.items):
        #             print('no next page, going to next url')
        #             break
        #         else:
        #             print("no next page or next url, quitting.")
        #             self.driver.quit()
        #             break


# take list of tuples in form: (page_url: str, file_path: str, sticker_filter: bool)
url="https://gamerpay.gg/?buffMax=102&priceMin=370.0619853825516&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&sortBy=deals&ascending=true&tournaments=Paris+2023%2CAntwerp+2022%2CStockholm+2021%2CKatowice+2019%2CLondon+2018%2CBoston+2018%2CKrakow+2017&priceMax=1850.3099269127579&subtype=CSGO_Type_Rifle.AK-47%2CCSGO_Type_Rifle.M4A1-S%2CCSGO_Type_Rifle.M4A4&page=1"
url2="https://gamerpay.gg/?buffMax=102&priceMin=370.0619853825516&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&sortBy=deals&ascending=true&tournaments=Paris+2023%2CAntwerp+2022%2CStockholm+2021%2CKatowice+2019%2CLondon+2018%2CBoston+2018%2CKrakow+2017&priceMax=1850.3099269127579&subtype=CSGO_Type_SniperRifle.AWP%2CCSGO_Type_Pistol.Desert+Eagle%2CCSGO_Type_Pistol.USP-S%2CCSGO_Type_Pistol.Glock-18&page=1"
url3="https://gamerpay.gg/?buffMax=105&priceMin=114.99999999999999&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&tournaments=Katowice+2014%2CCologne+2014%2CDreamHack+2014%2CKatowice+2015%2CCologne+2015%2CCluj-Napoca+2015%2CMLG+Columbus+2016%2CCologne+2016%2CAtlanta+2017&page=1&priceMax=2200&sortBy=deals&ascending=true"
url4="https://gamerpay.gg/?buffMax=105&priceMin=106.14731401144546&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&query=AWP+%7C+Asiimov&autocompleted=1&page=1"

#scrape_items = [(url, 'data_sh.csv', True), (url2, 'data_sh.csv', True), (url3, 'data.csv', False)]
scrape_items = [(url4, 'awp_asiimov.csv', False)]
Scraper(scrape_items)
