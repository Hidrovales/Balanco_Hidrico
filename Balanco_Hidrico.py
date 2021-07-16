"""
Simula o balanço hídrico
Referência: FAO 56 (2006)
"""

import numpy as np
import datetime
import sqlite3
import contextlib

def interpolacao(data, tempo, etapas, forma, data_in):
  """
  Interpolação: Equação 66 (FAO 56)
  :parâmetro data: data atual.
  :parâmetro tempo: dicionário com o número de dias de cada fase (inicial, desenvolvimento, media e final).
  :parâmetro etapas: dicionário com as etapas inicial, media e final.
  :parâmetro forma: dicionário com a forma de cada etapa (inicial, desenvolvimento, media e final). Para constante, etapa recebe True.
  :parâmetro data_in: data de início do cultivo.
  :return: valor interpolado
  """
  def interpola(prox, prev, L_etapa, Sum_L_prev, i):
    i = i + 1
    a = (i - Sum_L_prev) / L_etapa
    b = prox - prev
    c = a * b + prev
    return c
  i = data - data_in
  if i.days < tempo['inicial']:
    if forma['inicial']:
      valor = etapas['inicial']
  elif i.days < tempo['inicial'] + tempo['desenvolvimento']:
    if not forma['desenvolvimento']:
      valor = interpola(etapas['media'], etapas['inicial'], tempo['desenvolvimento'], tempo['inicial'], i.days)
  elif i.days < tempo['inicial'] + tempo['desenvolvimento'] + tempo['media']:
    if forma['media']:
      valor = etapas['media']
  elif i.days < tempo['inicial'] + tempo['desenvolvimento'] + tempo['media'] + tempo['final']:
    if not forma['final']:
      Sum_L_prev = tempo['inicial'] + tempo['desenvolvimento'] + tempo['media']
      valor = interpola(etapas['final'], etapas['media'], tempo['final'], Sum_L_prev, i.days)
    else:
      valor = etapas['final']
  return valor

def AFA(p, ADT):
  """
  Calculo da Agua facilmente aproveitável (AFA) da zona radicular do solo [mm]: Equação 83 (FAO 56)
  :parâmetro p: fator de disponibilidade hídrica [0 - 1].
  :parâmetro ADT: total de água disponível na zona radicular do solo [mm].
  :return: AFA
  """
  return p * ADT

def ADT(theta_fc, theta_wp, Zr):
  """
  Calculo do total de água disponível (ADT) na zona radicular do solo [mm]: Equação 83 (FAO 56)
  :parâmetro theta_fc: capacidade de campo [m^3 m^3].
  :parâmetro theta_wp: ponto de murcha [m^3 m^3].
  :parâmetro Zr: profundidade das raízes [m].
  :return: ADT
  """
  return 1000*(theta_fc - theta_wp)*Zr

def Din(P, Dfim, RO = 0):
  """
  Déficit de água do solo no inicil do dia [mm]: Equação 85 (FAO 56)
  O RO: Escoamento superficial do dia i [mm] pode ser considerado 0, uma vez que os eventos de precipitação que proporcionam escoamento 
  superficial também elevam a umidade do solo à capacidade de campo, podendo, dessa forma, ser ignorado.
  :parâmetro Dfim: Déficit de água do solo ao final do dia [mm].
  :parâmetro P: Precipitação do dia i [mm].
  :return: Déficit de água do solo no inicil do dia [mm].
  """

  if P > 0:
    return max(Dfim - P, 0)
  else:
    return Dfim

def DP(P, I, ET, Dfim):
  """
  Percolação profunda do dia i [mm]: Equação 88 (FAO 56)
  O CR: Ascensão capilar do dia i [mm] é considerado 0, uma vez que o nível do lençol freático se encontra 1m abaixo da zona radicular.
  O RO: Escoamento superficial do dia i [mm] é considerado 0, uma vez que os eventos de precipitação que proporcionam escoamento 
  superficial também elevam a umidade do solo à capacidade de campo, podendo, dessa forma, ser ignorado.
  :parâmetro P: Precipitação do dia [mm].
  :parâmetro I: Lâmina de irrigação do dia [mm].
  :parâmetro ET: Evapotranspiração do cultivo do dia anterior [mm].
  :parâmetro Dfim: Déficit de água do solo ao final do dia anterior [mm].
  return: Percolação profunda do dia i [mm]
  """
  CR = 0
  RO = 0
  if (P - RO) + I - ET - Dfim > 0:
    return (P - RO) + I - ET - Dfim
  else:
    return 0

