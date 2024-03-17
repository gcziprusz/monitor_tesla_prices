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
        'cookie':'_gcl_au=1.1.903473271.1707947758; ip_info={"ip":"76.18.165.47","location":{"latitude":35.9787,"longitude":-86.9134},"region":{"longName":"Tennessee","regionCode":"TN"},"city":"Franklin","country":"United States","countryCode":"US","postalCode":"37069"}; optimizelyEndUserId=oeu1708115171767r0.6417274056577873; coin_auth_inventory=8204972b674e7f9518f85813736ed9a1; _gid=GA1.2.1599164160.1710585472; _clck=ecnmgf%7C2%7Cfk5%7C0%7C1505; ak_bmsc=2712452CCB22B0AE002434022BC5D888~000000000000000000000000000000~YAAQIErcF1W4Yi2OAQAApJkXShdMnBRiXifgmsdpfD4h3S8kGCOYSqZRXrmeUtaBXE9C62Ovzgbze/FAKQuXXebXrTIdfFw6yqYVy21v29RQ6p36+trCKvl0OIu2gVdwok2WalZy+FWcBZ/Ud/u3a8F+yMNmug5m2JoxplO1FYKJBakKW5382tKmGoI8stANkaYyIKcbqcWL47IL0PNIUk1fojVRLbjS0Hptx0ALWCBiYV04LykeAq9DkTZcP03GcIfWJa049Qb+ck3Z8Hpwuiyp57U6nJ9UdRwqZ0ADmgCDTk7IJVn4HABhg1ArXByAvRZ6+68c3jcaZMGrjEPVgRbbqW9ETb1J97J6T0qGualAry5Q4yAGg8m32FYFgC1+4dvdOczgre0BjrQ7bu/vjEgObeGUOzSZpgmSrkpukX9Uhk2y39Ybp8Qq/+UG9OXqRW3dCsNk2uj37Gc=; oxpOriUrl=https%3A%2F%2Fwww.tesla.com%2Fteslaaccount; bm_sz=6E851A5B3CF934043BECDD6BF889854D~YAAQIErcF5G6Yi2OAQAAeK0XShdVBjx9NzlL5U+JIjhd/sjMGkYLQUjdSLcn+0VzS9njZVkYqkdBpvt/2iVOVjrID2ONOudmzAyNWzGXgtTvdWQDTW8eZ8Gf1CUtj2Yv1J3dazkfB/3MrRoKzafAewRny4hmkXgliPd19lF6a8kVED3rwHcf7t6rfbjLeoRSL+jpDKgw/i6Y78GQi/SdXBFXZtkR2YR/Pvb6s7mbG8VR3jEHYo61SHQ5o7BQMTlqoFjucGtRu5/O+Ku8yD7QcqLFK7u2b9juPA7+Bpc3krMPiuMpNGdr9pcJ7oyhvjO3orw6Mxgs84z/ft9Npd+8+JmEJLfxDa0hPSlMmuMmgTwcMj07XQ==~4600643~4599878; _abck=A21BCB603C79683528A29ADE6360AE58~-1~YAAQIErcF0e7Yi2OAQAAZrYXSguyRSA88DmCU3VJtGKgVe/MhiA2/pvESxFT4G7lKWY5+eQxCcWcUryk4HODeiwCZKGYTX10yiqPrjUD8noJPAJ7hl8a8li6DjYahM5CWcqUlQ+DmWhZueN6QLtEZUcJWXgU6NZGwDd/KY6kMUdOw/lF6tRUnriV57qFFLvriA1aYbpQvF9a+mEFFkQoKp3TUgq0pcF2a+0xyXLlGehuLO4s323ILSdN46pH65k6Od4JAtB6ZDO3EpchS2UHdAolOPPeGEQXhgFZBvP/wXmK7uWM4QlqHZzgB17lj3sXMfWvnaOshf8LhgKtZX775rAxZHuG0ZsDTEOBZOcDcvjnkVQ1WBjLFccHlSTNHtvupEsP5jE3e93RPA==~-1~-1~-1; _gat_UA-9152935-1=1; _ga_2RWV2RY971=GS1.1.1710640043.14.1.1710640154.0.0.0; _ga_KFP8T9JWYJ=GS1.1.1710640043.14.1.1710640154.49.0.0; _ga=GA1.2.653667591.1707947758; _uetsid=3dd455c0e38111ee95ba6fd22857cb40; _uetvid=1a5dc57084a111eeb230099573007ebc; cua_sess=0975ce964b8270ec8be636cfe8ff324d; _clsk=kddyru%7C1710640155073%7C3%7C1%7Ck.clarity.ms%2Fcollect; bm_sv=84088F2D683928B27E5405E5C5C8D37A~YAAQIErcFzLSYi2OAQAAxEoZShc0e1zLnEntGfzjadkiU6NNIk+OnpBBkIg6M8Ao5ftpNghG3SR5sJE8HxrxUzfYaaPtBNpQynfpHG/Yyaz2hZxjrjWIia5RsBtJlyKGut3JZ5uHqRRAPIZ3jFzxkm8xkFTEtpdm9L7aw/aRBGAa6SiUCeY6Cp4UuxiF4YFnFEtWraW6TWP6Yug7y1Q4Jgt6qZVx3aC9LVbz0gha8rqIR3ngrDCP7p7O2sEPwkMo~1',
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
