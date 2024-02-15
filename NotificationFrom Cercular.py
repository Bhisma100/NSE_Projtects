from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import gspread
from bs4 import BeautifulSoup as bs
import datetime
import pandas as pd
import json
import time

Sev_Day_Date = (datetime.datetime.now() - datetime.timedelta(days = 7)).strftime('%d-%m-%Y')
today_date = datetime.datetime.now().strftime('%d-%m-%Y')

print("*********************NSE Notification Batch *******************")
while True:
    try:
        url  = f'https://www.nseindia.com/api/circulars?fromDate={Sev_Day_Date}&toDate={today_date}'
        header = {
        'Accept':'*/*',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'en-US,en;q=0.6',
        'Sec-Ch-Ua':'"Not A(Brand";v="99", "Brave";v="121", "Chromium";v="121"',
        'Sec-Ch-Ua-Mobile':'?0',
        'Sec-Ch-Ua-Platform':'"Windows"',
        'Sec-Fetch-Dest':'empty',
        'Sec-Fetch-Mode':'cors',
        'Sec-Fetch-Site':'same-origin',
        'Sec-Gpc':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        for key, value in header.items():
            chrome_options.add_argument(f"{key}={value}")
        driver = webdriver.Chrome(options = chrome_options)
        driver.get('https://www.nseindia.com/resources/exchange-communication-circulars')
        driver.get(url)
        print(">>> fetching Data")
        page_source = driver.page_source
        time.sleep(1)
        driver.close()

        soup = bs(page_source,'html.parser')
        htmlsoup=(soup.find('pre')).string
        Data = json.loads(htmlsoup)
        temp1 = Data.get('data',[])
        Master_Data = pd.DataFrame(temp1)

        Master_Data = Master_Data[['cirDisplayDate','sub','circFilelink','circCategory','circDepartment']]
        filtered_df = Master_Data[Master_Data['sub'].str.contains('Listing of Equity|Listing of Sovereign Gold|Listing of units')]
        print(filtered_df)

        print(">>> Connecting with GoogleSheet")
        gc = gspread.service_account(filename=r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Python\Exchange Related task\NSE_Projtects\creds.json')
        spreadsheet_name = 'Notifications and Listings'
        sheet_name = 'NSE_Forthcoming_listing' 
        sh = gc.open(spreadsheet_name).worksheet(sheet_name)
        print(">>> Connection Successfull")
        existing_data_range = sh.range('A2:L' + str(sh.row_count))
        for cell in existing_data_range:
            cell.value = ''

        sh.update_cells(existing_data_range)

        print(">>> Inserting the Data ")
        values_lists =[]
        df_dict = filtered_df.to_dict(orient='records')
        for data in df_dict:
            values_lists.append([str(data['cirDisplayDate']), str(data['sub']), str(data['circFilelink']),str(data['circCategory']),str(data['circDepartment'])])
        sh.append_row([f'Batch ran at: {datetime.datetime.now()}'])
        sh.append_rows(values_lists)
        print(">>> Sucessfull ")
        time.sleep(5)

        break
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Retrying the script...")