"""
Funções para ajustar a base de dados nos padrões do FAO 56.
"""
import numpy as np
import math
import pandas as pd
from datetime import datetime

def conversao_U2(dataset):
    """
    Conversão da velocidade do vento medida a 10m para 2m com limite de 0.5 m/s
    Equação 47 (FAO 56)
    :param dataset: coluna de dados de velocidade do vento

    """
    for i in range(dataset.shape[0]-1): 
      if np.isnan(dataset.loc[i]) == False:
        dataset.loc[i] = dataset.loc[i] * (4.87 / math.log(67.8 * 10 - 5.42)) 
        if dataset.loc[i] < .5:
          dataset.loc[i] = .5
          
    return dataset
  
def completa_U2(dataset):
    """
      Completa dados faltantes de Velocidade do vento, inserindo 2 m/s.
      :param dataset: coluna de dados de velocidade do vento

    """
    for i in range(dataset.shape[0]-1): 
      if np.isnan(dataset.loc[i]):
        dataset.loc[i] = 2
    return dataset
  

def interpola_Temperatura(dataset_Tmax, dataset_Tmin):
    """
    Completa a base de dados em caso de dados faltantes de Temperatura máxima, mínima e média.
    :param dataset_Tmax: coluna de dados com Temperatura máxima.
    :param dataset_Tmin: coluna de dados com Temperatura mínima.
    :return: coluna de dados com Temperatura máxima, mínima e média.
    """
    dataset_Tmax = dataset_Tmax.interpolate(axis = 0)
    dataset_Tmin = dataset_Tmin.interpolate(axis = 0)
    dataset_Tmean = (dataset_Tmax + dataset_Tmin)/2
    
    return dataset_Tmax, dataset_Tmin, dataset_Tmean
  
  
def calcula_dia(dataset):
    """
      Calcula dia do ano e acrescenta na base de dados
      :param dataset: base de dados completa
      :return: base de dados + coluna com o dia do ano
    """
    date = dataset[:,1]
    day_of_year = []
    for i in range(date.shape[0]):
      adate = datetime.strptime(date[i],"%Y-%m-%d")
      day_of_year.append(adate.timetuple().tm_yday)
    day = np.asarray(day_of_year)
    dayframe=pd.DataFrame(day,columns=['J'])
    d = [dataset,dayframe]
    dataset = pd.concat(d,axis=1)
    return dataset
