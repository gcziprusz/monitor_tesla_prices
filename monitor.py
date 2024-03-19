import os
import requests
import smtplib
import json
import time
import urllib.parse
from email.mime.text import MIMEText
from datetime import datetime

MONITOR_SENDER_EMAIL = os.getenv('MONITOR_SENDER_EMAIL')
MONITOR_RECIPIENT_EMAIL = os.getenv('MONITOR_RECIPIENT_EMAIL')
MONITOR_EMAIL_PASSWORD = os.getenv('MONITOR_EMAIL_PASSWORD')
MONITOR_RECIPIENT_CC= os.getenv('MONITOR_RECIPIENT_CC')
MONITOR_PROCESSED_FILE=os.getenv('MONITOR_PROCESS_FILE')

def extract_vehicle_details(json_data):
    state = json_data.get("StateProvince", "")
    country = json_data.get("CountryCode", "")
    city = json_data.get("City", "")
    federal_incentives = json_data.get("FederalIncentives", {})
    year = json_data.get("Year", "")
    purchase_price = json_data.get("PurchasePrice", "")
    trim = json_data.get("TRIM", [])
    odometer = json_data.get("Odometer", "")
    vin = json_data.get("VIN", "")

    vehicle_details = {
        "State": state,
        "Country": country,
        "City": city,
        "FederalIncentives": federal_incentives,
        "Year": year,
        "TRIM": trim,
        "Odometer": odometer,
        "PurchasePrice":purchase_price,
        "Preview": f"https://www.tesla.com/m3/order/{vin}#overview"
    }

    return vehicle_details

def send_email(vehicle_details):
    subject = "Tesla Inventory Update"
    body = ""

    for obj in vehicle_details:
        for key, value in extract_vehicle_details(obj).items():
            body += f"{key}: {value}, \n"
        body = body.rstrip(", ")
        body += "\n"

    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = MONITOR_SENDER_EMAIL
    message['To'] = MONITOR_RECIPIENT_EMAIL
    message['Cc'] = MONITOR_RECIPIENT_CC

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(MONITOR_SENDER_EMAIL, MONITOR_EMAIL_PASSWORD)
        server.sendmail(MONITOR_SENDER_EMAIL, [MONITOR_RECIPIENT_EMAIL,MONITOR_RECIPIENT_CC], message.as_string())

def get_tesla_inventory():
    # AWD only!!!
    # "options": {
    #     "TRIM": ["PAWD", "LRAWD"]
    # },
    decoded_query = {
        "query": {
            "model": "m3",
            "condition": "used",
            "arrangeby": "Price",
            "order": "asc",
            "market": "US",
            "language": "en",
            "super_region": "north america",
            "lng": -86.91232169999999,
            "lat": 35.9953768,
            "zip": "37069",
            "range": 0,
            "region": "TN"
        },
        "offset": {},
        "count": 50,
        "outsideOffset": 0,
        "outsideSearch": True,
        "isFalconDeliverySelectionEnabled": False,
        "version": None
    }

    encoded_query = urllib.parse.urlencode({"query": json.dumps(decoded_query)})
    url = 'https://www.tesla.com/inventory/api/v4/inventory-results?' + encoded_query

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,hu;q=0.8',
        'referer': 'https://www.tesla.com/inventory/used/m3?TRIM=PAWD,LRAWD&arrangeby=plh&zip=37069',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0'
    }

    offset = 0
    results = []

    while True:
        response = requests.get(url.format(offset), headers=headers, timeout=30)
        data = response.json()
        total_matches_found = int(data.get('total_matches_found', 0))
        vehicles = data.get('results', [])

        results.extend(vehicles)

        offset += len(vehicles)

        time.sleep(2)
        if offset >= total_matches_found:
            break
    return results

sent_emails = {}

def check_inventory():
        vehicles = get_tesla_inventory()
        vehicle_details = []
        for vehicle in vehicles:
            vin = str(vehicle['VIN'])
            purchase_price = str(vehicle['PurchasePrice'])
            federal_incentives =vehicle.get("FederalIncentives", {})
            is_tax_incentive_eligible = bool(federal_incentives.get("IsTaxIncentiveEligible", "False"))
            if (vin, purchase_price) not in sent_emails and is_tax_incentive_eligible:
                vehicle_details.append(vehicle)
                sent_emails[(vin, purchase_price)] = True

                with open(MONITOR_PROCESSED_FILE, 'a') as f:
                    f.write(f"{vin},{purchase_price}\n")

        if vehicle_details:
            send_email(vehicle_details)
        else:
            print(datetime.now(),"No new inventory")

def bootstrap_existing_cars():
    with open(MONITOR_PROCESSED_FILE, 'r') as file:
        for line in file:
            vin, purchase_price = line.strip().split(',')
            sent_emails[(vin, purchase_price)] = True

def main():
    bootstrap_existing_cars()
    print(datetime.now(),"Checking inventory")
    check_inventory()

if __name__ == "__main__":
    main()
