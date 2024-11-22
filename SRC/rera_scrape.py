import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import random
import base64
import os
from tqdm import tqdm
from glob import glob

if not os.path.isdir("../DATA/RERA"):
    os.makedirs("../DATA/RERA")

#URLS
base_rera_url = "https://maharera.maharashtra.gov.in/"
rera_orders_url = "https://maharera.maharashtra.gov.in/orders-judgements"

# Setup chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")

# Set path to chrome/chromedriver
chrome_options.binary_location = "../../chrome-linux64/chrome"
webdriver_service = Service("../../chromedriver-linux64/chromedriver")

## FUNCTIONS
# start a browser instance and get the maha rera home page
def browser_start():
    brow = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    brow.get(base_rera_url)
    time.sleep(random.randint(2,5))
    brow.get(rera_orders_url)
    time.sleep(random.randint(2,4))
    return brow

# search for RERA final orders
def search_orders(brow, complaint_type="rera", order_type="final", from_date="01-01-2020", to_date="31-12-2020"):
    acceptable_complaints = {"rera": "edit-order-complaint-type-rulings-of-maharera",
                             "ao": "edit-order-complaint-type-judgements-by-adjudicating-officers",
                             "non-reg": "edit-order-complaint-type-non-registration-rulings"}
    acceptable_order = {"interim":"edit-orders-judgements-type-59",
                        "final": "edit-orders-judgements-type-60",
                        "non-comp": "edit-orders-judgements-type-0"}
    try:
        brow.find_element(By.ID, acceptable_complaints[complaint_type]).click()
    except KeyError:
        print("Invalid complaint type")
    else:
        time.sleep(2)
        try:
            brow.find_element(By.ID, acceptable_order[order_type]).click()
        except KeyError:
            print("Invalid order type")
        else:
            time.sleep(2)
            try:
                fdate = brow.find_element(By.ID, "date4")
                fdate.clear()
                fdate.send_keys(from_date)
                time.sleep(2)
                tdate = brow.find_element(By.ID, "date")
                tdate.clear()
                tdate.send_keys(to_date)
                time.sleep(2)
                brow.find_element(By.ID, "edit-submit").click()
            except:
                print("Element error")
                raise
            else:
                total_results = brow.find_element(By.XPATH, "/html/body/div[2]/section[2]/div/div[2]/div/div[4]/div/div[2]/p/span")
                pages = int(total_results.text)//10 + 2
                return {"pages": pages, "from_date":from_date}

# download orders
def pdf_grab(brow, pages=10, from_date="01-01-2020"):
    fyear = from_date[-4:]
    if not os.path.isdir(f"../DATA/RERA/{fyear}"):
        os.makedir(f"../DATA/RERA/{fyear}")
    base_path = f"../DATA/RERA/{fyear}"
    for current_page in tqdm(range(1,pages)):
        purl = f"https://maharera.maharashtra.gov.in/orders-judgements?from_date=&to_date=&page={current_page}&op=Submit"
        brow.get(purl)
        time.sleep(random.randint(1,3))
        # locate all orders and complaint IDs
        order_elements = brow.find_elements(By.CLASS_NAME, "btn")
        case_ids = brow.find_elements(By.CLASS_NAME, "p-0")
        # iterate through list of orders
        for order, case_id in zip(tqdm(order_elements, leave=False), case_ids):
            pdf_b64 = order.get_attribute("oj-data") # base64 encoded pdf
            proj_name = order.get_attribute("oj-name")
            fname = case_id.text[1:]+"_"+re.sub("\W+","_", proj_name)
            if os.path.isfile(f"{base_path}/{fname}.pdf"): # if file exists move on the next
                continue
            else:
                with open(f"{base_path}/{fname}.pdf", "wb") as fwrite:
                    fwrite.write(base64.b64decode(pdf_b64)) # convert b64 to pdf and write file
                fwrite.close

# start Chrome Browser
browser = browser_start()
# search for orders
results = search_orders(brow=browser, complaint_type="rera", order_type="final", from_date="01-01-2020", to_date="31-12-2020")
# iterate through pages and grab orders
_ = pdf_grab(brow=browser, pages=results["pages"], from_date=results["from_date"])
