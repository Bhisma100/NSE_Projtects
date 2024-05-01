# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
import requests
import http.cookiejar
import gspread
# from bs4 import BeautifulSoup as bs
import datetime
import pandas as pd
import json
import hashlib
import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

Sev_Day_Date = (datetime.datetime.now() - datetime.timedelta(days = 7)).strftime('%d-%m-%Y')
today_date = datetime.datetime.now().strftime('%d-%m-%Y')
s = requests.Session()
cookie_jar = http.cookiejar.CookieJar()
s.cookies = cookie_jar

MaxRetry = 0
print("*********************NSE Notification Batch *******************")
while True and MaxRetry < 10:
    try:
        url  = f'https://www.nseindia.com/api/circulars?fromDate={Sev_Day_Date}&toDate={today_date}'
        headernse ={
        'Accept':'*/*',
        'Accept-Encoding':'gzip, deflate, br, zstd',
        'Accept-Language':'en-US,en;q=0.9',
        'Referer':'https://www.google.com/',
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

        # chrome_options = Options()
        # chrome_options.add_argument('--headless')
        # for key, value in header.items():
        #     chrome_options.add_argument(f"{key}={value}")
        # driver = webdriver.Chrome(options = chrome_options)
        # driver.get('https://www.nseindia.com/resources/exchange-communication-circulars')
        # driver.get(url)
        # time.sleep(1)
        # print(">>> fetching Data")
        # page_source = driver.page_source
        # driver.close()

        # soup = bs(page_source,'html.parser')
        # htmlsoup=(soup.find('pre')).string
        # Data = json.loads(htmlsoup)
        # temp1 = Data.get('data',[])
        r = s.get(url,headers=headernse)
        Master_Data = pd.DataFrame(r.json()['data'])
        Master_Data = Master_Data[['cirDisplayDate','sub','circFilelink','circCategory','circDepartment']]
        Master_Data.loc[:,'cirDisplayDate'] = pd.to_datetime(Master_Data['cirDisplayDate'])

        print(">>> Connecting with GoogleSheet")
        gc = gspread.service_account(filename=r"C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Python\Keys and Passwords\GoogleCloud(Key)\creds.json")
        spreadsheet_name = 'Notifications and Listings'
        sheet_name = 'NSE_Forthcoming_listing' 
        sh = gc.open(spreadsheet_name).worksheet(sheet_name)
        print(">>> Connection Successfull")

        # New Listing
        NSEFortList = Master_Data[Master_Data['sub'].str.contains('Listing of Equity|Listing of Sovereign Gold|Listing of units')]
        print(NSEFortList)
        Forth_pathNew = r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Notifications and Listings\NSE_Fortlisting1.csv'
        if os.path.exists(Forth_pathNew):
            os.remove(Forth_pathNew)
        Forth_pathOld = r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Notifications and Listings\NSE_Fortlisting2.csv'
        NSEFortList.to_csv(Forth_pathNew,index=False)
        hash_new = hashlib.sha256(open(Forth_pathNew, 'rb').read()).hexdigest()

        NSEChanges = Master_Data[Master_Data['sub'].str.contains('Change in|Name Change|Symbol Change|Symbol|name|Name')]
        print(NSEChanges)
        ChangesPathNew = r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Notifications and Listings\NSEChanges1.csv'
        if os.path.exists(ChangesPathNew):
            os.remove(ChangesPathNew)
        ChangesPathold = r'C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Notifications and Listings\NSEChanges2.csv'
        NSEChanges.to_csv(ChangesPathNew,index=False)
        hash_newc = hashlib.sha256(open(ChangesPathNew, 'rb').read()).hexdigest()

        if os.path.exists(Forth_pathOld) and os.path.exists(ChangesPathold):
            with open(Forth_pathOld, 'rb') as f:
                hash_old = hashlib.sha256(f.read()).hexdigest()
            with open(ChangesPathold, 'rb') as fc:
                hash_oldc = hashlib.sha256(fc.read()).hexdigest()
            if hash_new!= hash_old or hash_newc!= hash_oldc :
                os.remove(Forth_pathOld)
                os.rename(Forth_pathNew,Forth_pathOld)
                os.remove(ChangesPathold)
                os.rename(ChangesPathNew,ChangesPathold)
                existing_data_range = sh.range('A2:L' + str(sh.row_count))
                for cell in existing_data_range:
                    cell.value = ''

                sh.update_cells(existing_data_range)
                print(">>> Existing data has been Deleted ")

                values_lists1 =[]
                values_lists =[]
                df_dict = NSEFortList.to_dict(orient='records')
                df_dict1 = NSEChanges.to_dict(orient='records')
                for data1 in df_dict1:
                    values_lists1.append([data1['cirDisplayDate'].strftime('%Y-%m-%d'), str(data1['sub']), str(data1['circFilelink']),str(data1['circCategory']),str(data1['circDepartment'])])
                for data in df_dict:
                    values_lists.append([data['cirDisplayDate'].strftime('%Y-%m-%d'), str(data['sub']), str(data['circFilelink']),str(data['circCategory']),str(data['circDepartment'])])
                sh.append_row([f'Batch ran at: {datetime.datetime.now()}'])
                sh.append_row(['Forthcoming Listing'])
                sh.append_rows(values_lists,value_input_option='USER_ENTERED')
                sh.append_row([f'Changes in Securities'])
                sh.append_rows(values_lists1,value_input_option='USER_ENTERED')
                print(">>> Sucessfull ")

                #Email trigger

                html_table1 = "<div style='text-align: center;'><h2>NSE Forthcoming Listing</h2></div>" + NSEFortList.to_html(index=False)
                html_table2 = "<div style='text-align: center;'><h2>NSE Changes in Securities</h2></div>" + NSEChanges.to_html(index=False)

                # Step 3: Compose Email
                with open(r"C:\Users\Ashish Kumar Pal\OneDrive\Desktop\Python\Keys and Passwords\EmailandPassword\EmailCreds.json") as config_file:
                    config = json.load(config_file)
                sender_email = config['email_username']
                receiver_emails = config['email recievers']
                password = config['email_password']
    
                msg = MIMEMultipart('alternative')
                msg['From'] = sender_email
                msg['To'] = ', '.join(receiver_emails)
                msg['Subject'] = 'NSE Notifications and Listing'

                # Step 4: Attach HTML Tables
                html_content = html_table1 + html_table2
                msg.attach(MIMEText(html_content, 'html'))

                # Step 5: Send Email
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_emails, msg.as_string())

                print("Email sent successfully!")

                # NSEFortList.loc[:,'cirDisplayDate'] = pd.to_datetime(NSEFortList['cirDisplayDate'])
                # values_lists =[]
                # df_dict = NSEFortList.to_dict(orient='records')
                # for data in df_dict:
                #     values_lists.append([data['cirDisplayDate'].strftime('%Y-%m-%d'), str(data['sub']), str(data['circFilelink']),str(data['circCategory']),str(data['circDepartment'])])
                # sh.append_row([f'Batch ran at: {datetime.datetime.now()}'])
                # sh.append_row(['Forthcoming Listing'])
                # sh.append_rows(values_lists,value_input_option='USER_ENTERED')
                # print(f">>> New NSE Listing has been updated in the Sheet, Rows = {len(values_lists)}")
                # var = 1

            else:
                os.remove(Forth_pathNew)
                os.remove(ChangesPathNew)
                print("No New Fothcoming Listing")
                print("No New Changes")
        else:
            os.rename(Forth_pathNew,Forth_pathOld)
            os.rename(ChangesPathNew,ChangesPathold)
        
        # NSEChanges = Master_Data[Master_Data['sub'].str.contains('Change in|Name Change|Symbol Change|Symbol|name|Name')]
        # print(NSEChanges)
        # ChangesPathNew = r'C:\Users\Ashish Pal\Desktop\Notifications and Listings\NSEChanges1.csv'
        # if os.path.exists(ChangesPathNew):
        #     os.remove(ChangesPathNew)
        # ChangesPathold = r'C:\Users\Ashish Pal\Desktop\Notifications and Listings\NSEChanges2.csv'
        # NSEChanges.to_csv(ChangesPathNew,index=False)
        # hash_newc = hashlib.sha256(open(ChangesPathNew, 'rb').read()).hexdigest()
        # hash_oldc = None
        # if os.path.exists(ChangesPathold):
        #     with open(ChangesPathold, 'rb') as f:
        #         hash_oldc = hashlib.sha256(f.read()).hexdigest()
        #         f.close()
        #         if hash_newc!= hash_oldc or var == 1:
        #             os.remove(ChangesPathold)
        #             os.rename(ChangesPathNew,ChangesPathold)

        #             NSEChanges.loc[:,'cirDisplayDate'] = pd.to_datetime(NSEChanges['cirDisplayDate'])
        #             values_lists1 =[]
        #             df_dict1 = NSEChanges.to_dict(orient='records')
        #             for data1 in df_dict1:
        #                 values_lists1.append([data1['cirDisplayDate'].strftime('%Y-%m-%d'), str(data1['sub']), str(data1['circFilelink']),str(data1['circCategory']),str(data1['circDepartment'])])
        #             sh.append_row([f'Changes in Securities'])
        #             sh.append_rows(values_lists1,value_input_option='USER_ENTERED')
        #             print(f">>> New NSE Changes has been updated in the Sheet, Rows = {len(values_lists1)}")
        #         else:
        #             os.remove(ChangesPathNew)
        #             print("Nothing New change in Securities")
        # else:
        #     os.rename(ChangesPathNew,ChangesPathold)



        # print(">>> Connecting with GoogleSheet")
        # gc = gspread.service_account(filename=r'C:\Users\Ashish Pal\Desktop\PrevousLapData\Ashish\Python\Exchange Related task\NSE_Projtects\creds.json')
        # spreadsheet_name = 'Notifications and Listings'
        # sheet_name = 'NSE_Forthcoming_listing' 
        # sh = gc.open(spreadsheet_name).worksheet(sheet_name)
        # print(">>> Connection Successfull")
        # existing_data_range = sh.range('A2:L' + str(sh.row_count))
        # for cell in existing_data_range:
        #     cell.value = ''

        # sh.update_cells(existing_data_range)

        # print(">>> Inserting the Data ")
        # filtered_df1 = Master_Data[Master_Data['sub'].str.contains('Change in|Name Change|Symbol Change|Symbol|name|Name')]
        
        # Change In anything Securities
        # filtered_df1.loc[:,'cirDisplayDate'] = pd.to_datetime(filtered_df1['cirDisplayDate'])
        # values_lists1 =[]
        # df_dict1 = filtered_df1.to_dict(orient='records')
        # for data1 in df_dict1:
        #     values_lists1.append([data1['cirDisplayDate'].strftime('%Y-%m-%d'), str(data1['sub']), str(data1['circFilelink']),str(data1['circCategory']),str(data1['circDepartment'])])
        # filtered_df.loc[:,'cirDisplayDate'] = pd.to_datetime(filtered_df['cirDisplayDate'])
        # values_lists =[]
        # df_dict = filtered_df.to_dict(orient='records')
        # for data in df_dict:
        #     values_lists.append([data['cirDisplayDate'].strftime('%Y-%m-%d'), str(data['sub']), str(data['circFilelink']),str(data['circCategory']),str(data['circDepartment'])])
        # sh.append_row([f'Batch ran at: {datetime.datetime.now()}'])
        # sh.append_row(['Forthcoming Listing'])
        # sh.append_rows(values_lists,value_input_option='USER_ENTERED')
        # sh.append_row([f'Changes in Securities'])
        # sh.append_rows(values_lists1,value_input_option='USER_ENTERED')
        # print(">>> Sucessfull ")
        time.sleep(5)

        break
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Retrying the script...")
        MaxRetry += 1