### PATH TO BROWSER
import httplib

path_to_browser = "/home/postsapien/scraper/mp_scraper/chromedriver"
# path_to_browser = "./chromedriver"
###
import hashlib
import urllib

from selenium import webdriver  # install selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select

import time
import os
from lxml import html  # install lxml

TIME_PAUSE = 2.0  # pause


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


def go_to_url(url):
    try:
        driver.get(url)
        return
    except Exception as e:
        print 'something went wrong while fetching ' + url + ' retrying...'
        time.sleep(TIME_PAUSE)
        go_to_url(url)


def wait_by_id(id_name):
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, id_name)))
        time.sleep(1.0)
    except TimeoutException:
        print "Too much time has passed."


def fetch_master_url(master_link, dir_name):
    print 'fetching url ' + master_link
    driver.get(master_link)  # get the first page
    print 'url loaded 1'
    wait_by_class("search-results-table")
    print 'url loaded 2'
    # first see the general page link and the number of pages
    general_page_link = master_link
    singlePage = False
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

        for elm in elements:
            print ("Element index " + str(elements.index(elm)))
            if 'url' not in elm:
                continue
            try:
                driver.get(elm['url'])
            except Exception as e:
                print e
                continue
            wait_by_id("vip-seller")

            image_paths = driver.find_elements_by_xpath(
                "//div[@id='vip-image-viewer']/div[contains(@class, 'image ')]/img")
            year = driver.find_element_by_xpath(
                "//div[@id='car-attributes']/div[contains(@class, 'car-feature-table spec-table')]/div/div[2]/span[2]").text
            new_dir_name = dir_name + "_" + year
            if not os.path.exists(new_dir_name):
                os.makedirs(new_dir_name)

            for i in image_paths:  # get images
                url = i.get_attribute('src')
                print url
                filename = url.split('/')[-1]
                extension = filename.split('.')[1].lower()
                new_filename = hashlib.md5(url.encode()).hexdigest() + "." + extension
                urllib.urlretrieve(i.get_attribute('src'), new_dir_name + "/" + new_filename)


options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(path_to_browser, chrome_options=options)
# driver.maximize_window()


# first handle cookies button
driver.get("https://www.marktplaats.nl/")
wait_by_class("page")
print "before click"

N_click_attempts = 0
while 1:
    if N_click_attempts == 10:
        print "Something is wrong. "
        break
    N_click_attempts = N_click_attempts + 1
    try:
        print "try to click."
        cook_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//form[@method='post']/input[@type='submit']"))).click()
        time.sleep(2.0)
    except Exception as e:
        print 'click failed '
        print e
        time.sleep(2.0)
        break

# cook_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//form[@method='post']/input[@type='submit']"))).click()
print "after click"
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

driver.set_page_load_timeout(360)
driver.get("https://www.marktplaats.nl/c/auto-s/c91.html")
wait_by_id("cars-search-categories")
min_year = 2000
brands = driver.find_elements_by_xpath(
    "//div[@id='cars-search-categories']/select[@name='categoryId']/optgroup[@label='Populair']/option")

brand_dict = {}
print 'loading options'

for brand in brands:
    try:
        if not brand.text:
            continue
        print brand.text
        brand_dict[brand.text] = []
        select = Select(driver.find_element_by_name('categoryId'))
        select.select_by_visible_text(brand.text)
        wait_by_id("cars-search-models")
        models = driver.find_elements_by_xpath("//div[@id='cars-search-models']/select/option")
        for model in models:
            time.sleep(0.005)
            try:
                if not model.text or model.text == "Model" or model.text == "Overige modellen":
                    continue
                print model.text
                brand_dict[brand.text].append(model.text)
            except Exception as e:
                print e
                print model.text
                continue
    except Exception as e:
        print e
        print brand.text
        continue

print 'options loaded'
for brand_key in brand_dict:
    print 'scraping brand ' + brand_key
    for model_name in brand_dict[brand_key]:
        print 'scraping model ' + model_name
        go_to_url("https://www.marktplaats.nl/c/auto-s/c91.html")
        wait_by_id("cars-search-categories")
        folder_name = 'data/' + brand_key + '_' + model_name
        print folder_name
        select_brand = Select(driver.find_element_by_name('categoryId'))
        select_brand.select_by_visible_text(brand_key)
        wait_by_id("cars-search-models")

        select_model = Select(driver.find_element_by_name('attributes'))
        select_model.select_by_visible_text(model_name)
        wait_by_id("cars-search-year-min")

        select_year = Select(driver.find_element_by_name('yearFrom'))
        select_year.select_by_visible_text(str(min_year))

        driver.find_element_by_xpath("//input[@id='cars-search-button']").click()
        try:
            fetch_master_url(driver.current_url, folder_name)
        except Exception as e:
            print 'could not fetch ' + folder_name
            print e
            continue

driver.quit()
time_end = time.time()

print "Total runtime: " + str(time_end - time_beg) + " seconds"

# WRITE TO EXCEL AND RUN FOR ALL PAGES
