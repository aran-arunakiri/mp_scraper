### PATH TO BROWSER
import httplib

path_to_browser = "./chromedriver"
###

from selenium import webdriver  # install selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select

from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
import time
from datetime import datetime
import os
import re
import pickle
import unicodedata
import xlwt  # install xlwt
import xlrd  # install xlrd
from lxml import html  # install lxml

TIME_PAUSE = 2.0  # pause

LIST_OF_RELEVANT_FOLDERS = []


def wait_by_xpath(xp):
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xp)))
        time.sleep(TIME_PAUSE)
    except TimeoutException:
        print "Too much time has passed."


def wait_by_class(class_name):
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        time.sleep(TIME_PAUSE)
    except Exception:
        print "Too much time has passed."


def wait_by_id(id_name):
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, id_name)))
        time.sleep(1.0)
    except TimeoutException:
        print "Too much time has passed."


def write():
    column_indexes = {"seller_name": 0, "seller_phone": 3, "seller_location": 5, "product_name": 7, "price": 11,
                      "url": 13}

    for relevant_folder in LIST_OF_RELEVANT_FOLDERS:
        current_row = 0
        wb = xlwt.Workbook(encoding='windows-1252')
        ws = wb.add_sheet("Sheet1", cell_overwrite_ok=True)
        ws.write(0, column_indexes["seller_name"], "Seller name")
        ws.write(0, column_indexes["seller_phone"], "Seller TEL")
        ws.write(0, column_indexes["seller_location"], "Seller location")
        ws.write(0, column_indexes["product_name"], "Product name")
        ws.write(0, column_indexes["price"], "Price")
        ws.write(0, column_indexes["url"], "Link")
        current_row = current_row + 1

        all_pages = os.listdir(relevant_folder + '/saved')
        # keys are: seller_name, seller_phone, seller_location, product_name, price, url
        for one_page in all_pages:
            with open(relevant_folder + '/saved' + '/' + one_page, "rb") as fi:
                d = pickle.load(fi)  # d is a list of dicts, one dict is one ad
            for ad in d:
                for key in ad:
                    ws.write(current_row, column_indexes[key], ad[key])
                current_row = current_row + 1

        wb.save("output link " + str(1 + LIST_OF_RELEVANT_FOLDERS.index(relevant_folder)) + '.xls')

    return


def fetch_master_url(master_link):
    print 'fetching url ' + master_link
    driver.get(master_link)  # get the first page
    print 'url loaded 1'
    wait_by_class("search-results-table")
    print 'url loaded 2'
    # first see the general page link and the number of pages
    general_page_link = master_link
    singlePage = False;
    try:
        page_2_el = driver.find_element_by_xpath(
            "//span[@id='pagination-pages']/a[contains(@data-ga-track-event, 'gination')]")
        page_2_link = page_2_el.get_attribute("href")
        last_page_el = driver.find_element_by_xpath("//span[@id='pagination-pages']/span[@class='last']")
        last_page = int(last_page_el.get_attribute("innerText"))  # inclusively this page
        general_page_link = page_2_link[0:page_2_link.find(
            "&currentPage=")] + "&currentPage="  # append the number of page to this,
    except Exception:
        print 'just 1 page'
        last_page = 1
        singlePage = True

    print 'last_page ' + str(last_page)
    for page_index in range(1, last_page + 1):  # from page 2  until the last_page+1 index
        print 'got a page ' + str(page_index)
        if not singlePage:
            driver.get(general_page_link + str(page_index))

        wait_by_class("search-results-table")
        if "&currentPage=" not in driver.current_url and not singlePage:
            print "Page doesn't exist."
            continue

        innerHTML = driver.execute_script("return document.body.innerHTML")
        htmlElem = html.document_fromstring(innerHTML)

        elmlist = htmlElem.xpath(
            "//section[contains(@class, 'search-results-table')]/article[contains(@class,'search-result')]")  # upper ones, yellow list are just advertisements
        elements = []
        for elm in elmlist:
            thiselm = {}  # url, name of product, price, name of seller, location of seller
            url_path = elm.xpath(".//a[contains(@class, 'listing-table-mobile-link')]")
            thiselm['url'] = url_path[0].attrib["href"]  # url

            name_path = elm.xpath(
                ".//div/div[contains(@class,'cell column-listing')]/div[contains(@class, 'listing-title-description')]/h2/a/span")
            thiselm['product_name'] = name_path[0].attrib['title']  # name of product

            price_path = elm.xpath(
                ".//div/div[contains(@class, 'column-price')]/div[contains(@class, 'price-and-thumb')]/span/span")
            thiselm['price'] = price_path[0].text_content()  # price in eur, will have to work on the string

            elements.append(thiselm)

        for elm in elements:  # get images
            print ("Element index " + str(elements.index(elm)))
            if 'url' not in elm:
                continue
            driver.get(elm['url'])
            wait_by_id("vip-seller")

            image_paths = driver.find_elements_by_xpath(
                "//div[@id='vip-image-viewer']/div[contains(@class, 'image ')]/img")

            for i in image_paths:
                print i.get_attribute('src')


