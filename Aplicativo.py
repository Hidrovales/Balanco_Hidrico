import streamlit as st
import numpy as np
import pandas as pd 
import math
import pmfao as gse
from datetime import date
import matplotlib.pyplot as plt
from PIL import Image
import base64
from IPython.display import HTML


def eto_calc(dataset, metodo):
    latitude_graus = dataset.Latitude[0] #--em graus
    altitude = dataset.Altitude[0]  #--em metros
    latitude = math.pi/180 * latitude_graus #Converte a latitude de graus para radianos
    #: Solar constant [ MJ m-2 min-1]
    Gsc = 0.0820
    # Stefan Boltzmann constant [MJ K-4 m-2 dia-1]
    sigma = 0.000000004903
    if metodo == 'pmfao':
        eto = gse.gera_serie(dataset,altitude,latitude,Gsc,sigma)
    
    return eto

def imput_FAO():
    st.write("""
    ### Método de estimativa PM FAO:

    Equação de Penman-Monteith:
    """)
    st.latex(r'''ET_{FAO} = \frac{0.408\Delta(R_n-G)+\gamma\frac{900}{T+273}u_2(e_s-e_a)}{\Delta+\gamma(1+ 0.34u_2)}''')
    tmax = st.text_input(label='Temperatura máxima do ar em °C (obrigatório)', value= 31.4)
    tmax = float(tmax)
    tmin = st.text_input('Temperatura mínima do ar em °C (obrigatório)', value= 19.1)
    tmin = float(tmin)
    tmedia = st.text_input('Temperatura média do ar em °C')
    if tmedia == "":
        tmedia = None
    else:
        tmedia = float(tmedia)
    insolacao = st.text_input('Insolação em Horas')
    if insolacao == "":
        insolacao = None
    else:
        insolacao = float(insolacao)
    radiacao = st.text_input('Radição Solar Global em MJ/md')
    if radiacao == "":
        radiacao = None
    else:
        radiacao = float(radiacao)
    ur = st.text_input('Umidade Relativa Média em % (obrigatório)', value= 75.9)
    ur = float(ur)
    v = st.text_input('Velocidade do vento em m/s (obrigatório)', value= 1.1)
    v = float(v)
    j = st.text_input('Data (obrigatório)', value= '01/01/2020')
    lat = st.text_input('Latitude em graus (obrigatório)', value= -15.7)
    lat = float(lat)
    alt = st.text_input('Altitude em metros (obrigatório)', value= 850.06)
    alt = float(alt)
    gsc = 0.0820
    sigma = 0.000000004903
    g = 0
    
    
    eto = gse.gera_serie(tmin, tmax, ur, v, j, lat, alt, gsc, sigma, g, tmedia, insolacao, radiacao)


    st.subheader('ETo estimada:')
    st.write(eto)
    st.success('ETo foi calculada com sucesso!')
    return eto

def imput_HG():
    st.write("""
    ### Método de estimativa HG:

    Descrever aqui o método!
    """)
    tmax = st.sidebar.text_input(label="Temperatura máxima", value= 30.0, key="na_lower")
    tmin = st.sidebar.text_input('Temperatura mínima', value= 15.0, key="na_lower")
    j = st.sidebar.date_input ('Dia do ano', date.today())
    dia = gse.calcula_dia(j)
    lat = st.sidebar.text_input('Latitude', value= -19.46, key="na_lower")
    alt = st.sidebar.text_input('Altitude', value= 732.00, key="na_lower")
    data = {
        'Dia': dia,
        'Latitude': float(lat),
        'Altitude': float(alt),
        'Tmax': float(tmax),
        'Tmin': float(tmin),
    }
    features = pd.DataFrame(data, index = [0])
    eto = eto_calc(features, 'hg')

    st.subheader('Parâmetros escolhidos:')
    st.write(features)
    st.subheader('ETo estimada:')
    st.write(eto)
    return eto

def imput_FAODF():
    st.write("""
    ### Método de estimativa PM FAO com dados faltantes:

    Descrever aqui o método!
    """)
    tmax = st.sidebar.text_input(label="Temperatura máxima", value= 30.0, key="na_lower")
    tmin = st.sidebar.text_input('Temperatura mínima', value= 15.0, key="na_lower")
    j = st.sidebar.date_input ('Dia do ano', date.today())
    dia = gse.calcula_dia(j)
    lat = st.sidebar.text_input('Latitude', value= -19.46, key="na_lower")
    alt = st.sidebar.text_input('Altitude', value= 732.00, key="na_lower")
    data = {
        'Dia': dia,
        'Latitude': float(lat),
        'Altitude': float(alt),
        'Tmax': float(tmax),
        'Tmin': float(tmin),
    }
    features = pd.DataFrame(data, index = [0])
    eto = eto_calc(features, 'pmfaodf')
    st.subheader('ETo estimada:')
    st.write(eto)
    return 0