def Ks(Din, ADT, AFA):
  """
  Coeficiente de redução de evapotranspiração em função da umidade do solo [0 - 1]: Equação 84 (FAO 56)
  :parâmetro Din: Déficit inicial de água do solo do dia [mm].
  :parâmetro ADT: Total de água disponível na zona radicular do solo [mm].
  :parâmetro AFA: Agua facilmente aproveitável (AFA) da zona radicular do solo [mm].
  return: Coeficiente de redução de evapotranspiração em função da umidade do solo [0 - 1]
  """
  if Din < AFA:
    return 1
  else:
    return (ADT - Din) / (ADT - AFA)

def Etca(Eto, Kc, Ks):
  """
  Evapotranspiração da cultura ajustada [mm/d]: Equação 81 (FAO 56)
  :parâmetro Eto: Evapotranspiração de referencia [mm].
  :parâmetro Kc: coeficiente da cultura.
  :parâmetro Ks: coeficiente de redução de evapotranspiração em função da umidade do solo [0 - 1].
  return: Evapotranspiração da cultura ajustada [mm/d].
  """
  return Eto * Kc * Ks

def Dfim(Dfim, P, I, ET, DP):
  """
  Déficit de água do solo ao final do dia [mm]: Equação 85 (FAO 56)
  O CR: Ascensão capilar do dia i [mm] é considerado 0, uma vez que o nível do lençol freático se encontra 1m abaixo da zona radicular.
  O RO: Escoamento superficial do dia i [mm] é considerado 0, uma vez que os eventos de precipitação que proporcionam escoamento 
  superficial também elevam a umidade do solo à capacidade de campo, podendo, dessa forma, ser ignorado.
  :parâmetro P: Precipitação do dia [mm].
  :parâmetro I: Lâmina de irrigação do dia [mm].
  :parâmetro ET: Evapotranspiração do cultivo do dia [mm].
  :parâmetro Dfim: Déficit de água do solo ao final do dia anterior [mm].
  :parâmetro DP: Percolação profunda do dia [mm].
  return: Déficit de água do solo ao final do dia  [mm]
  """
  CR = 0
  RO = 0
  if Dfim - (P - RO) - I - CR + ET + DP < 0:
    return 0
  else:
    return Dfim - (P - RO) - I - CR + ET + DP

def Irrigacao(Din, AFA):
  """
  Lâmina de irrigação [mm]
  :parâmetro Din: Déficit de água do solo no inicil do dia [mm].
  :parâmetro AFA: Agua facilmente aproveitável (AFA) da zona radicular do solo [mm].
  return: Lâmina de irrigação [mm]
  """
  if Din >= AFA:
    return AFA
  else:
    return 0

#Função para executar INSERT INTO
def execute_insert(sql,data,database_path):
    """
    Função para executar INSERT INTO
    :parametro sql: string com código sql
    :parametro data: dados que serão inseridos no banco de dados
    :parametro database_path: caminho para o banco de dados
    """
    with contextlib.closing(sqlite3.connect(database_path)) as conn: # auto-closes
        with conn: # auto-commits
            with contextlib.closing(conn.cursor()) as cursor: # auto-closes
                cursor.execute(sql,data)
                return cursor.fetchall()


def execute(sql,database_path):
    """
    Função para executar INSERT INTO
    :parametro sql: string com código sql
    :parametro database_path: caminho para o banco de dados
    :return: dataframe com os valores retornados pela consulta sql
    """
    with contextlib.closing(sqlite3.connect(database_path)) as conn: # auto-closes
        with conn: # auto-commits
            with contextlib.closing(conn.cursor()) as cursor: # auto-closes
                cursor.execute(sql)
                return cursor.fetchall()

