from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import time

service = Service(executable_path='chromedriver.exe')
driver = webdriver.Chrome(service=service)

# many page url
# driver.get("https://gamerpay.gg/?buffMax=105&priceMin=114.99999999999999&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&tournaments=Katowice+2014%2CCologne+2014%2CDreamHack+2014%2CKatowice+2015%2CCologne+2015%2CCluj-Napoca+2015%2CMLG+Columbus+2016%2CCologne+2016%2CAtlanta+2017&page=1&priceMax=2200&sortBy=deals&ascending=true")

# # 2 item url
# driver.get(
#    "https://gamerpay.gg/?buffMax=105&priceMin=115.37751522983201&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&tournaments=Katowice+2014%2CCologne+2014%2CDreamHack+2014%2CKatowice+2015%2CCologne+2015%2CCluj-Napoca+2015%2CMLG+Columbus+2016%2CCologne+2016%2CAtlanta+2017&page=1&priceMax=147.68321949418498&sortBy=deals&ascending=true")

# 2-page url
driver.get("https://gamerpay.gg/?buffMax=105&priceMin=114.99999999999999&wear=Battle-Scarred%2CField-Tested%2CMinimal"
           "%22%22+Wear%2CFactory+New&tournaments=Katowice+2014%2CCologne+2014%2CDreamHack+2014%2CKatowice+2015"
           "%2CCologne%22%22+2015%2CCluj-Napoca+2015%2CMLG+Columbus+2016%2CCologne+2016%2CAtlanta+2017&page=1"
           "&priceMax=5500&sortBy%22%22=deals&ascending=true&sortBy=price")


def sticker_to_string(s: str):
    s = s.split('/')
    return s[-1].split('.')[0] + ' ' + s[-2]


def read_page():

    # exit if element does not exist
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div[class^='ItemCardNew_wrapper']")))

    listings = driver.find_elements(By.CSS_SELECTOR, "div[class^='ItemCardNew_wrapper']")

    for n in listings:
        if ' ' not in n.get_attribute('class'):
            print(n.find_element(By.TAG_NAME, "a").get_attribute('href'))  # link
            print(n.find_element(By.CSS_SELECTOR, "span[class^='ItemCardNewBody_name']").text)  # listing name
            print(n.find_element(By.CSS_SELECTOR, "div[class^='ItemCardNewBody_wear']").text)  # wear
            print(n.find_element(By.CSS_SELECTOR, "span[class^='ItemCardNewBody_float']").text)  # float
            print(n.find_element(By.CSS_SELECTOR, "div[class^='ItemCardNewBody_pricePrimary']").text)  # price

            stickers = n.find_elements(By.CSS_SELECTOR, "div[class^='Sticker_container']")
            for sticker in stickers:
                sticker_name = sticker_to_string(sticker.find_element(By.TAG_NAME, "img").get_attribute('src'))
                print(sticker_name)


read_page()

while True:
    try:
        WebDriverWait(driver, 20).until(
            expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[class^='Pager_next']"))).click()
        read_page()
    except Exception as e:
        print("no next page, quitting.")
        driver.quit()
