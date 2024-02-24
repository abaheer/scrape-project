from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

service = Service(executable_path='chromedriver.exe')
driver = webdriver.Chrome(service=service)

# driver.get("https://https://gamerpay.gg/?buffMax=105&priceMin=125.41497602360754&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&tournaments=Katowice+2014%2CCologne+2014%2CDreamHack+2014%2CKatowice+2015%2CCologne+2015%2CCluj-Napoca+2015%2CMLG+Columbus+2016%2CCologne+2016%2CAtlanta+2017&page=1&priceMax=3135.374400590188&sortBy=deals&ascending=true")

driver.get(
    "https://gamerpay.gg/?buffMax=105&priceMin=115.37751522983201&wear=Battle-Scarred%2CField-Tested%2CMinimal+Wear%2CFactory+New&tournaments=Katowice+2014%2CCologne+2014%2CDreamHack+2014%2CKatowice+2015%2CCologne+2015%2CCluj-Napoca+2015%2CMLG+Columbus+2016%2CCologne+2016%2CAtlanta+2017&page=1&priceMax=147.68321949418498&sortBy=deals&ascending=true")

# exit if element does not exist
WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(((By.CLASS_NAME, "Index_feedContainer__Wa9_B"))))

listings = driver.find_elements(By.CLASS_NAME, "ItemCardNew_wrapper__phLcV")

for n in listings:
    if(n.get_attribute('class') == "ItemCardNew_wrapper__phLcV"):
        print(n.find_element(By.TAG_NAME, "a").get_attribute('href'))  # link
        print(n.find_element(By.CLASS_NAME, "ItemCardNewBody_name__SYDXg").text)  # listing name
        print(n.find_element(By.CLASS_NAME, "ItemCardNewBody_wear__vFzrf").text)  # wear
        print(n.find_element(By.CLASS_NAME, "ItemCardNewBody_float__mpCp4").text)  # float
        print(n.find_element(By.CLASS_NAME, "ItemCardNewBody_pricePrimary__pqq_k").text)  # price

        stickers = n.find_elements(By.CLASS_NAME, "Sticker_container__aWWJd")
        for sticker in stickers:
            print(sticker.find_element(By.TAG_NAME, "img").get_attribute('src'))

driver.quit()