options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(path_to_browser, chrome_options=options)
# driver.maximize_window()

input_workbook = xlrd.open_workbook("INPUT.xlsx")
input_sheet_names = input_workbook.sheet_names()
input_sheet = input_workbook.sheet_by_name(input_sheet_names[0])

# first handle cookies button
driver.get("https://www.marktplaats.nl/")
wait_by_class("page")
print "Before click"

N_click_attempts = 0
while 1:
    if N_click_attempts == 10:
        print "Something is wrong. "
        break
    print "Try to click."
    N_click_attempts = N_click_attempts + 1
    try:
        cook_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//form[@method='post']/input[@type='submit']"))).click()
        time.sleep(2.0)
    except:
        time.sleep(2.0)
        break

# cook_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//form[@method='post']/input[@type='submit']"))).click()
print "After click"
# cook_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//form[@method='post']/input[@type='submit']"))).click()
# cook_button.click()
# driver.execute_script('arguments[0].click();', cook_button)

'''
while 1:
    try:
        cookie_btn_el = driver.find_element_by_xpath("//form[@id='track-accept']/input[contains(@value, 'accepteren')]")
        time.sleep(2.0)
    except NoSuchElementException:
        break
'''

# now start scraping
time_beg = time.time()
driver.set_page_load_timeout(60)
driver.get("https://www.marktplaats.nl/c/auto-s/c91.html")
wait_by_id("cars-search-categories")

# brands = driver.find_elements_by_xpath(
#     "//div[@id='cars-search-categories']/optgroup[contains(@label, 'Populair ')]")
brands = driver.find_elements_by_xpath(
    "//div[@id='cars-search-categories']/select[@name='categoryId']/optgroup[@label='Populair']/option")

for brand in brands:
    try:
        print(brand.text)
        select = Select(driver.find_element_by_name('categoryId'))
        select.select_by_visible_text(brand.text)
        wait_by_id("cars-search-models")
        models = driver.find_elements_by_xpath("//div[@id='cars-search-models']/select/option")
        for model in models:
            time.sleep(0.05)
            try:
                modelName = model.text
                if not model.text or model.text == "Model" or model.text == "Overige modellen":
                    continue

                print("- " + model.text)
                select = Select(driver.find_element_by_name('attributes'))
                select.select_by_visible_text(model.text)
                wait_by_id("cars-search-year-min")
                year_models = driver.find_elements_by_xpath("//div[@id='cars-search-year-min']/select/option")
                for year_model in year_models:
                    try:
                        modelName = model.text
                        if not year_model.text or year_model.text == "Bouwjaar (vanaf)":
                            continue
                        if int(year_model.text) < 2000:
                            break
                        print("-- " + year_model.text)
                        select = Select(driver.find_element_by_name('yearFrom'))
                        select.select_by_visible_text(year_model.text)
                        driver.find_element_by_xpath("//input[@id='cars-search-button']").click()
                        fetch_master_url(driver.current_url)
                    except Exception as e:
                        print e
                        continue
            except Exception as e:
                print e
                continue
    except Exception:
        print e
        continue

# fetch_master_url()
driver.quit()
time_end = time.time()
write()

print "Total runtime: " + str(time_end - time_beg) + " seconds"

# WRITE TO EXCEL AND RUN FOR ALL PAGES
