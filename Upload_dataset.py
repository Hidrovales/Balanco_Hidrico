"""
Upload da base de dados.
Os dados são originais da plataforma Google Engine: "UCSB-CHG/CHIRPS/DAILY" e NASA POWER.
"""

import ee
import json
from ipygee import*
import pandas as pd
import numpy as np

def get_google_engine(latitude, longitude, start, end):
  ee_coord = ee.Geometry.Point([longitude,latitude])
  ref_coll = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")\
    .select('precipitation')\
    .filterBounds(ee_coord)\
    .filterDate(start, end)
  count = ref_coll.size()
  num_image = count.getInfo()
  coll_list = ref_coll.toList(num_image)
  values_output = []
  for i in range(0,num_image):
      img_temp = ee.Image(coll_list.get(i))
      dict = img_temp.reduceRegion(reducer = ee.Reducer.first(), geometry = ee_coord, scale = 2400)
      value_pixel = list(dict.getInfo().values())[0]  
      dates = ref_coll.aggregate_array('system:time_start').map(lambda d: ee.Date(d).format('YYYY-MM-dd')).sort()    
      values_output.append((dates, value_pixel))
  df_cols = ['DATA', 'P']
  df_ge = pd.DataFrame(values_output, columns = df_cols)
  df_ge = df_ge.drop(['DATA'], axis=1)
  return df_ge


def get_nasa_power(latitude, longitude, start, end):
  import os, json, requests

  base_url = r"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,T2MDEW,T2MWET,TS,T2M_RANGE,T2M_MAX,T2M_MIN&community=RE&longitude={longitude}&latitude={latitude}&start={start}&end={end}&format=JSON"
  api_request_url = base_url.format(longitude=longitude, latitude=latitude, start=start, end=end)

  response = requests.get(url=api_request_url, verify=True, timeout=30.00)
  content = json.loads(response.content.decode('utf-8'))
  dataset = convert_json_dataframe(content)
  return dataset


def convert_json_dataframe(file_json):
  import pandas as pd
  final_df = pd.DataFrame()
  df = pd.DataFrame(file_json['properties'])
  for i in range(7):
    new_df = pd.DataFrame(list(df['parameter'][i].items()),columns = ['DATA',df.index[i]])
    new_df = new_df.drop(['DATA'], axis=1)
    final_df = pd.concat([final_df, new_df], axis=1) 
  return final_df


def generate_date(start, number_of_days):
  import datetime
  date_list = []
  for day in range(number_of_days):
    a_date = (start + datetime.timedelta(days = day)).isoformat()
    date_list.append(a_date)
  date = pd.DataFrame(date_list,columns = ['DATA'])
  return date


def get_dataset(latitude, longitude, start, end):
  """
  Upload da base de dados
  :parâmetro latitude: latitude do local.
  :parâmetro longitude: longitude do local.
  :parâmetro start: data de início. Formato string = 'YYYY-MM-dd'
  :parâmetro end: data de final. Formato string = 'YYYY-MM-dd'. 
  :return: dataframe da base de dados
  """
  import datetime
  from datetime import timedelta  
  start_datetime = datetime.date(int(start[:4]), int(start[5:7]), int(start[8:]))
  end_datetime = datetime.date(int(end[:4]), int(end[5:7]), int(end[8:]))
  date_nasa_start = start[:4] + start[5:7] + start[8:]
  date_nasa_end = str(end_datetime + timedelta(days=-1))
  date_nasa_end = date_nasa_end[:4] + date_nasa_end[5:7] + date_nasa_end[8:]
  data_nasa = get_nasa_power(latitude, longitude, start = date_nasa_start, end = date_nasa_end)
  data_google = get_google_engine(latitude, longitude, start, end)
  date = generate_date(start=start_datetime, number_of_days = (datetime.datetime.strptime(end, "%Y-%m-%d").date() - datetime.datetime.strptime(start, "%Y-%m-%d").date()).days)
  dataset = pd.concat([date, data_google, data_nasa], axis=1) 
  return dataset
