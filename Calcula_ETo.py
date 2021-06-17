"""
Gera série temporal de Evapotranspiração de Referência
Referência: FAO 56 (2006)
Dados climáticos usados como entrada:
- Temperaturas (máxima, mínima e média) do ar em °C - Tmax, Tmin e Tmean
- Umidade Relativa Média - RH
- Insolação em Horas - I
- Velocidade do vento em m/s - U2
- Dia do ano - J
Dados da estação meteorológica usados como entrada:
Latitude em radianos
Altitude em metros
Constante Solar é de 0.0820  MJ m−2 min−1 
Constante de Stefan Boltzmann é de 0.000000004903  MJ m−2 dia−1
Fluxo de calor do solo (G) para o período de 1 dia ou 10 dias = 0
"""

import pandas as pd
import math
import numpy as np
from datetime import datetime

def Pressao_atm(altitude):
    """
    Pressão Atmosférica (P): Equação 7 (FAO 56)
    :parâmetro altitude: altitude acima do nível do mar [m]
    :return: pressão atmosférica [kPa]
    """
    tmp = (293.0 - (0.0065 * altitude)) / 293.0
    return math.pow(tmp, 5.26) * 101.3
    
def psicrometrica(pressao_atm):
    """
    Constante Psicrométrica ( γ ): Equação 8 (FAO 56, 2006)
    :parâmetro pressao_atm: pressão atmosférica [kPa]. Estimada pela função pressao_atm().
    :return: Constante psicrométrica [kPa C-1].
    """
    return 0.000665 * pressao_atm
    
def Es(t):
    """
    Pressão de vapor saturado médio ( es ) à temperatura do ar: Equação 11 (FAO 56)
    :parâmetro t: temperatura [C]
    :return: pressão de vapor saturado [kPa]
    """
    return 0.6108 * math.exp((17.27 * t) / (t + 237.3))
    
def Es_medio(tmin, tmax):
    """
    :parâmetro tmin: temperatura mínima [C]
    :parâmetro tmax: temperatura máxima [C]
    :return: pressão média de vapor saturado [kPa]
    """
    return (Es(tmin) + Es(tmax)) / 2.0
    
def Delta(tmedia):
    """
    Declividade da curva de pressão do valor de saturação ( Δ ): Equação 13 (FAO 56)
    :parâmetro t: Temperatura média [C].
    :return: declividade da curva de pressão do valor de saturação [kPa C-1]
    """
    tmp = 4098 * (0.6108 * math.exp((17.27 * tmedia) / (tmedia + 237.3)))
    return tmp / math.pow((tmedia + 237.3), 2)

def Ea(tmin, tmax, RH):
    """
    Pressão de vapor atual ( ea ) usando umidade relativa média ( RH ): Equação 19 (FAO 56)
    OBS: em caso de ausência de RH, será usada a Equação 48 (FAO 56)
    :parâmetro tmin: temperatura mínima [C]
    :parâmetro tmax: temperatura máxima [C]
    :parâmetro RH: umidade relativa média [%]
    :return: pressão de vapor atual [kPa]
    """
    if np.isnan(RH):
        ea = 0.611 * math.exp((17.27 * tmin) / (tmin + 237.3))
    else:
        ea = (RH * Es_medio(tmax,tmin))/ 100.0
    return ea
    
def Ra(latitude, declinacao_sol, omega, dr, Gsc):
    """
    Radiação extraterrestre para períodos diários ( Ra ): Equação 21 (FAO 56)
    :parâmetro latitude: latitude [rad]
    :parâmetro declinacao_sol: declinação do sol [rad]. Calculada pela função declinacao_sol().
    :parâmetro omega: ângulo horário pôr-do-sol [rad]. Calculado pela função omega().
    :parâmetro dr: inverso da distância relativa da terra-sol. Calculada pela função dr().
    :return: Radiação extraterrestre para períodos diários [MJ m-2 day-1]
    """

    tmp1 = (24.0 * 60.0) / math.pi
    tmp2 = omega * math.sin(latitude) * math.sin(declinacao_sol)
    tmp3 = math.cos(latitude) * math.cos(declinacao_sol) * math.sin(omega)
    return tmp1 * Gsc * dr * (tmp2 + tmp3)
    
def Declinacao_sol(J):
    """
    :parâmetro J: dia do ano, inteiro de 1 a 365 ou 366.
    :return: declinação solar [rad]
    """
    return float(0.409) * math.sin(((float(2.0) * math.pi / float(365.0)) * J - float(1.39)))
    
