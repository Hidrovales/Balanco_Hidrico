"""
Simula o balanço hídrico
Referência: FAO 56 (2006)
"""



import numpy as np
import datetime

def interpolacao_kc_cultura_anual(data, tempo, kc_etapas, forma_kc, data_in):
  """
  Interpolação do coeficiente da cultura (Kc) anual: Equação 66 (FAO 56)
  :parâmetro data: data para calcular o kc.
  :parâmetro tempo: dicionário com o número de dias de cada fase (inicial, desenvolvimento, media e final).
  :parâmetro kc_etapas: dicionário com o kc das etapas inicial, media e final.
  :parâmetro forma_kc: dicionário com a forma de kc de cada etapa (inicial, desenvolvimento, media e final). Para constante, etapa recebe True.
  :parâmetro data_in: data de início do cultivo.
  :return: coeficiente da cultura (Kc) anual
  """
  def interpola_kc(kc_prox, kc_prev, L_etapa, Sum_L_prev, i):
    i = i + 1
    a = (i - Sum_L_prev) / L_etapa
    b = kc_prox - kc_prev
    c = a * b + kc_prev
    return c
  i = data - data_in
  if i.days < tempo['inicial']:
    if forma_kc['inicial']:
      kc = kc_etapas['inicial']
  elif i.days < tempo['inicial'] + tempo['desenvolvimento']:
    if not forma_kc['desenvolvimento']:
      kc = interpola_kc(kc_etapas['media'], kc_etapas['inicial'], tempo['desenvolvimento'], tempo['inicial'], i.days)
  elif i.days < tempo['inicial'] + tempo['desenvolvimento'] + tempo['media']:
    if forma_kc['media']:
      kc = kc_etapas['media']
  elif i.days < tempo['inicial'] + tempo['desenvolvimento'] + tempo['media'] + tempo['final']:
    if not forma_kc['final']:
      Sum_L_prev = tempo['inicial'] + tempo['desenvolvimento'] + tempo['media']
      kc = interpola_kc(kc_etapas['final'], kc_etapas['media'], tempo['final'], Sum_L_prev, i.days)
  else:
    kc = kc_etapas['final']
  return kc
