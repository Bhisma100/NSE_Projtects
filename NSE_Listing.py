# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup as bs
import http.cookiejar
import requests
import datetime
import gspread
import time
import json
import pandas as pd
import hashlib
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
print('************** NSE Listing Batch *******************')
# Initialising Selenium
s = requests.Session()
cookie_jar = http.cookiejar.CookieJar()
s.cookies = cookie_jar
headernse ={
        'Accept':'*/*',
        'Accept-Encoding':'gzip, deflate, br, zstd',
        'Accept-Language':'en-US,en;q=0.9',
        'Referer':'https://www.nseindia.com/market-data/new-stock-exchange-listings-recent',
        'Sec-Ch-Ua':'"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform':'"Windows"',
        'Sec-Fetch-Mode':'cors',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
r = s.get('https://www.nseindia.com/',headers=headernse)
if r.status_code == 200:
    print(">>> Cookies has been Stored successfully")
else:
    print(">>> Problem with Cookie verification")

MaxRetry = 0
while True and MaxRetry <= 10 :
    try:
        # driver = webdriver.Chrome()
        # url = 'https://www.nseindia.com/market-data/new-stock-exchange-listings-recent'
        # print(">>> Opening page in Chrome")
        # driver.get(url)
        # time.sleep(5)
        # r = driver.page_source
        # Final_Table = []
        # DataInTable = []
        # driver.close()
        url = 'https://www.nseindia.com/api/new-listing-today?index=RecentListing'
        r = s.get(url,headers=headernse)
        print(f'Response from NSE is  = {r}')

        # Getting the Data From NSE
        # soup= bs(r,'html.parser')
        # # Getting the Data From NSE
        # soup= bs(r,'html.parser')
        # table = soup.find('div',{'class':'customTable-width tableWidth-1150 firstRow deque-table-sortable-group'})
        # for rows in table:
        #     row = rows.find_all('td')
        # for data in row:
        #     DataInTable.append(data.text)
        # for i in range(0,len(DataInTable),6):
        #     New=DataInTable[i:i+6]
        #     Final_Table.append(New)

        print(">>> Data has been fetched from NSE")

        gc = gspread.service_account(filename=r"C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Python\Keys and Passwords\GoogleCloud(Key)\creds.json")
        spreadsheet_name = 'Notifications and Listings'
        sheet_name = 'NSE_Listing'
        sh = gc.open(spreadsheet_name).worksheet(sheet_name)
        print(">>> Connected to GoogleSheet")

        # Filtering The data 
        # df = pd.DataFrame(Final_Table,columns=['Date','Market Type','Symbol','Company Name','Series','ISIN'])
        df = pd.DataFrame(r.json()['data'])
        NSE_Listing = df[df['series'].str.contains('EQ|ST|BE|MF|GB')]
        print(NSE_Listing)
        New_listingNew = r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Notifications and Listings\NSE_Listing1.csv'
        if os.path.exists(New_listingNew):
            os.remove(New_listingNew)
        New_listingOld = r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Notifications and Listings\NSE_Listing2.csv'
        NSE_Listing.to_csv(New_listingNew,index=False)
        hash_new = hashlib.sha256(open(New_listingNew,'rb').read()).hexdigest()
        with open(New_listingNew,'rb') as file:
            hash_new = hashlib.sha256(file.read()).hexdigest()
            file.close()
        hash_old = None
        if os.path.exists(New_listingOld):
            with open(New_listingOld,'rb') as f:
                hash_old = hashlib.sha256(f.read()).hexdigest()
                f.close()
            if hash_new != hash_old:
                os.remove(New_listingOld)
                os.rename(New_listingNew,New_listingOld)

                existing_data_range = sh.range('A2:L' + str(sh.row_count))
                for cell in existing_data_range:
                    cell.value = ''

                sh.update_cells(existing_data_range)
                print(">>> Existing data has been Deleted ")

                NSE_Listing.loc[:, 'listing_date'] = pd.to_datetime(NSE_Listing['listing_date'])
                values_lists = []
                df_dict = NSE_Listing.to_dict(orient='records')
                print(f">>> Number Rows to be Updated are: {len(df_dict)}")
                for data in df_dict:
                    values_lists.append([data['listing_date'].strftime('%Y-%m-%d'),str(data['instrument']), str(data['symbol']), str(data['name']),str(data['series']),str(data['isin'])])
                sh.append_row([f'Batch ran at: {datetime.datetime.now()}'])
                sh.append_rows(values_lists,value_input_option='USER_ENTERED') 
                print(f">>> New Data has been updated in the Sheet, Row = {len(values_lists)}")
                print(">>> Success")

                html_table = "<div style='text-align: center;'><h2>NSE Listing</h2></div>" + NSE_Listing.to_html(index=False)

                # Step 3: Compose Email
                with open(r"C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Python\Keys and Passwords\EmailandPassword\EmailCreds.json") as config_file:
                       config = json.load(config_file)
                sender_email = config['email_username']
                receiver_emails = config['email recievers']
                password = config['email_password']

                msg = MIMEMultipart('alternative')
                msg['From'] = sender_email
                msg['To'] = ', '.join(receiver_emails)
                msg['Subject'] = 'NSE New Listing'

                # Step 4: Attach HTML Tables
                msg.attach(MIMEText(html_table, 'html'))

                # Step 5: Send Email
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_emails, msg.as_string())

                print("Email sent successfully!")
                time.sleep(5)
                
                time.sleep(5)
            else:
                os.remove(New_listingNew)
                print('>>> No New Listing ******')
        else:
            os.rename(New_listingNew,New_listingOld)

        # gc = gspread.service_account(filename=r'C:\Users\Ashish Pal\Desktop\PrevousLapData\Ashish\Python\Exchange Related task\NSE_Projtects\creds.json')
        # spreadsheet_name = 'Notifications and Listings'
        # sheet_name = 'NSE_Listing'
        # sh = gc.open(spreadsheet_name).worksheet(sheet_name)
        # print(">>> Connected to GoogleSheet")

        # Deleting the existing data from Sheet
        # existing_data_range = sh.range('A2:L' + str(sh.row_count))
        # for cell in existing_data_range:
        #     cell.value = ''

        # sh.update_cells(existing_data_range)
        # print(">>> Existing Data has been deleted")
        # #Updating the Data in the sheet
        # filtered_df.loc[:, 'Date'] = pd.to_datetime(filtered_df['Date'])
        # values_lists = []
        # df_dict = filtered_df.to_dict(orient='records')
        # print(f">>> Number Rows to be Updated are: {len(df_dict)}")
        # for data in df_dict:
        #     values_lists.append([data['Date'].strftime('%Y-%m-%d'),str(data['Market Type']), str(data['Symbol']), str(data['Company Name']),str(data['Series']),str(data['ISIN'])])
        # sh.append_row([f'Batch ran at: {datetime.datetime.now()}'])
        # sh.append_rows(values_lists,value_input_option='USER_ENTERED') 
        # print(f">>> New Data has been updated in the Sheet, Row = {len(values_lists)}")
        # output = "Success"
        # print(f" >>> {output}")
        # time.sleep(5)

        break
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Retrying the script...")
        MaxRetry += 1
        

    