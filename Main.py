import subprocess
import sys
import requests
import logging
import json
import os
import env
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import TimeoutException

# Environment Variables
SKU = sys.argv[1]
URL = sys.argv[2]
EMAIL = os.getenv("BB_EMAIL")
PASSWORD = os.getenv("BB_PASSWORD")
API_KEY = os.getenv("BB_API_KEY")
PRODUCT_LINK = os.getenv("BB_URL")
CC_CARD_NUM = os.getenv("CC_CARD_NUM")
CC_CARD_NAME = os.getenv("CC_CARD_NAME")
CC_CVV = os.getenv("CC_CVV")
CC_EXP_DATE = os.getenv("CC_EXP_DATE")
STREET_ADDR = os.getenv("STREET_ADDR")
CITY = os.getenv("CITY")
STATE = os.getenv("STATE")
ZIP_CODE = os.getenv("ZIP_CODE")

# Logging Initialization
log_format = ('[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')
logging.basicConfig(
    level=logging.INFO,
    format=log_format
)
logger = logging.getLogger(__name__)

# Selenium Driver
driver = webdriver.Firefox()

ORDER_SUCCESSFUL = False


def login():
    sign_in_url = 'https://www.bestbuy.com/signin'
    driver.get(sign_in_url)

    # fill in email and password
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "fld-e"))
    )
    email_field.send_keys(EMAIL)

    pw_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "fld-p1"))
    )
    pw_field.send_keys(PASSWORD)

    # click sign in button
    sign_in_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "/html/body/div/div/section/main/div/div/div/div/div/div/form/div[4]/button"))
    )
    sign_in_btn.click()
    logger.info("Signing in...")


def close_modal():
    try:
        close_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/main/div[2]/div[5]/div/div/div/div/div/div/div/button"))
        )
        logger.info("Close modal button found...")
        close_btn.click()

    except (NoAlertPresentException, TimeoutException) as py_ex:
        logger.error("Failed while waiting close modal button: Alert not present!")
        logger.error(py_ex)
        logger.error(py_ex.args)


def go_to_product():
    driver.get(URL)


def query_availability_api():
    url = f'https://api.bestbuy.com/v1/products(sku={SKU})?apiKey={API_KEY}&facet=onlineAvailability,1&format=json'

    query_count = 0
    is_available = False
    while not is_available:
        time.sleep(0.5)
        query_count += 1
        response = requests.get(url)
        if response.status_code == 200:
            is_available = response.json()["products"][0]["onlineAvailability"]
            logger.info(f'Available: {is_available} (Query {query_count})')
        else:
            logger.info(f'Received non-200 response: Status [{response.status_code}]\n{response.json()}')


def execute_purchase():
    add_to_cart()
    checkout()


def add_to_cart():
    add_button_available = False
    while not add_button_available:
        # find add to cart button
        try:
            atc_btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".add-to-cart-button"))
            )
            logger.info("Add to cart button found, adding to cart and navigating there...")
            add_button_available = True
            atc_btn.click()
            driver.get("https://www.bestbuy.com/cart")

        except (NoAlertPresentException, TimeoutException) as py_ex:
            logger.error("Not available: No Add-to-cart button found. Refreshing and retrying...")
            driver.refresh()
            continue


def checkout():
    clicked_checkout_button = False
    while not clicked_checkout_button:
        try:
            checkout_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                    "/html/body/div/main/div/div[2]/div/div/div/div/section[2]/div/div/div[3]/div/div/button"))
            )
            logger.info("Checking out...")
            checkout_btn.click()
            clicked_checkout_button = True
            fill_in_cvv()
            place_order()

        except (NoAlertPresentException, TimeoutException) as py_ex:
            logger.error("Failed while waiting for checkout button: Alert not present!")
            logger.error(py_ex)
            logger.error(py_ex.args)
            continue


def fill_in_cvv():
    filled_out_cvv = False
    while not filled_out_cvv:
        try:
            cvv_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "credit-card-cvv"))
            )
            logger.info("Filling in credit card CVV...")
            cvv_field.send_keys(CC_CVV)
            filled_out_cvv = True

        except (NoAlertPresentException, TimeoutException) as py_ex:
            logger.error("Failed while waiting CVV field: Alert not present!")
            logger.error(py_ex)
            logger.error(py_ex.args)
            continue


def place_order():
    placed_order = False
    while not placed_order:
        try:
            place_order_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".button__fast-track"))
            )
            logger.info("Placing order...")
            place_order_btn.click()
            placed_order = True

        except (NoAlertPresentException, TimeoutException) as py_ex:
            logger.error("Failed while clicking 'Place Order' button: Alert not present!")
            logger.error(py_ex)
            logger.error(py_ex.args)
            continue


def main():
    logger.info(f'Using URL: {URL}')
    logger.info(f'Using SKU: {SKU}')
    login()
    close_modal()
    go_to_product()
    # query_availability_api()  # Reaches daily limit quickly
    execute_purchase()


if __name__ == '__main__':
    main()

