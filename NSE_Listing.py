from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
import datetime
import gspread
import time
import pandas as pd
print('************** NSE Listing Batch *******************')
# Initialising Selenium
output = "Try Again"
while output == 'Try Again':
    driver = webdriver.Chrome()
    url = 'https://www.nseindia.com/market-data/new-stock-exchange-listings-recent'
    print(">>> Opening page in Chrome")
    driver.get(url)
    time.sleep(5)
    r = driver.page_source
    Final_Table = []
    DataInTable = []
    driver.close()

    # Getting the Data From NSE
    soup= bs(r,'html.parser')
    if any(table.get('id') == "livenltRecentTable" for table in soup.find_all('table')):
        table = soup.find('div',{'class':'customTable-width tableWidth-1150 firstRow deque-table-sortable-group'})
        for rows in table:
            row = rows.find_all('td')
        for data in row:
            DataInTable.append(data.text)
        for i in range(0,len(DataInTable),6):
            New=DataInTable[i:i+6]
            Final_Table.append(New)
        print(">>> Data has been fetched from NSE")

        # Filtering The data 
        df = pd.DataFrame(Final_Table,columns=['Date','Market Type','Symbol','Company Name','Series','ISIN'])
        filtered_df = df[df['Series'].str.contains('EQ|ST|BE|MF|GB')]
        print(filtered_df)

        gc = gspread.service_account(filename=r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Python\Exchange Related task\NSE_Projtects\creds.json')
        spreadsheet_name = 'Notifications and Listings'
        sheet_name = 'NSE_Listing'
        sh = gc.open(spreadsheet_name).worksheet(sheet_name)
        print(">>> Connected to GoogleSheet")

        # Deleting the existing data from Sheet
        existing_data_range = sh.range('A2:L' + str(sh.row_count))
        for cell in existing_data_range:
            cell.value = ''

        sh.update_cells(existing_data_range)
        print(">>> Existing Data has been deleted")
        #Updating the Data in the sheet
        filtered_df.loc[:, 'Date'] = pd.to_datetime(filtered_df['Date'])
        values_lists = []
        df_dict = filtered_df.to_dict(orient='records')
        print(f">>> Number Rows to be Updated are: {len(df_dict)}")
        for data in df_dict:
            values_lists.append([data['Date'].strftime('%Y-%m-%d'),str(data['Market Type']), str(data['Symbol']), str(data['Company Name']),str(data['Series']),str(data['ISIN'])])
        sh.append_row([f'Batch ran at: {datetime.datetime.now()}'])
        sh.append_rows(values_lists,value_input_option='USER_ENTERED') 
        print(f">>> New Data has been updated in the Sheet, Row = {len(values_lists)}")
        output = "Success"
        print(f" >>> {output}")
        time.sleep(5)
    else:
        driver.close()
        output = "Try Again"
        print(f">>> {output}")
        time.sleep(5)

    