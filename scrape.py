#%%

import pandas as pd
import time
import re
import numpy as np
from scipy.stats import norm, zscore
from functions import scrape, load_jsonl

# %%
#Get Initial Data
jsonl = load_jsonl('search_results_output.jsonl')
amazonData = pd.DataFrame(jsonl)
amazonData = amazonData[['title','url','price','rating','reviews']]

#bring in synonyms function?
# %%
#Data Cleaning
data = amazonData.drop_duplicates()
data["price"] = 0.95*pd.to_numeric(data["price"]
                                     .str.replace(r',','')
                                     .str.extract('(\d*\.?\d+)')[0]
                                     #.fillna(0.0)[0]
                                     , errors='coerce')

data["rating"] = pd.to_numeric(data["rating"]
                                     .str.replace(r',','')
                                     .str.extract('(\d*\.?\d+)')[0]
                                     #.fillna(0.0)[0]
                                     , errors='coerce')

data["reviews"] = pd.to_numeric(data["reviews"].str.replace(r',',''))#.fillna(0)

data["search"] = data["title"] + data["url"].str.replace(r'/',' ').str.replace(r'-',' ').str.replace(r'?',' ').str.replace(r'&',' ').str.replace(r'=',' ').str.rsplit('keyword', n=1).str.get(0)
data["search"] = data["search"].str.lower()

data["packsize"] = pd.to_numeric(data['search'].str.extract('(?:(\d+)[-\s]*[Pp]ack|(?:[Pp]ack|[Ss]et)\s?(?:of\s)?(\d+))').fillna(1.0)[0])

##Protocals
zigbee_search = '|'.join([f'(?i){i}' for i in ['zigbee']])
zwave_search = '|'.join([f'(?i){i}' for i in ['zwave','z-wave']])
wifi_search = '|'.join([f'(?i){i}' for i in ['wifi','wi-fi', 'mqtt', 'http']])

data['protocal_zigbee'] = data['search'].str.contains(zigbee_search, flags=re.IGNORECASE, regex=True)
data['protocal_zwave'] = data['search'].str.contains(zwave_search, flags=re.IGNORECASE, regex=True)
data['protocal_wifi'] = data['search'].str.contains(wifi_search, flags=re.IGNORECASE, regex=True)
data = data.loc[data['protocal_zigbee']+data['protocal_zwave']+data['protocal_wifi'] > 0 ]

def extract_protocal(row):
    for c in data[['protocal_zigbee','protocal_zwave', 'protocal_wifi']].columns:
        if row[c]==True:
            return c

data['protocal'] = data[['protocal_zigbee','protocal_zwave', 'protocal_wifi']].apply(extract_protocal, axis =1).str.replace(r'protocal_','')
data = data.drop(['protocal_zigbee','protocal_zwave', 'protocal_wifi'], axis=1)

##Sensors
temp_search = '|'.join([f'(?i){i}' for i in ['temp','temperature','heat','cold']])
motion_search = '|'.join([f'(?i){i}' for i in ['motion','movement','detection']])
humidity_search = '|'.join([f'(?i){i}' for i in ['humid','humidity']])
uv_search = '|'.join([f'(?i){i}' for i in ['uv','rays']])
lux_search = '|'.join([f'(?i){i}' for i in ['light sensor','light detection','lighting', 'lux', 'ulx', 'daylight', 'lumen']])
vibration_search = '|'.join([f'(?i){i}' for i in ['tamper','vibrate', 'vibration']])
plant_search = '|'.join([f'(?i){i}' for i in ['plant','soil', 'flower']])
door_search = '(?<!in|ut)door'

data['sense_temp'] = data['search'].str.contains(temp_search, flags=re.IGNORECASE, regex=True)
data['sense_motion'] = data['search'].str.contains(motion_search, flags=re.IGNORECASE, regex=True)
data['sense_humidity'] = data['search'].str.contains(humidity_search, flags=re.IGNORECASE, regex=True)
data['sense_uv'] = data['search'].str.contains(uv_search, flags=re.IGNORECASE, regex=True)
data['sense_light'] = data['search'].str.contains(lux_search, flags=re.IGNORECASE, regex=True)
data['sense_vibration'] = data['search'].str.contains(vibration_search, flags=re.IGNORECASE, regex=True)
data['sense_plant'] = data['search'].str.contains(plant_search, flags=re.IGNORECASE, regex=True)
data['sense_door'] = data['search'].str.contains(door_search, flags=re.IGNORECASE, regex=True)

#remove rows without sensors
data = data.loc[data['sense_temp']+data['sense_motion']+data['sense_humidity']+data['sense_uv']+data['sense_light']+data['sense_vibration']+data['sense_plant']+data['sense_door'] > 0 ]

#add useful summaries
data['total_sensors'] = data[[col for col in data.columns if col.startswith('sense_')]].sum(axis=1)

data['adjprice'] = data["price"]/data["packsize"]
data['pps'] = data['adjprice']/data['total_sensors']


data['sensors'] = data[[col for col in data.columns if col.startswith('sense_')]].eq(True).dot(data[[col for col in data.columns if col.startswith('sense_')]].columns+',').str[:-1].str.split().astype(str)
data['sensors'] = data['sensors'].str.replace(r'sense_','')

#remove bulbs and hubs and switches
data = data[~data.search.str.contains("(?i)bulb")]
data = data[~data.search.str.contains("(?i)switch")]
data = data[~(data.search.str.contains("(?i)hub") & ~data.search.str.contains("(?i)require"))] #keeps 'requires __ hub'

data = data.drop(['search'], axis=1)

data = data.fillna(data.mean()) 

data.to_csv('output.csv',index=False)
# %%
data.dtypes
# %%