def Omega(latitude, declinacao_sol):
    """
    :parâmetro latitude: latitude [rad].
    :parâmetro declinacao_sol: declinação solar [rad]. Calculada pela função declinacao_sol().
    :return: ângulo horário pôr-do-sol [rad].
    """

    cos_sha = -math.tan(latitude) * math.tan(declinacao_sol)
    return math.acos(min(max(float(cos_sha), float(-1.0)), float(1.0)))
    
def Dr(J):
    """
    :parâmetro J: dia do ano, inteiro de 1 a 365 ou 366.
    :return: inverso da distância relativa da terra-sol.
    """
    return 1 + (0.033 * math.cos((2.0 * math.pi / 365.0) * J))
    
def N_insolacao(omega):
    """
    Duração máxima de insolação no dia (N): Equação 34 (FAO 56)
    :parâmetro omega: ângulo horário do pôr-do-sol [rad]. Calculado pela função omega()
    :return: duração máxima de insolação no dia [h].
    """
    return (24.0 / math.pi) * omega
    
def Rs(N, n, ra, tmax, tmin):
    """
    Radiação Solar ( Rs ): Equação 35 (FAO 56)
    OBS: em caso de ausência de n, será usada a Equação 50 (FAO 56)
    :parâmetro N: duração máxima de insolação no dia [h]. Pode ser calculada pela função N.
    :parâmetro n: Insolação [h].
    :parâmetro Ra: extraterrestrial radiation [MJ m-2 day-1]. Calculada pela função Ra.
    :return: radiação solar [MJ m-2 day-1]
    """
    if np.isnan(n):
      rs = 0.16 * np.sqrt(tmax - tmin) * ra
    else:
      rs = (0.5 * n / N + 0.25) * ra
    return rs
    
def Rso(altitude, ra):
    """
    Radiação Solar de Céu Claro ( Rso ) para valores não calibrados de as e bs: Equação 37 (FAO 56)
    :parâmetro altitude: altitude acima do nível do mar [m]
    :parâmetro ra: extraterrestrial radiation [MJ m-2 day-1]. Calculada pela função Ra.
    :return: radiação solar de céu claro [MJ m-2 day-1]
    """
    return (0.00002 * altitude + 0.75) * ra
    
def Rns(rs, albedo=0.23):
    """
    Radiação de onda curta líquida ou solar líquida ( Rns ): Equação 38 (FAO 56)
    :parâmetro rs: radiação solar [MJ m-2 day-1]. Calculada pela função Rs().
    :parâmetro albedo: coeficiente de reflexão do dossel,  é de 0.23 para a cultura de referência grama hipotética.
    :return: radiação de onda curta líquida [MJ m-2 day-1].
    """
    return (1 - albedo) * rs
    
def Rnl(tmin, tmax, rs, rso, ea, sigma):
    """
    Radiação de onda longa líquida ( Rnl ): Equação 39 (FAO 56)
    :parâmetro tmin: Temperatura mínima absoluta [K]
    :parâmetro tmax: Temperatura máxima absoluta [K]
    :parâmetro Rs: radiação solar [MJ m-2 day-1]. Calculada pela função Rs().
    :parâmetro Rso: radiação solar de céu claro [MJ m-2 day-1]. Calculada pela função Rso().
    :parâmetro ea: pressão de vapor atual [kPa]. Calculada pela função Ea().
    :return:  radiação de onda longa líquida [MJ m-2 day-1]
    """
    tmax_k = tmax + 273.16 #----Converte a temperatura de °C para °K
    tmin_k = tmin + 273.16 #----Converte a temperatura de °C para °K
    
    tmp1 = (sigma * ((math.pow(tmax_k, 4) + math.pow(tmin_k, 4)) / 2))
    tmp2 = (0.34 - (0.14 * math.sqrt(ea)))
    tmp3 = 1.35 * (rs / rso) - 0.35
    return tmp1 * tmp2 * tmp3

def Rnl_medio(tmean, rs, rso, ea, sigma):
    """
    Equação modificada para dados faltantes de temperaturas máxima e mínima
    Radiação de onda longa líquida ( Rnl ): Equação 39 (FAO 56)
    :parâmetro tmean: Temperatura média absoluta [K]
    :parâmetro Rs: radiação solar [MJ m-2 day-1]. Calculada pela função Rs().
    :parâmetro Rso: radiação solar de céu claro [MJ m-2 day-1]. Calculada pela função Rso().
    :parâmetro ea: pressão de vapor atual [kPa]. Calculada pela função Ea().
    :return:  radiação de onda longa líquida [MJ m-2 day-1]
    """
    tmax_k = tmean + 273.16 #----Converte a temperatura de °C para °K
    tmin_k = tmean + 273.16 #----Converte a temperatura de °C para °K
    
    tmp1 = (sigma * ((math.pow(tmax_k, 4) + math.pow(tmin_k, 4)) / 2))
    tmp2 = (0.34 - (0.14 * math.sqrt(ea)))
    tmp3 = 1.35 * (rs / rso) - 0.35
    return tmp1 * tmp2 * tmp3
    