def imput_explicacao():
    st.markdown(
    """
        A evapotranspiração ($ET$) é a variável mais ativa do ciclo hidrológico e a principal componente no balanço hídrico em ecossistemas agrícolas \citep{Pereira2013Evapotranspiracao}. Durante a evapotranspiração a água passa do estado líquido para o de vapor e retorna à atmosfera por meio de dois processos físicos semelhantes: a evaporação e a transpiração. Esses processos se diferenciam unicamente quanto ao tipo de superfície evaporante. A evaporação pode ocorrer a partir do solo úmido ou da copa das plantas molhadas. Já na transpiração a água contida nos tecidos das plantas é perdida através das folhas, caule, flores e/ou raízes \citep{Anjitha2019EvapotranspirationReview}.

        Dessa forma, a $ET$, segundo \cite{Bernardo2019ManualIrrigacao.}, pode ser definida como a quantidade de água evaporada e transpirada por uma superfície com  vegetal, durante um determinado período do tempo''. A $ET$ pode ser expressa como altura equivalente de água evaporada em $mm \ t^{-1}$, onde $t$ denota uma unidade de tempo (horas, dia, mês, estações de crescimento, ou anos) \citep{Frizzone2012MicroirrigacaoMicroaspersao}.

        """)
    return


def showCsv(df):
    st.dataframe(df)
    return

def showPlot(df):
    st.line_chart(df)
    return

def create_download_link(df, filename):  
    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    #html = f'<a html="data:file/txt;base64,{payload}" download="{filename}">Click here!!</a>'
    html = '<a href="data:text/csv;base64,{payload}"> Clique aqui para download! </a>'
    html = html.format(payload=payload,filename=filename)
    st.markdown(html, unsafe_allow_html=True)


def imput():
    st.sidebar.image('testeeee.png')
    st.sidebar.header('HIDROVALES APP')
    st.sidebar.write('Bem-vindo! Este é o aplicativo educativo da Hidrovales! Aqui, você poderá calcular, de maneira rápida e prática, evapotranspiração de referência (ETo) pontual e sua série temporal e simular o balanço hídrico, além de conhecer um pouco mais sobre nosso trabalho. Selecione qualquer uma das opções abaixo para começar! Para mais informações, acesse: www.hidrovales.com.br.')

    st.sidebar.header('Escolha a opção desejada:')
    option_1 = st.sidebar.selectbox('Escolha o que deseja fazer:', ['<Selecione>','Ler sobre ETo', 'Gerar valor único', 'Gerar série temporal de ETo', 'Gerar balanço hídrico'])
    if option_1:
        st.write("")
    if option_1 == 'Ler sobre ETo':
        imput_explicacao()
    if option_1 == 'Gerar valor único':
        option_2 = st.sidebar.selectbox('Escolha o método de estimativa:', ['<Selecione>','PM FAO'])
        if option_2 == 'PM FAO':
            eto = imput_FAO()
    if option_1 == 'Gerar série temporal de ETo':
        option_2 = st.sidebar.selectbox('Escolha a estação:', ['<Selecione>','Rio Pardo de Minas'])
        if option_2 == 'Rio Pardo de Minas':
            st.write(
            """
            ### Dados climáticos da estação de Rio Pardo de Minas no estado de Minas Gerais.
            """)
            df = pd.read_csv('RIO_PARDO_MINAS_AJUSTADO.csv', delimiter = ',')
            df = df.drop(["Unnamed: 0" ],axis=1)
            showCsv(df)

            if st.button('Salvar'):
                create_download_link(df, filename="RIO_PARDO_MINAS.csv")
    

            st.write(
            """
            ### Visualização gráfica dos dados climáticos.
            """)
            df_drop = df.drop(["DATA","PRECIPITACAO_TOTAL","PRESSAO_ATMOSFERICA", "TEMPERATURA_PONTO_ORVALHO", "UMIDADE_RELATIVA.1", "VENTO", "J"],axis=1)
            showPlot(df_drop)
            latitude = math.pi/180 * -15.72305554 #Converte a latitude de graus para radianos
            altitude=850.06
            #: Solar constant [ MJ m-2 min-1]
            GSC = 0.0820
            # Stefan Boltzmann constant [MJ K-4 m-2 dia-1]
            sigma = 0.000000004903
            G = 0
            eto = gse.gera_serie(df['TEMPERATURA_MINIMA'], df['TEMPERATURA_MAXIMA'], df['UMIDADE_RELATIVA'], df['VELOCIDADE_VENTO'], df['J'], 
                                 latitude, altitude, GSC, sigma, G, df['TEMPERATURA_MEDIA'])
            st.subheader('Série temporal de ETo estimada:')
            showPlot(eto)
            df = pd.DataFrame(eto)
            if st.button('Salvar Eto'):
                create_download_link(df, "RIO_PARDO_MINAS.csv")
            st.success('ETo foi calculada com sucesso!')
        elif option_2 == 'HG':
            eto = imput_HG()
        elif option_2 == 'HGDF':
            eto = imput_FAODF()


    if option_1 == 'Gerar balanço hídrico':
        option_2 = st.sidebar.selectbox('Escolha a estação:', ['<Selecione>','Rio Pardo de Minas'])
        if option_2 == 'Rio Pardo de Minas':
            st.sidebar.selectbox('Escolha a cultura:', ['<Selecione>','Milho'])

            theta_fc = st.sidebar.text_input(label='Capacidade de campo [m^3 m^3]', value= 0.23)
            theta_wp = st.sidebar.text_input(label='Ponto de murcha [m^3 m^3]', value= 0.1)
            p = st.sidebar.text_input(label='Fator de disponibilidade hídrica [0 - 1]', value= 0.5)
            data = st.sidebar.date_input ('Dia do ano', date.today())
            dados = {
                'Data': data,
                'theta_fc': float(theta_fc),
                'theta_wp': float(theta_wp),
                'p': float(p),
            }
            features = pd.DataFrame(dados, index = [0])


imput()
