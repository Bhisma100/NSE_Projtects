import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import gspread
import datetime
import time

print('************** NSE Notification Batch *******************')

s = requests.Session()
header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
}
url = 'https://nsearchives.nseindia.com/content/RSS/Circulars.xml'
response = s.get(url,headers=header)
if response.status_code == 200:
    print(">>> Connection succesfull")

    # Getting data From XML
    soup = bs(response.content,features='xml')
    items = soup.find_all('item')
    Notifications =[]
    values_lists =[]
    for item in items:
        item_dict={
        'Date':item.find('pubDate').text[:15].strip(),
        'Title':item.find('title').text.strip(),
        'Link':item.find('link').text.strip()
        }
        Notifications.append([str(item_dict['Date']),str(item_dict['Title']),str(item_dict['Link'])])

    # Converting the data into PandasData Frame
    df = pd.DataFrame(Notifications,columns=['Date','Title','Link'])
    filter_df = df[df['Title'].str.contains('Listing of Equity|Listing of Sovereign Gold|Listing of units')]

    # Connecting to GoogleSheet Using googleAPI
    gc = gspread.service_account(filename=r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Python\Exchange Related task\NSE_Projtects\creds.json')
    spreadsheet_name = 'Notifications and Listings'
    sheet_name = 'NSE_Forthcoming_listing' 
    sh = gc.open(spreadsheet_name).worksheet(sheet_name)
    print(">>> Connected to GoogleSheet")
    
    # Deleting the existing data from the worksheet
    existing_data_range = sh.range('A2:E' + str(sh.row_count))
    for cell in existing_data_range:
        cell.value = ''

    sh.update_cells(existing_data_range)

    # Inserting the data in googleSheet
    df_dict = filter_df.to_dict(orient='records')
    for data in df_dict:
        values_lists.append([str(data['Date']), str(data['Title']), str(data['Link'])])
    sh.append_row([f'Batch ran at: {datetime.datetime.now()}'])
    sh.append_rows(values_lists)
    print(">>> Data Insersion succesfull")

    time.sleep(2)
    
    #for Log purpose 
    file = open(r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Logs\NSERSSFeed_Logs.txt','a')

    file.write(f"script ran at : {datetime.datetime.now()}\n")
        
else:
    print(f"Response code: {response.status_code}")