def Rn(rns, rnl):
    """
    Radiação líquida ( Rn ): Equação 40 (FAO 56)
    :parâmetro rns: radiação de onda curta líquida [MJ m-2 day-1]. Calculada pela função Rns().
    :parâmetro rnl: radiação de onda longa líquida [MJ m-2 day-1]. Calculada pela função Rnl().
    :return: radiação líquida [MJ m-2 day-1].
    """
    return rns - rnl
    
def fao56_penman_monteith(rn, t, u2, es, ea, delta, gamma, G):
    """
    Calcula a Evapotranspiração de referência (ETo): Equação 6 (FAO 56)
    :parâmetro rn: Radiação líquida à superfície de cultura [MJ m-2 day-1]. Calculada pela função Rn().
    :parâmetro t: Temperatura média diária a 2m de altura [K].
    :parâmetro u2:  Velocidade do vento a 2m de altura [m s-1].
    :parâmetro es: Pressão do vapor de saturação [kPa]. Calculada pela função Es().
    :parâmetro ea: Pressão do vapor atual  [kPa]. Calculada pela função Ea().
    :parâmetro delta: Declividade da curva de pressão do vapor [kPa degC-1]. Calculada pela função Delta().
    :parâmetro gamma: Constante psicrométrica [kPa deg C]. Calculada pela função psicrométrica().
    :parâmetro G: Densidade do fluxo de calor do solo  [MJ m-2 day-1].
    :return: Evapotranspiração de referência (ETo) [mm day-1].
    """
    a1 = (0.408 * (rn - G) * delta) + ((900 / (t + 273)) * u2 * gamma * (es - ea))
    a2 =  a1 / (delta + (gamma * (1 + 0.34 * u2)))
    return a2
    
def gera_serie(dataset, latitude, altitude, Gsc, sigma, G):
    """
    Gera a série Evapotranspiração de referência (ETo): Equação 6 (FAO 56)
    :parâmetro dataset: dataset com os seguintes dados: 
        - Temperaturas (máxima, mínima e média) do ar em °C - Tmax, Tmin e Tmean
        - Umidade Relativa Média - RH
        - Insolação em Horas - I
        - Velocidade do vento em m/s - U2
        - Dia do ano - J
    :return: Série de Evapotranspiração de referência (ETo) [mm day-1].
    """
    serie_eto = []
    for i in range(len(dataset)):
        if np.isnan(dataset[i,2]) == False or np.isnan(dataset[i,1]) == False:
            es = Es(dataset[i,4]) #------------> Pressão do vapor de saturação
        else:
            es = Es_medio(dataset[i,2],dataset[i,1]) #------------> Pressão do vapor de saturação
        ea = Ea(dataset[i,2],dataset[i,1],dataset[i,5]) #--------> Pressão do vapor atual
        delta = Delta(dataset[i,4]) #----------------------> Declividade da curva de pressão do vapor
        pressao_atm = Pressao_atm(altitude) #-----------> Pressão atmosférica
        gamma = psicrometrica(pressao_atm) #------------> Constante
        declinacao_sol = Declinacao_sol(dataset[i,7]) #----> Declinação solar
        omega = Omega(latitude, declinacao_sol) #-------> Ângulo horário pôr-do-sol
        dr = Dr(dataset[i,7]) #----------------------------> Inverso da distância relativa da terra-sol
        ra = Ra(latitude, declinacao_sol, omega, dr, Gsc) #--> Radiação extraterrestre para períodos diários
        N = N_insolacao(omega) #------------------------> Duração máxima de insolação no dia
        rs = Rs(N, dataset[i,3], ra, dataset[i,1], dataset[i,2]) #---------------------> Radiação solar
        rso = Rso(altitude, ra) #-----------------------> Radiação solar de céu claro
        rns = Rns(rs, albedo=0.23) #--------------------> Radiação de onda curta líquida
        if np.isnan(dataset[i,2]) == False or np.isnan(dataset[i,1]) == False:
            rnl = Rnl_medio(dataset[i,4], rs, rso, ea, sigma) #---> Radiação de onda longa líquida
        else:
            rnl = Rnl(dataset[i,2],dataset[i,1], rs, rso, ea, sigma) #---> Radiação de onda longa líquida
        rn = Rn(rns,rnl) #------------------------------> Radiação líquida
        serie_eto.append(fao56_penman_monteith(rn, dataset[i,4], dataset[i,6], es, ea, delta, gamma, G)) #---> Evapotranspiração
  
    return serie_eto
