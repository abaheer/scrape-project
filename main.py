from selenium import webdriver
from selenium.common import ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import TimeoutException
from selenium.webdriver.chrome.options import Options

from tabulate import tabulate
from email.message import EmailMessage
import ssl
import smtplib
import json

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
        self.page = 1

        chrome_options = Options()

        # ----------------------------- run in headless -----------------------------
        chrome_options.add_argument("--headless=new")
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        # ------- need to specify user_agent; otherwise blocked when headless -------

        # chrome_options.add_experimental_option("detach", True)

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
        self.send_email()

    def read_page(self):
        # on first visit to website
        if self.first_load:
            # accept cookies before proceeding as we will need to click some things
            WebDriverWait(self.driver, 10).until(
                expected_conditions.element_to_be_clickable(
                    (By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))).click()
            self.first_load = False

        # compare to buff market price instead of steam market price
        WebDriverWait(self.driver, 15).until(
            expected_conditions.element_to_be_clickable((By.XPATH, '//img[@src="/img/price_plus@2x.png"]'))).click()
        comparison = self.driver.find_element(By.CSS_SELECTOR, "div[class^='ItemCardNewBody_marketFilterRow']")
        WebDriverWait(comparison, 15).until(
            expected_conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, "div[class^='FilterRadio_checkbox']"))).click()

        # wait for buff prices to load
        WebDriverWait(self.driver, 15).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, "span[class^='ItemCardNewBody_buffPrice']")))

        listings = self.driver.find_elements(By.CSS_SELECTOR, "div[class^='ItemCardNew_wrapper']")

        for n in listings:
            if ' ' not in n.get_attribute('class'):

                buff_price = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "span[class^='ItemCardNewBody_buffPrice']"))).text[7:]

                link = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('href')

                name = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "span[class^='ItemCardNewBody_name']"))).text

                wear = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[class^='ItemCardNewBody_wear']"))).text

                float_value = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "span[class^='ItemCardNewBody_float']"))).text

                price = WebDriverWait(n, 10).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[class^='ItemCardNewBody_pricePrimary']"))).text[1:]

                try:
                    price = round(float(price) * 1.09, 2)
                    buff_price = round(float(buff_price) * 1.09, 2)

                    stickers = WebDriverWait(n, 1).until(
                        expected_conditions.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "div[class^='Sticker_container']")))
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

                        self.output.append([name, str(price)+' / '+str(buff_price), all_stickers, link])

                except TimeoutException as e:
                    print('listing does not contain stickers')
                except TypeError as e:
                    print("prices did not load as expected")

        self.df.to_csv(self.file_path, index=False)

    def read_pages(self):
        while True:
            try:
                self.read_page()
                self.page += 1
                WebDriverWait(self.driver, 2).until(
                    expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[class^='Pager_next']")))
                self.driver.get(self.items[self.count][0] + f'&page={self.page}')

            except TimeoutException as e:
                self.count += 1
                if self.count < len(self.items):
                    self.page = 1
                    print('no next page, going to next url')
                    print("\n")
                    break
                else:
                    print("no next page or next url, quitting.")
                    self.driver.quit()
                    print("\n")
                    break

    def send_email(self):
        if self.output and os.path.isfile('email.json'):
            with open("email.json") as json_file:
                json_data = json.load(json_file)
                email_sender = json_data['email_sender']
                email_password = json_data['email_password']
                email_receiver = json_data['email_receiver']
                subject = "New items from GamerPay Scraper"
                body = tabulate(self.output, headers=["name", "price/buff", "stickers", "link"], tablefmt='html')
                em = EmailMessage()
                em['From'] = email_sender
                em['To'] = email_receiver
                em['Subject'] = subject
                em.set_content('fail')
                em.add_alternative(body, subtype='html')
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                    smtp.login(email_sender, email_password)
                    smtp.sendmail(email_sender, email_receiver, em.as_string())
            print('email sent')
        else:
            print(tabulate(self.output, headers=["name", "price/buff", "stickers", "link"]))


# take list of tuples in form: (page_url: str, file_path: str, sticker_filter: bool)
url = "https://gamerpay.gg/?query=M4A1-S+%7C+Chantico%27s+Fire&autocompleted=1&page=1"
url2 = "https://gamerpay.gg/?query=AWP+%7C+Asiimov&autocompleted=1&page=1"
url3 = "https://gamerpay.gg/?autocompleted=1&page=1&query=AK-47+%7C+Redline"

scrape_items = [(url, 'chantico.csv', True), (url2, 'awp-asiimov.csv', True), (url3, 'redline.csv', True)]
Scraper(scrape_items)