def balanco(local, cultura, theta_fc, theta_wp, p, P, eto, periodo, z_etapas, forma_z, kc_etapas, forma_kc, data_in, database_path):
  """
  Balanço de irrigação
  :parâmetro theta_fc: capacidade de campo [m^3 m^3].
  :parâmetro theta_wp: ponto de murcha [m^3 m^3].
  :parâmetro p: fator de disponibilidade hídrica [0 - 1].
  :parâmetro P: precipitação do dia [mm].
  :parâmetro eto: dataframe com a série temporal de Evapotranspiração de referencia [mm] (Coluna 0 - Data, Coluna 1 - Eto).
  :parâmetro periodo: dicionário com o número de dias de cada fase (inicial, desenvolvimento, media e final).
  :parâmetro z_etapas: dicionário com as etapas inicial, media e final da profundidade radicular.
  :parâmetro forma_z: dicionário com a forma de cada etapa (inicial, desenvolvimento, media e final) da profundidade radicular. 
                      Para constante, etapa recebe True.
  :parâmetro kc_etapas: dicionário com as etapas inicial, media e final do coeficiente de cultura.
  :parâmetro forma_kc: dicionário com a forma de cada etapa (inicial, desenvolvimento, media e final) do coeficiente de cultura. 
                       Para constante, etapa recebe True.
  :parâmetro data_in: data de início do cultivo.
  return: Série temporal do déficit de água do solo dos dias de cultivo [mm].
  """
  #------------------------------------
  dias = sum(periodo.values())
  data_in = datetime.datetime(data_in['ano'], data_in['mes'], data_in['dia'])
  data_list = [data_in + datetime.timedelta(days=idx) for idx in range(dias)]
  #------------------------------------
  eto = eto[eto.iloc[:,0] >= data_list[0]]
  eto = eto[eto.iloc[:,0] <= data_list[-1]]
  eto = eto.iloc[:,1].values
  #------------------------------------
  P = P[P.iloc[:,0] >= data_list[0]]
  P = P[P.iloc[:,0] <= data_list[-1]]
  P = P.iloc[:,1].values
  #------------------------------------
  #Informações para o dia 0:
  etca = 0
  dfim = 0
  din = 0
  #------------------------------------
  result_kc, result_Zr, result_adt, result_afa = np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]])
  result_din, result_dfim, result_ks = np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]])
  result_I, result_dp, result_etca, result_FC =  np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]])
  result_PMP, result_F, result_UA = np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]]), np.empty([1,eto.shape[0]])
  #------------------------------------
  for j, i in enumerate(data_list):
    kc = interpolacao(i, periodo, kc_etapas, forma_kc, data_in)
    Zr = interpolacao(i, periodo, z_etapas, forma_z, data_in)
    adt = ADT(theta_fc, theta_wp, Zr)
    afa = AFA(p , ADT= adt)
    if j != 0:
      din = Din(P[j], dfim)
    ks = Ks(din, adt, afa)
    I = Irrigacao(din, afa)
    dp = DP(P[j], I, etca, dfim)
    etca = Etca(eto[j], kc, ks)
    dfim = Dfim(dfim, P[j], I, etca, dp)
    FC = Zr * theta_fc * 1000
    PMP = Zr * theta_wp * 1000
    F = FC - (FC - PMP) * p
    UA = FC - din 
    #------------------------------------
    result_din[0][j] = din
    result_kc[0][j] = kc
    result_Zr[0][j] = Zr
    result_adt[0][j] = adt
    result_afa[0][j] = afa
    result_dfim[0][j] = dfim
    result_ks[0][j] = ks
    result_I[0][j] = I
    result_dp[0][j] = dp
    result_etca[0][j] = etca
    result_FC[0][j] = FC
    result_PMP[0][j] = PMP
    result_F[0][j] = F
    result_UA[0][j] = UA
    #------------------------------------
  execute("""CREATE TABLE IF NOT EXISTS results(LOCAL TEXT, CULTURA TEXT, DATA_PLANTIO TEXT,
                                              KC_INICIAL INT, KC_MEDIO INT, KC_FINAL INT,
                                              ZR_INICIAL INT, ZR_MEDIO INT, ZR_FINAL INT,
                                              PERIODO_INICIAL INT, PERIODO_DESENVOLVIMENTO INT, PERIODO_MEDIO INT, PERIODO_FINAL INT,
                                              P FLOAT, THETA_FC FLOAT, THETA_WP FLOAT,
                                              ETO BLOB, PRECIPITACAO BLOB,
                                              KC BLOB, ZR BLOB, ADT BLOB, AFA BLOB, DIN BLOB, DFIM BLOB, KS BLOB,
                                              I BLOB, DP BLOB, ETCA BLOB, FC BLOB, PMP BLOB, F BLOB, UA BLOB
                                              )""", database_path)

  
  execute_insert("""INSERT INTO results VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                               ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                               ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
              ,(local, cultura, data_in, 
                kc_etapas['inicial'], kc_etapas['media'], kc_etapas['final'], 
                z_etapas['inicial'], z_etapas['media'], z_etapas['final'],
                periodo['inicial'], periodo['desenvolvimento'], periodo['media'], periodo['final'], 
                p, theta_fc, theta_wp, 
                eto.tobytes(), P.tobytes(),
                result_kc.tobytes(), result_Zr.tobytes(), result_adt.tobytes(), result_afa.tobytes(),
                result_din.tobytes(), result_dfim.tobytes(), result_ks.tobytes(), 
                result_I.tobytes(), result_dp.tobytes(), result_etca.tobytes(), result_FC.tobytes(), 
                result_PMP.tobytes(), result_F.tobytes(), result_UA.tobytes()
                ), database_path)

  
  return
