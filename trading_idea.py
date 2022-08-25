# coding=utf-8
from email import header
from pickle import FALSE
from random import seed
from random import random
import math as m
from time import process_time
from scipy.stats import norm
from random import randrange
import quantumrandom 
import numpy as np
from bitarray import bitarray
from bitarray.util import int2ba
import streamlit as st
import pandas as pd
import altair as alt
import base64
import xlsxwriter
from io import BytesIO
from streamlit_option_menu import option_menu
import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go
from scipy.special import erfinv
import requests
import yfinance as yf
import pandas_datareader as web
from datetime import datetime
#import lxml
#import plotly.figure_factory as ff



# TOdo
# Transak. bei Ergebnis tabelle einbinden
# transakt. bei kredit fall einbinden und als Übersicht in den der gesamtübersicht aller Sims



output = BytesIO()


st.set_page_config(page_title="My Webpage", page_icon=":tada:", layout="wide")
#with st.sidebar:
selected = option_menu(
    menu_title = "Simulationstool für den Vergleich zwischen Buy and Hold und quantitativen Handelsstrategien", #"None,
    options= ["HOME", "Simulation - Stetig", "Simulation - Diskret"],
    icons=["house", "clipboard-data","bar-chart-line"], #clipboard-data-fill, #bar-chart-line
    menu_icon="bar-chart-line",
    default_index=1,
    orientation="horizontal",
    
    #styles={
    #    "container": {"padding": "0!important", "background-color": "#fafafa"},
    #    "icon": {"color": "orange", "font-size": "25px"},
    #    "nav-link": {
    #        "font-size": "25px",
    #        "text-align": "left",
    #        "margin": "0px",
    #        "--hover-color": "#eee",
    #    },
    #    "nav-link-selected": {"background-color": "green"},
    #},
)
hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_st_style, unsafe_allow_html=True)
#st.write("""# Vergleich von Buy and Hold vs. Trading""")
#st.markdown("***")
#st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

def binary(num, pre='0b', length=12, spacer=0):   #12
    return '{{:{0}>{1}}}'.format(spacer, length).format(bin(num)[2:])


def lognorm(x,mu,sigma):
    a = (m.log(x) - mu)/m.sqrt(2*sigma**2)
    p = 0.5 + 0.5*m.erf(a)
    return p

def lognorminv(p,mu,sigma):
    a = erfinv((2*p)-1)
    x = m.exp(a * m.sqrt(2*sigma**2) + mu)
    return x


if 'ergebnis_array' not in st.session_state:
    st.session_state.ergebnis_array = np.zeros(shape=(int(10),5))
if 'first_session' not in st.session_state:
    st.session_state.first_session = True


def main():
    output = "empty"
    up = 0.0
    down = 0.0
  
    #verlaufArray = [4096][12]

    counter_trading_diskret = 0
    counter_buyAndHold_diskret = 0
    counter_indifferent_diskret = 0
    summe_trading_diskret = 0
    summe_buyAndHold_diskret = 0
    summe_indifferent_diskret = 0
    kredit_faktor = 0
    kredit_kondition = 0
    kredit_BH = False
    kredit_rueckzahlung = "zum Laufzeitende"
    kredit_ausloeser = 0.3
    anzahl_simulationen = 100
    kredit_ausloeser_signal = False
    periodenlaenge_trigger = 0
    transaktionskosten = 0.0
    transaktionskosten_relativ = 0.0
    kredit_reinvest = False
    cash_zins = 0
    

    if "load_state" not in st.session_state:
        st.session_state.load_state = False



    if selected == "Simulation - Stetig":

        diskret = '<p style="font-family:sans-serif; color:black; font-size: 30px;"><i>Simulation - mit nicht abzählbaren Kursverläufen</i></p>'
        st.markdown(diskret, unsafe_allow_html=True)
        #st.write("[Mehr zur Generierung echter Zufallszahlen (Quantenvakuum-Fluktuation) >](https://qrng.anu.edu.au/)")

        #st.text_input('Sigma: ')
        #st.text_input('Mu: ')
        #st.selectbox('Zufallszahlen: ', ["Echte ANU","Pseudo","Pseudo-System"])

        # Stetig nicht abzählbar - Trading vs Buy and Hold 
        
        with st.expander("Simulationseinstellungen"):
            left, right = st.columns(2)
            with left:
                #st.text_input('Sigma: ')
                zeitraum = st.number_input('Simulierter Zeitraum T (in Jahren): ', 0, 10, value=5) 
                anzahl_simulationen = st.number_input('Anzahl an Simulationsläufen (max. 1000): ', 1, 1000, value=100)
                sigma = st.number_input('Volatilität/Sigma σ (in %): ', 0.0, 100.0, value=20.0) / 100.0
                art_der_zufallszahlen = st.selectbox('Art der Zufallszahlen: ', ["Pseudo Zufallszahlen","Immer-Gleiche Pseudo Zufallszahlenfolge (gleicher Seed)","Echte Zufallszahlen (Quantenfluktuation)", "Immer-Gleiche Zufallszahlenfolge (Quantenfluktuation)"])
            with right:
                #st.text_input('Mu: ')
                handelstage = st.number_input('Handelstage pro Jahr (z.B. 52 = Wochenweise, 260 = Tageweise...): ', 0, 260, value=52) 
                price = st.number_input('Aktienkurs in € (zu Beginn)', 0, 1000, value= 100)
                my = st.number_input('Drift/Mu µ (in %): ', 0.0, 100.0, value= 8.0) / 100.0
                cash_zins = st.number_input('Cash-Verzinsung beim Trading (wenn nicht investiert, in %): ', 0.0, 10.0, value= 0.0) / (handelstage*100.0)
            
                
        #ergebnis_placeholder = st.empty()
        with st.expander("Handelsstrategie wählen"):
            ausgewaehlte_strategie = st.selectbox('Handelsstrategie: ', ["Siganlgrenzen für Wahrscheinlichkeiten", "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten","XX/YY Tagelinie","MACD"])
            left_2, right_2 = st.columns(2)
            with left_2:
                if "Siganlgrenzen für Wahrscheinlichkeiten" in ausgewaehlte_strategie:
                    signalgrenze_verkauf = st.number_input('Signalgrenze "VERKAUFEN" (in %, verkaufen wenn überhalb dieser Grenze): ', 0.0, 1.0, value= 0.60)
                if "XX/YY Tagelinie" in ausgewaehlte_strategie:
                    signalgrenze_klein = st.number_input('Kleinere Tageslinie (XX): ', 0, 200, value= 38)
                if "MACD" in ausgewaehlte_strategie:
                    periodenlaenge_klein = st.number_input('Kleinere Periodenlänge (EMA-1): ', 0, 200, value= 12)
                    macd_zero = st.checkbox("MACD mit EMA-Trigger (ja/nein)", value=False)
                if "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie:
                    signalgrenze_verkauf = st.number_input('Signalgrenze "VERKAUFEN" in % (verkaufen wenn überhalb dieser Grenze): ', 0.0, 1.0, value= 0.60)
                    signalgrenze_klein = st.number_input('XX-Tageslinie (als Basis, statt des einfachen Kurses): ', 0, 200, value= 38)
                    


            with right_2:
                if "Siganlgrenzen für Wahrscheinlichkeiten" in ausgewaehlte_strategie:
                    signalgrenze_kauf = st.number_input('Signalgrenze "KAUFEN" (in %, kaufen wenn unterhalb dieser Grenze): ', 0.0, 1.0, value= 0.30)
                    if signalgrenze_kauf > signalgrenze_verkauf:
                        st.info("Der Wert muss kleiner sein, als die Verkaufssignalgrenze")
                if "XX/YY Tagelinie" in ausgewaehlte_strategie:
                    signalgrenze_groß = st.number_input('Größere Tageslinie (YY): ', 0, 400, value= 200)
                if "MACD" in ausgewaehlte_strategie:
                    periodenlaenge_groß = st.number_input('Größere Periodenlänge (EMA-2): ', 0, 200, value= 26)
                    if macd_zero:
                        periodenlaenge_trigger = st.number_input('MACD-Trigger Periodenlänge (EMA-3): ', 0, 200, value= 9)
                if "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie:
                    signalgrenze_kauf = st.number_input('Signalgrenze "KAUFEN" in % (kaufen wenn unterhalb dieser Grenze): ', 0.0, 1.0, value= 0.30)
            

        with st.expander("Transaktionskosten (Optional)"):
            transaktionskosten_true = st.checkbox("Transaktionskosten mit einbeziehen (ja/nein)", value=False)
            left_4, right_5 = st.columns(2) 
            with left_4:
                if transaktionskosten_true:
                    transaktionskosten = st.number_input('Transaktionskosten pro Trade (Festbetrag in €): ', 0.0, 100.0, value=0.0)
                else:
                    transaktionskosten = 0.0 
            with right_5:
                if transaktionskosten_true:
                    transaktionskosten_relativ = st.number_input('Transaktionskosten pro Trade bzgl. Ordervolumen in % (1,0 ≙ 1%): ', 0.00, 15.00, step=0.01, value=0.00) * 0.01
                else:
                    transaktionskosten_relativ = 0.0 
            


        with st.expander("Leverage mit Kredit (Optional)"):
            #kredit_true = st.checkbox("Kreditaufnahme (ja/nein)", value=False)
            left_3, right_3 = st.columns(2) 
            with left_3:
                kredit_true = st.checkbox("Kreditaufnahme (ja/nein)", value=False)
                if kredit_true:
                    kredit_faktor = st.number_input('Kreditaufnahme (x-fache des Start-Aktienkurses): ', 0.0, 20.0, value=0.5)
                    if "XX/YY Tagelinie" in ausgewaehlte_strategie:
                        kredit_ausloeser = st.number_input('Kreditauslöse-Ereignis (ZZ/YY-Tagelinie): ', 0, 200, value= signalgrenze_klein)
                    elif "Siganlgrenzen für Wahrscheinlichkeiten" in ausgewaehlte_strategie:
                        kredit_ausloeser = st.number_input('Kreditauslöse-Ereignis (Signalgrenze "Nachkaufen"): ', 0.0, 1.0, value= signalgrenze_kauf)
                    elif "MACD" in ausgewaehlte_strategie:
                        kredit_ausloeser = 0.0
                    elif "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie:
                        kredit_ausloeser = st.number_input('Kreditauslöse-Ereignis (Signalgrenze "Nachkaufen"): ', 0.0, 1.0, value= signalgrenze_kauf)
                    else:
                        kredit_ausloeser = 0.0

            with right_3:
                if kredit_true:
                    kredit_reinvest = st.checkbox("Gewinn (durch Kredit) drauffolgend reinvestieren (ja/nein)", value=False)
                    #kredit_BH = st.checkbox("Kreditaufnahme auch für Buy and Hold Strategie (ja/nein)", value=False)
                    kredit_kondition =  st.number_input('Kreditkondition p.a. (1.0 ≙ 1%): ', -30.0, 30.0, value = 1.0) / (handelstage*100.0)
                    kredit_rueckzahlung = st.selectbox('Kreditrueckzahlung (Zeitpunkt): ',('zum Laufzeitende', 'bei Verkauf-Signalgrenze (mehrfache Kreditaufnahme möglich)'))
                    

        kredit = kredit_faktor * price

        #@st.cache(show_spinner=True)
        #my = 0.08
        #sigma = 0.2
        #St = 120
        #min = a if a < b else b
        t = float(1.0/handelstage)

        if "Siganlgrenzen für Wahrscheinlichkeiten" in ausgewaehlte_strategie or "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie:
            up = signalgrenze_verkauf  #Signalgrenze (in abhängigkeit der Wahrscheinlichkeit) für den Verkauf --> Verkaufsignal z.B. wenn >= 60%
            down = signalgrenze_kauf   #Signalgrenze (in abhängigkeit der Wahrscheinlichkeit) für den Kauf --> Kaufsignal z.B. wenn <= 30%
        elif "XX/YY Tagelinie" in ausgewaehlte_strategie:
            up = signalgrenze_klein  #Signalgrenze (in abhängigkeit der Wahrscheinlichkeit) für den Verkauf --> Verkaufsignal z.B. wenn >= 60%
            down = signalgrenze_groß #Signalgrenze (in abhängigkeit der Wahrscheinlichkeit) für den Kauf --> Kaufsignal z.B. wenn <= 30%
        else: 
            up = 0.6
            down = 0.3

        #countBH = 0
        #countTS = 0
        #countTS_mit_leverage = 0
        #countBH_mit_leverage = 0
        countTS_kredit_aktiv = 0
        countTS_Kredit_gewinn = 0
        betragBH = 0
        betragTS = 0
        betragTS_mit_Leverage = 0
        betrag_kredit_gewinn_all = 0
        betragTS_kredit = 0
        zf = randrange(100)
        #print(zf)
        csv_klassisch = pd.DataFrame(list())
        df_chart = pd.DataFrame(list())
        df3 = pd.DataFrame(list())
        df_array = []
        kurs_trading_chart = []
        #endwerte_sim = [0] * 260
        endwerte_sim = np.zeros(shape=(int(anzahl_simulationen),5)) # 4096,12
        endwerte_sim_ohne = np.zeros(shape=(int(anzahl_simulationen),3)) # 4096,12
        #endwerte_sim_trading = [0] * int(anzahl_simulationen) # 4096,12
        #endwerte_sim_buyandhold = [0] * int(anzahl_simulationen) # 4096,12
        handelstage_gesamt = int(handelstage * zeitraum)
        
        ergebnis_array = np.zeros(shape=(int(10),5))  # 0 Häufigkeit (BH,TS,%BH,%TS,performanceTS), 1 Betrag/Summe (BH,TS,%BH,%TS,performanceTS), 2
        ergebnis_array_kredit = np.zeros(shape=(int(10),5)) # 0 Häufigkeit, 1 Betrag/Summe (BH,TS,%TS), 2 Summe der Gewinne nur durch Kredit
        grunddaten = [""] * 13
        prozess_daten = [""] * 7
        #ergebnis_array_transaktionsgebühr = np.zeros(shape=(int(10),5))
        transaktionskosten_array = [0.0] * int(anzahl_simulationen)
        transaktionskosten_array_kredit_only = [0.0] * int(anzahl_simulationen)
        #np.array([[countBH, countTS],[countBH_mit_leverage, countTS_mit_leverage], [betragBH_rund, betragTS_rund],[betragBH_rund,betragTS_mit_Leverage], [0,betrag_kredit_gewinn_all_rund]])
       
       # sp500_tickers = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        
        #url_link = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        #r = requests.get(url_link,headers ={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        #sp500_tickers = pd.read_html(r.text)
        #sp500_tickers = sp500_tickers[0] 
        #tickers = sp500_tickers['Symbol'].values.tolist()
        #print(tickers[3])

        start_time = datetime(2020,1,1)
        end_time = datetime(2022,1,1)
        stock_ticker = ["GOOG", "AAPL", "AMZN"]
        stock_array = np.zeros(shape=(len(stock_ticker),int(505))) # 4096,12
        tagelinien_vorfeld = 0
        max_taglinien_vorfeld = 400





        if st.button('Simulation durchführen'):

            #for i in range(len(stock_ticker)):
            #    
            #    df_stock = web.DataReader(stock_ticker[i], 'yahoo', start_time,end_time)
            #    td_stock = pd.DataFrame(df_stock) 
            #    schlusskurse_stock = td_stock['Close']
            #    stock_array[i] = schlusskurse_stock[1]
#
            #    print(stock_array[i][4])


            
            st.session_state.load_state = True
            st.session_state.first_session = False
            grunddaten[0] = str(zeitraum)
            grunddaten[1] = str(anzahl_simulationen)
            grunddaten[2] = str(handelstage)
            grunddaten[3] = str(sigma)
            grunddaten[4] = str(my)
            grunddaten[5] = str(price)
            grunddaten[6] = str(transaktionskosten) + "€ + " +str(round(transaktionskosten_relativ,4)*100) + "%"
            grunddaten[7] = str(art_der_zufallszahlen)
            grunddaten[8] = str(ausgewaehlte_strategie)
            grunddaten[9] = "ja" if kredit_true else "nein"
            grunddaten[10] = "ja" if kredit_reinvest else "nein"
            grunddaten[11] = str(kredit_rueckzahlung)
            grunddaten[12] = "Konfiguration"
            randomNum_tagelinien = [0] * tagelinien_vorfeld 
            process_vorfeld = [0] * tagelinien_vorfeld 



            my_bar = st.progress(0)
            with st.spinner('Bitte warten...'):


                if "XX/YY Tagelinie" in ausgewaehlte_strategie:
                    tagelinien_vorfeld = signalgrenze_groß 
                if "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie:
                    tagelinien_vorfeld = signalgrenze_klein 

                ### Falls gleiche Zufallszahlenfolge gewünscht wird ### 
                if "Immer-Gleiche Pseudo Zufallszahlenfolge (gleicher Seed)" == art_der_zufallszahlen: #in art_der_zufallszahlen:
                    zufallszahlen_Set = np.zeros(shape=(int(anzahl_simulationen),handelstage_gesamt + max_taglinien_vorfeld)) # 4096,12
                    sed = seed(4)
                    for u in range(anzahl_simulationen):
                        for p in range(handelstage_gesamt + max_taglinien_vorfeld):
                            zufallszahlen_Set[u][p] = random()


                  ### Echte Stock-Prices untersucht werden sollen ### 
                if False: #"Immer-Gleiche Pseudo Zufallszahlenfolge (gleicher Seed)" == art_der_zufallszahlen: #in art_der_zufallszahlen:
                    zufallszahlen_Set = np.zeros(shape=(int(anzahl_simulationen),handelstage_gesamt)) # 4096,12
                    sed = seed(4)
                    for u in range(anzahl_simulationen):
                        for p in range(handelstage_gesamt):
                            zufallszahlen_Set[u][p] = random()



                if "Immer-Gleiche Zufallszahlenfolge (Quantenfluktuation)" == art_der_zufallszahlen:
                    zufallszahlen_Set_echt = np.zeros(shape=(int(anzahl_simulationen),handelstage_gesamt + max_taglinien_vorfeld))
                    #c1 = c2 = c3 = c4 = 0
                    file = open("zahlenfolge_groß", "rb")
                    pre_generated_random_numbers = np.fromfile(file, dtype=np.uint32)
                    max_int = 4294967295.0 # unsigned max int wert (nur positive werte)
                    pre_generated_random_numbers  = np.divide(pre_generated_random_numbers, max_int) # 2.621.440 Zahlen (passt: bei 10 Jahren mit 260 Handeltagen und 1000 Sims. = 2.6 Mio.)
             
                    for u in range(anzahl_simulationen):
                        for p in range(handelstage_gesamt + max_taglinien_vorfeld):
                            zufallszahlen_Set_echt[u][p] = pre_generated_random_numbers[u * (handelstage_gesamt + max_taglinien_vorfeld) + p]
                    file.close()
                



                for i in range(int(anzahl_simulationen)):
                    my_bar.progress((i+1)/anzahl_simulationen)
                    seed(i+zf+10)
                    #handelstage_gesamt = handelstage * zeitraum
                    randomNum = [0] * handelstage_gesamt      # Aray der Zufallszahlen [0;1]


                    if tagelinien_vorfeld > 0:

                        randomNum_tagelinien = [0] * tagelinien_vorfeld 
                        process_vorfeld = [0] * tagelinien_vorfeld 
                        process_vorfeld[0] = price

                        if "Echte Zufallszahlen (Quantenfluktuation)" == art_der_zufallszahlen:
                            myList_vorfeld = quantumrandom.get_data(data_type='uint16', array_length=tagelinien_vorfeld) # tagelinie muss <1000 Tage umfassen    
                            myInt = 65535.0
                            myList_vorfeld  = np.divide(myList_vorfeld, myInt)


                        for number in range(len(randomNum_tagelinien)):
                            
                            if "Pseudo Zufallszahlen" == art_der_zufallszahlen: #in art_der_zufallszahlen: 
                                randomNum_tagelinien[number] = random() # Mit Random from Python

                            elif "Echte Zufallszahlen (Quantenfluktuation)" == art_der_zufallszahlen:
                                randomNum_tagelinien[number] = myList_vorfeld[number]  #Mit Quantenfluktuationszahlen

                            elif "Immer-Gleiche Pseudo Zufallszahlenfolge (gleicher Seed)" == art_der_zufallszahlen: #in art_der_zufallszahlen:
                                randomNum_tagelinien[number] = zufallszahlen_Set[i][handelstage_gesamt + number]
                            elif "Immer-Gleiche Zufallszahlenfolge (Quantenfluktuation)" == art_der_zufallszahlen:
                                randomNum_tagelinien[number] = zufallszahlen_Set_echt[i][handelstage_gesamt + number]
                            else: 
                                randomNum_tagelinien[number] = random()
                        

                       
                            if number > 0:
                                process_vorfeld[number] = process_vorfeld[number-1] * m.exp((my - (sigma**2)/2) * t + sigma * m.sqrt(t) * norm.ppf(randomNum_tagelinien[number]))

                        #if i == 1:
                        #    print(process_vorfeld)
                        #    print("###############")
                        #process_vorfeld = process_vorfeld - (process_vorfeld[tagelinien_vorfeld-1] - price)

                        process_vorfeld = [x - (process_vorfeld[tagelinien_vorfeld-1] - price) for x in process_vorfeld]

                        #if i == 1:
                        #    print(process_vorfeld)
                        #    print("###################")













                    process = [0.0] * handelstage_gesamt      # Array für die Aktienkurse / Prozess
                    buy_and_hold = [0.0] * handelstage_gesamt 
                    buy_and_hold_transaktionskosten_verkauf = 0.0  
                    buy_and_hold_transaktionskosten_kauf = 0.0        
                    position = [0.0] * handelstage_gesamt
                    cash = [0.0] * handelstage_gesamt
                    prob = [0.0] * handelstage_gesamt
                    signal = [0.0] * handelstage_gesamt
                    possible = [0.0] * handelstage_gesamt
                    golden = [0.0] * handelstage_gesamt 
                    kreditlinie = [0.0] * handelstage_gesamt 
                    kredit_cash = [0.0] * handelstage_gesamt 
                    kredit_position = [0.0] * handelstage_gesamt 
                    kredit_kurs = [0.0] * handelstage_gesamt
                    kredit_gewinn = [0.0] * handelstage_gesamt
                    tageschnitte_yy = [0.0] * handelstage_gesamt 
                    tageschnitte_xx = [0.0] * handelstage_gesamt 
                    tageschnitte_zz = [0.0] * handelstage_gesamt 
                    ema_klein = [0.0] * handelstage_gesamt 
                    ema_groß = [0.0] * handelstage_gesamt 
                    macd = [0.0] * handelstage_gesamt 
                    macd_trigger = [0.0] * handelstage_gesamt 
                    transaktionskosten_kummuliert = [0.0] * handelstage_gesamt 
                    transaktionskosten_kummuliert_kredit = [0.0] * handelstage_gesamt 
                    # 500 Zufallszahlen werden erzeugt
                    randomNum[0] = int(1)

                    process[0] = price
                    buy_and_hold_position = (process[0] - (transaktionskosten + process[0] * transaktionskosten_relativ))/process[0]
                    buy_and_hold[0] = process[0] * buy_and_hold_position 
                    buy_and_hold_transaktionskosten_kauf = (transaktionskosten + process[0] * transaktionskosten_relativ)
                    #print(str(buy_and_hold[0]) + str(buy_and_hold_position))

                    position[0] = 0
                    cash[0] = price #100.0
                    golden[0] = price #100.0
                    kredit_aktiv = False
                    kredit_gewinn_all = 0
                    kredit_gewinn_zw = 0
                    kredit_ende = False

                    
        
                    if "Echte Zufallszahlen (Quantenfluktuation)" == art_der_zufallszahlen: #in art_der_zufallszahlen: 
                        if handelstage_gesamt < 1000:
                            myList = quantumrandom.get_data(data_type='uint16', array_length=handelstage_gesamt)
                        else:
                            myList = quantumrandom.get_data(data_type='uint16', array_length=1000)
                            if handelstage_gesamt > 1000: 
                                myList2 = quantumrandom.get_data(data_type='uint16', array_length=1000)
                                myList += myList2
                            if handelstage_gesamt > 2000: 
                                myList3 = quantumrandom.get_data(data_type='uint16', array_length=1000)
                                myList += myList3
                            if handelstage_gesamt > 3000: 
                                myList4 = quantumrandom.get_data(data_type='uint16', array_length=1000)
                                myList += myList4
                        myInt = 65535.0
                        newList  = np.divide(myList, myInt)



                    sell_out = False
                    traded_ever = False

                    ### Schleife für den Prozess einer einzigen Simulation (eine trading_idea-Excel-Tabelle quasi)
                    for rand in range(handelstage_gesamt):
                        
                        if "Pseudo Zufallszahlen" == art_der_zufallszahlen: #in art_der_zufallszahlen: 
                            randomNum[rand] = random() # Mit Random from Python
                        elif "Echte Zufallszahlen (Quantenfluktuation)" == art_der_zufallszahlen: #in art_der_zufallszahlen: 
                            randomNum[rand] = newList[rand] # Mit Quantenfluktuationszahlen
                            #print(randomNum[rand])
                        elif "Immer-Gleiche Pseudo Zufallszahlenfolge (gleicher Seed)" == art_der_zufallszahlen: #in art_der_zufallszahlen:
                            randomNum[rand] = zufallszahlen_Set[i][rand]
                        elif "Immer-Gleiche Zufallszahlenfolge (Quantenfluktuation)" == art_der_zufallszahlen:
                            randomNum[rand] = zufallszahlen_Set_echt[i][rand]
                        else: 
                            randomNum[rand] = random()
                            

    ############ Handelsstrategie Signalgrenzen (weitere Strategien folgen hier) #############

                        #Prozess bzw. geometrisch brownsche Bewegung
                        if rand > 0: 
                            process[rand] = process[rand-1] * m.exp((my - (sigma**2)/2) * t + sigma * m.sqrt(t) * norm.ppf(randomNum[rand]))
                            buy_and_hold[rand] = process[rand] * buy_and_hold_position


    ###### MACD  ##########   mit und ohne 9-Day Trigger

                            if "MACD" in ausgewaehlte_strategie:
                                if rand == 1:
                                    ema_klein[rand-1] = process[rand-1]
                                    ema_groß[rand-1] = process[rand-1]
                                    macd_trigger[rand-1] = process[rand-1]
                                    #print("EMA_START: " + str(process[rand-1]))

                                smoothing_factor_klein = 2/(periodenlaenge_klein + 1)
                                smoothing_factor_groß = 2/(periodenlaenge_groß + 1)
                                smoothing_factor_trigger = 2/(periodenlaenge_trigger + 1)
                                ema_klein[rand] = process[rand] * smoothing_factor_klein + (1 - smoothing_factor_klein) *  ema_klein[rand-1]
                                ema_groß[rand] = process[rand] * smoothing_factor_groß + (1 - smoothing_factor_groß) *  ema_groß[rand-1]
                                macd[rand] = ema_klein[rand] - ema_groß[rand]
                                if macd_zero: # Mit oder ohne 9-Day-Trigger
                                    macd_trigger[rand] =  macd[rand] * smoothing_factor_trigger + (1 - smoothing_factor_trigger) *  macd_trigger[rand-1]#
                                else:
                                    macd_trigger[rand] = 0
                                kredit_ausloeser = macd_trigger[rand]


                                # Einschätzung ob Kauf oder Verkaufssignal vorhanden
                                if macd[rand] >= macd_trigger[rand]: #Sofern die „MACD“-Linie ihren „Trigger“ von unten nach oben kreuzt, ist ein Kaufsignal gegeben
                                    signal[rand] = "Kauf"
                                elif macd[rand] < macd_trigger[rand]: #Analog gilt ein Verkaufssignal, wenn die „MACD“-Linie ihren „Trigger“ von oben nach unten kreuzt
                                    signal[rand] = "Verkauf" 
                                else:
                                    signal[rand] = "-" 
                            
                                # Kauf oder Verkauf überhaupt möglich (Cash zum einsteigen oder schon investiert)?
                                if signal[rand] == "Kauf" and cash[rand-1] > 0 + (transaktionskosten + cash[rand-1] * transaktionskosten_relativ): # > 0 + transaktionskosten: 
                                    possible[rand] = "möglich"
                                elif signal[rand] == "Kauf" and cash[rand-1] <= 0:
                                    possible[rand] = "nicht möglich" 
                                elif signal[rand] == "Verkauf" and position[rand-1] > 0:
                                    possible[rand] = "möglich"
                                elif signal[rand] == "Verkauf" and position[rand-1] <= 0:     # funktioniert evtl. nicht wenn der Aktien-Kurs/Prozess ins minus geht --> eher unwahrscheinlich
                                    possible[rand] = "nicht möglich"
                                else:
                                    possible[rand] = "-" 


    ###### 38/200 Tagelinie ########  
                            elif "XX/YY Tagelinie" in ausgewaehlte_strategie:
                                
                                summe_yy = 0
                                summe_xx = 0
                                summe_zz = 0 #Tagelinie für Kredit Szenario 

                                if rand <= signalgrenze_groß: # Vorfeld berechnung der Tagelinien

                                    process_array = np.concatenate((process_vorfeld, process))

                                    for l in range(signalgrenze_groß):
                                        summe_yy += process_array[(signalgrenze_groß + rand) - l]
                                        if l < signalgrenze_klein:
                                            summe_xx += process_array[signalgrenze_groß + rand - l]
                                        if kredit_true and l < kredit_ausloeser:
                                            summe_zz += process_array[signalgrenze_groß + rand - l]
                                    tageschnitte_yy[rand] = summe_yy/signalgrenze_groß
                                    tageschnitte_xx[rand] = summe_xx/signalgrenze_klein
                                    if kredit_true and  0 < kredit_ausloeser:
                                        tageschnitte_zz[rand] = summe_zz/kredit_ausloeser
                                    #if i == 1 and rand ==1:
                                    #    print("+++++++++++")
                                    #    print(process_array)
                                    #    print(tageschnitte_yy[rand])
                                    #    print("+++++++++++")


                                if rand > signalgrenze_groß: #Tagelinienberechnung nachdem Signalgrenze_groß in der Sim erreicht wurde
                                    summe_yy = 0
                                    summe_xx = 0
                                    summe_zz = 0 #Tagelinie für Kredit Szenario 
                                    for l in range(signalgrenze_groß):
                                        summe_yy += process[rand-l]
                                        if l < signalgrenze_klein:
                                            summe_xx += process[rand-l]
                                        if kredit_true and l < kredit_ausloeser:
                                            summe_zz += process[rand-l]

                                    tageschnitte_yy[rand] = summe_yy/signalgrenze_groß
                                    tageschnitte_xx[rand] = summe_xx/signalgrenze_klein
                                    if kredit_true and  0 < kredit_ausloeser:
                                        tageschnitte_zz[rand] = summe_zz/kredit_ausloeser



                                # Einschätzung ob Kauf oder Verkaufssignal vorhanden
                                if tageschnitte_xx[rand] >= tageschnitte_yy[rand]: #38 Tagelinie kreuzt die 200 Tagelinie von unten --> Trend: Kursausbruch nach oben
                                    signal[rand] = "Kauf"
                                elif tageschnitte_xx[rand] < tageschnitte_yy[rand]: #38 Tagelinie kreuzt die 200 Tagelinie von oben --> Abverkauf-Trend
                                    signal[rand] = "Verkauf" 
                                else:
                                    signal[rand] = "-" 

                                # Kauf oder Verkauf überhaupt möglich (Cash zum einsteigen oder schon investiert)?
                                if signal[rand] == "Kauf" and cash[rand-1] > 0 + (transaktionskosten + cash[rand-1] * transaktionskosten_relativ): # transaktionskosten:
                                    possible[rand] = "möglich"
                                elif signal[rand] == "Kauf" and cash[rand-1] <= 0:
                                    possible[rand] = "nicht möglich" 
                                elif signal[rand] == "Verkauf" and position[rand-1] > 0:
                                    possible[rand] = "möglich"
                                elif signal[rand] == "Verkauf" and position[rand-1] <= 0:     # funktioniert evtl. nicht wenn der Aktien-Kurs/Prozess ins minus geht --> eher unwahrscheinlich
                                    possible[rand] = "nicht möglich"
                                else:
                                    possible[rand] = "-" 
                        
                        



    #######  Handelsstrategie Welland mit z.B. 38 Tagelinie als Wert für die Wahrscheinlichkeiten/Signalgrenzen #########

                            elif "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie:

                                summe_xx = 0
                                if rand <= signalgrenze_klein: # Vorfeld berechnung der Tagelinien

                                    process_array = np.concatenate((process_vorfeld, process))

                                    for l in range(signalgrenze_klein):
                                        summe_xx += process_array[(signalgrenze_klein + rand) - l]
                                    tageschnitte_xx[rand] = summe_xx/signalgrenze_klein

                                  
                                    #if i == 99 and rand ==1:
                                    #    print("+++++++++++")
                                    #    print(process_array)
                                    #    print(tageschnitte_xx[rand])
                                    #    print("+++++++++++")


                                #summe_zz = 0 #Tagelinie für Kredit Szenario 
                                if rand > signalgrenze_klein:
                                    for l in range(signalgrenze_klein):
                                        summe_xx += process[rand-l]
                                    tageschnitte_xx[rand] = summe_xx/signalgrenze_klein


                                
                                prob[rand] = lognorm(tageschnitte_xx[rand], m.log(price)+(my+(sigma**2)/2)*rand*t, sigma * m.sqrt(rand*t))
                                # Einschätzung ob Kauf oder Verkaufssignal vorhanden
                                if prob[rand] < down:
                                    signal[rand] = "Kauf"
                                elif prob[rand] > up:
                                    signal[rand] = "Verkauf" 
                                else:
                                    signal[rand] = "-" 

                                # Kauf oder Verkauf überhaupt möglich (Cash zum einsteigen oder schon investiert)?
                                if signal[rand] == "Kauf" and cash[rand-1] > 0 + (transaktionskosten + cash[rand-1] * transaktionskosten_relativ): #transaktionskosten:
                                    possible[rand] = "möglich"
                                elif signal[rand] == "Kauf" and cash[rand-1] <= 0:
                                    possible[rand] = "nicht möglich" 
                                elif signal[rand] == "Verkauf" and position[rand-1] > 0:
                                    possible[rand] = "möglich"
                                elif signal[rand] == "Verkauf" and position[rand-1] <= 0:     # funktioniert evtl. nicht wenn der Aktien-Kurs/Prozess ins minus geht --> eher unwahrscheinlich
                                    possible[rand] = "nicht möglich"
                                else:
                                    possible[rand] = "-" 




    #######  Handelsstrategie Welland  #########
                            else:
                                prob[rand] = lognorm(process[rand], m.log(price)+(my+(sigma**2)/2)*rand*t, sigma * m.sqrt(rand*t))
                                #prob[rand] = norm.sf(process[rand], m.log(price)+(my+(sigma**2)/2)*rand*t, sigma * m.sqrt(rand*t))
                                # Einschätzung ob Kauf oder Verkaufssignal vorhanden
                                if prob[rand] < down:
                                    signal[rand] = "Kauf"
                                elif prob[rand] > up:
                                    signal[rand] = "Verkauf" 
                                else:
                                    signal[rand] = "-" 

                                # Kauf oder Verkauf überhaupt möglich (Cash zum einsteigen oder schon investiert)?
                                if signal[rand] == "Kauf" and cash[rand-1] > 0 + (transaktionskosten + cash[rand-1] * transaktionskosten_relativ): #transaktionskosten:
                                    possible[rand] = "möglich"
                                elif signal[rand] == "Kauf" and cash[rand-1] <= 0:
                                    possible[rand] = "nicht möglich" 
                                elif signal[rand] == "Verkauf" and position[rand-1] > 0:
                                    possible[rand] = "möglich"
                                elif signal[rand] == "Verkauf" and position[rand-1] <= 0:     # funktioniert evtl. nicht wenn der Aktien-Kurs/Prozess ins minus geht --> eher unwahrscheinlich
                                    possible[rand] = "nicht möglich"
                                else:
                                    possible[rand] = "-" 





    # Falls kein Kredit

                            if not kredit_true: 
                                # Position aufbauen/abbauen, je nach Signal von oben (Signal + möglich)
                                transaktionskosten_kummuliert[rand] = transaktionskosten_kummuliert[rand-1] 
                                if signal[rand] == "Kauf" and possible[rand] == "möglich" and not rand == handelstage_gesamt-1:
                                    traded_ever = True
                                    transaktionskosten_kummuliert[rand] += (transaktionskosten + cash[rand-1] * transaktionskosten_relativ) #transaktionskosten  
                                    position[rand] = (cash[rand-1]-(transaktionskosten + cash[rand-1] * transaktionskosten_relativ))/process[rand]   

                                #elif (signal[rand] == "Verkauf" and possible[rand] == "möglich") or rand == handelstage_gesamt-1:
                                    #position[rand] = 0
                                    #transaktionskosten_kummuliert[rand] += transaktionskosten 
                                else: 
                                    position[rand] = position[rand-1]
                                  
                                # Cash
                                if (signal[rand] == "Verkauf" and possible[rand] == "möglich") or (rand == handelstage_gesamt-1 and position[rand] > 0):
                                    if (rand == handelstage_gesamt-1 and position[rand] > 0):
                                        sell_out = True
                                    position[rand] = 0
                                    transaktionskosten_kummuliert[rand] += (transaktionskosten + (process[rand] * position[rand-1]) * transaktionskosten_relativ) #transaktionskosten 
                                    cash[rand] = process[rand] * position[rand-1] - (transaktionskosten + (process[rand] * position[rand-1]) * transaktionskosten_relativ) 
                                    
                                elif signal[rand] == "Kauf" and possible[rand] == "möglich" and not rand == handelstage_gesamt-1:
                                    cash[rand] = 0
                                else: 
                                    cash[rand] = cash[rand-1] * (1+cash_zins)
                            else:

    # Falls mit Kredit
    # Kreditauslöse_Signal:
    # Bei 38/200 Tagelinie z.B. weitere Tagelinie die kreuzt, 50/200
    # Bei Signalgrenzen mit Wahrscheinlichkeiten, einfacheine geringere Grenze
                                if "XX/YY Tagelinie" in ausgewaehlte_strategie and rand > signalgrenze_groß and tageschnitte_zz[rand] >= tageschnitte_yy[rand]:
                                    kredit_ausloeser_signal = True 
                                elif "Siganlgrenzen für Wahrscheinlichkeiten" in ausgewaehlte_strategie and prob[rand] < kredit_ausloeser : 
                                    kredit_ausloeser_signal = True
                                elif "MACD" in ausgewaehlte_strategie and macd[rand] > kredit_ausloeser: 
                                    kredit_ausloeser_signal = True
                                elif "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie and prob[rand] < kredit_ausloeser:
                                    kredit_ausloeser_signal = True
                                else:
                                    kredit_ausloeser_signal = False

                           
         # 1. Möglichkeit
                                if 'bei Verkauf-Signalgrenze (mehrfache Kreditaufnahme möglich)' in kredit_rueckzahlung:
                                    #Kreditaufnahme
                                    transaktionskosten_kummuliert[rand] += transaktionskosten_kummuliert[rand-1]
                                    transaktionskosten_kummuliert_kredit[rand] += transaktionskosten_kummuliert_kredit[rand-1]
                                    if kredit_ausloeser_signal and not kredit_aktiv and not rand == handelstage_gesamt-1:
                                        kreditlinie[rand] = kredit
                                       
                                        if (signal[rand] == "Kauf" and possible[rand] == "möglich"):
                                            kredit_position[rand] = (kreditlinie[rand] - (kreditlinie[rand] * transaktionskosten_relativ))/process[rand]
                                            transaktionskosten_kummuliert[rand] += (kreditlinie[rand] * transaktionskosten_relativ)
                                       
                                        #if not (signal[rand] == "Kauf" and possible[rand] == "möglich"):
                                        else:
                                            #transaktionskosten_kummuliert[rand] += transaktionskosten
                                            kredit_position[rand] = (kreditlinie[rand]-(transaktionskosten + kreditlinie[rand] * transaktionskosten_relativ))/process[rand]
                                            transaktionskosten_kummuliert_kredit[rand] += (transaktionskosten + kreditlinie[rand] * transaktionskosten_relativ)
                                      

                                        #transaktionskosten_kummuliert_kredit += (transaktionskosten + kreditlinie[rand] * transaktionskosten_relativ) # Nur Transaktionskosten von Käufen über den Kredit werden gezählt
                                        kredit_aktiv = True
                                    elif kredit_aktiv:
                                        kreditlinie[rand] = kreditlinie[rand-1] + kredit * kredit_kondition # Zinsen werden addiert
                                        kredit_kurs[rand] = kredit_position[rand] * process[rand]
                                        kredit_position[rand] = kredit_position[rand-1]
                                    else:
                                        kreditlinie[rand] = 0.0
                            

                                    # Kauf/Verkauf/Bewegung der Position
                                    if signal[rand] == "Kauf" and possible[rand] == "möglich" and not rand == handelstage_gesamt-1:
                                        traded_ever = True
                                        transaktionskosten_kummuliert[rand] += (transaktionskosten + cash[rand-1] * transaktionskosten_relativ)  #nur zum Tracken der Kosten 
                                        position[rand] = (cash[rand-1]-(transaktionskosten + cash[rand-1] * transaktionskosten_relativ))/process[rand]   

                                    elif signal[rand] == "Verkauf" and possible[rand] == "möglich":
                                        position[rand] = 0
                                    else: 
                                        position[rand] = position[rand-1]

                                    # Cash
                                    if (signal[rand] == "Verkauf" and possible[rand] == "möglich") or (rand == handelstage_gesamt-1 and position[rand] > 0): #kredit_aktiv):
                                        cash[rand] = process[rand] * position[rand-1] - (transaktionskosten + (process[rand] * position[rand-1]) * transaktionskosten_relativ) 
                                        if (rand == handelstage_gesamt-1 and position[rand] > 0):
                                            sell_out = True
                                        position[rand] = 0
                                        transaktionskosten_kummuliert[rand] += (transaktionskosten + (process[rand] * position[rand-1]) * transaktionskosten_relativ)  
                                        if kredit_aktiv:
                                            kredit_cash[rand] = process[rand] * kredit_position[rand-1] - ((process[rand] * kredit_position[rand-1]) * transaktionskosten_relativ) #- transaktionskosten
                                            transaktionskosten_kummuliert[rand] += (process[rand] * kredit_position[rand-1]) * transaktionskosten_relativ 
                                            #transaktionskosten_kummuliert[rand] += transaktionskosten #Aktienpaket wird als eine Transaktion losgeschlagen (Trading und Kredit Aktien) daher keine extra kosten für Kredit-Aktien
                                            kredit_aktiv = False
                                            kredit_gewinn[rand] =  kredit_cash[rand] - kreditlinie[rand] 
                                            print("Kredit_Gewinn: " + str(kredit_gewinn[rand]))
                                            if kredit_reinvest:
                                                cash[rand] += kredit_gewinn[rand] # Gewinn/Verlust durch Kredit wird mit Cash verrechnet / Reinvestierbar # 1. Möglichkeit + Reinvestieren des Kreditgewinns
                                            kredit_gewinn_all += kredit_gewinn[rand]
                                    
                                    elif signal[rand] == "Kauf" and possible[rand] == "möglich" and not rand == handelstage_gesamt-1:
                                        cash[rand] = 0

                                    elif (rand == handelstage_gesamt-1 and position[rand] == 0) and kredit_aktiv:
                                        kredit_cash[rand] = process[rand] * kredit_position[rand-1] - (transaktionskosten + (process[rand] * kredit_position[rand-1]) * transaktionskosten_relativ)
                                        #transaktionskosten_kummuliert[rand] += transaktionskosten #Aktienpaket wird als eine Transaktion losgeschlagen (Trading und Kredit Aktien) daher keine extra kosten für Kredit-Aktien
                                        kredit_aktiv = False
                                        kredit_gewinn[rand] =  kredit_cash[rand] - kreditlinie[rand] 
                                        if kredit_reinvest:
                                            cash[rand] += kredit_gewinn[rand] # Gewinn/Verlust durch Kredit wird mit Cash verrechnet / Reinvestierbar # 1. Möglichkeit + Reinvestieren des Kreditgewinns
                                        kredit_gewinn_all += kredit_gewinn[rand]
                                        transaktionskosten_kummuliert[rand] += (transaktionskosten + (process[rand] * kredit_position[rand-1]) * transaktionskosten_relativ) 

                                    else: 
                                        cash[rand] = cash[rand-1] * (1 + cash_zins)
                                        kredit_cash[rand] = kredit_cash[rand-1]
                                

    


    # 1. Möglichkeit
                                if False: # 'bei Verkauf-Signalgrenze (mehrfache Kreditaufnahme möglich)' in kredit_rueckzahlung and not kredit_reinvest:
                                    #Kreditaufnahme
                                    transaktionskosten_kummuliert[rand] += transaktionskosten_kummuliert[rand-1]
                                    if kredit_ausloeser_signal and not kredit_aktiv:
                                        kreditlinie[rand] = kredit
                                        kredit_position[rand] = (kreditlinie[rand]-transaktionskosten)/process[rand]
                                        transaktionskosten_kummuliert[rand] += transaktionskosten
                                        kredit_aktiv = True
                                    elif kredit_aktiv:
                                        kreditlinie[rand] = kreditlinie[rand-1] + kredit * kredit_kondition # Zinsen werden addiert
                                        kredit_kurs[rand] = kredit_position[rand] * process[rand]
                                        kredit_position[rand] = kredit_position[rand-1]
                                    else:
                                        kreditlinie[rand] = 0.0
                            
                                    # Kauf/Verkauf/Bewegung der Position
                                    if signal[rand] == "Kauf" and possible[rand] == "möglich":
                                        #transaktionskosten_kummuliert[rand] += transaktionskosten_kummuliert[rand-1] + transaktionskosten
                                        transaktionskosten_kummuliert[rand] += transaktionskosten  #nur zum Tracken der Kosten 
                                        position[rand] = (cash[rand-1]-transaktionskosten)/process[rand]   

                                    elif signal[rand] == "Verkauf" and possible[rand] == "möglich":
                                        position[rand] = 0
                                        #transaktionskosten_kummuliert[rand] += transaktionskosten_kummuliert[rand-1] + transaktionskosten  #transaktionskosten werden unten in Cash berücksichtigt als kummuliert
                                    else: 
                                        position[rand] = position[rand-1]
                                        #transaktionskosten_kummuliert[rand] += transaktionskosten_kummuliert[rand-1]

                                    # Cash
                                    if (signal[rand] == "Verkauf" and possible[rand] == "möglich") or (rand == handelstage_gesamt-1 and kredit_aktiv):
                                        cash[rand] = process[rand] * position[rand-1] - transaktionskosten 
                                        transaktionskosten_kummuliert[rand] += transaktionskosten 
                                        if kredit_aktiv:
                                            kredit_cash[rand] = process[rand] * kredit_position[rand-1] - transaktionskosten
                                            transaktionskosten_kummuliert[rand] += transaktionskosten
                                            kredit_aktiv = False
                                            kredit_gewinn[rand] =  kredit_cash[rand] - kreditlinie[rand] 
                                            kredit_gewinn_all += kredit_gewinn[rand]
                                    elif signal[rand] == "Kauf" and possible[rand] == "möglich":
                                        cash[rand] = 0
                                    else: 
                                        cash[rand] = cash[rand-1]
                                        kredit_cash[rand] = kredit_cash[rand-1]

                                    # Cash ohne Transaktionskosten
                                    #if (signal[rand] == "Verkauf" and possible[rand] == "möglich") or (rand == handelstage_gesamt-1 and kredit_aktiv):
                                    #    cash[rand] = process[rand] * position[rand-1]
                                    #    if kredit_aktiv:
                                    #        kredit_cash[rand] = process[rand] * kredit_position[rand-1]
                                    #        kredit_aktiv = False
                                    #        kredit_gewinn[rand] =  kredit_cash[rand] - kreditlinie[rand] 
                                    #        kredit_gewinn_all += kredit_gewinn[rand]
                                    #elif signal[rand] == "Kauf" and possible[rand] == "möglich":
                                    #    cash[rand] = 0
                                    #else: 
                                    #    cash[rand] = cash[rand-1]
                                    #    kredit_cash[rand] = kredit_cash[rand-1]
                                

    # 1. Möglichkeit + Reinvestieren des Kreditgewinns
                                if False: #'bei Verkauf-Signalgrenze (mehrfache Kreditaufnahme möglich)' in kredit_rueckzahlung and kredit_reinvest:

                                    #Kreditaufnahme
                                    transaktionskosten_kummuliert[rand] += transaktionskosten_kummuliert[rand-1]
                                    if kredit_ausloeser_signal and not kredit_aktiv:
                                        kreditlinie[rand] = kredit
                                        kredit_position[rand] = (kreditlinie[rand]-transaktionskosten)/process[rand]
                                        transaktionskosten_kummuliert[rand] += transaktionskosten
                                        kredit_aktiv = True
                                    elif kredit_aktiv:
                                        kreditlinie[rand] = kreditlinie[rand-1] + kredit * kredit_kondition # Zinsen werden addiert
                                        kredit_kurs[rand] = kredit_position[rand] * process[rand]
                                        kredit_position[rand] = kredit_position[rand-1]
                                    else:
                                        kreditlinie[rand] = 0.0

                                    # Position aufbauen/abbauen, je nach Signal von oben (Signal + möglich)
                                    if signal[rand] == "Kauf" and possible[rand] == "möglich":
                                        transaktionskosten_kummuliert[rand] += transaktionskosten
                                        position[rand] = (cash[rand-1]-transaktionskosten)/process[rand]    

                                    elif signal[rand] == "Verkauf" and possible[rand] == "möglich":
                                        position[rand] = 0
                                    else: 
                                        position[rand] = position[rand-1]

                                    # Cash
                                    if (signal[rand] == "Verkauf" and possible[rand] == "möglich") or (rand == handelstage_gesamt-1 and kredit_aktiv):
                                        cash[rand] = process[rand] * position[rand-1] - transaktionskosten 
                                        transaktionskosten_kummuliert[rand] += transaktionskosten 
                                        if kredit_aktiv:
                                            kredit_cash[rand] = process[rand] * kredit_position[rand-1] - transaktionskosten
                                            transaktionskosten_kummuliert[rand] += transaktionskosten
                                            kredit_aktiv = False
                                            kredit_gewinn[rand] = kredit_cash[rand] - kreditlinie[rand] 
                                            cash[rand] += kredit_gewinn[rand] # Gewinn/Verlust durch Kredit wird mit Cash verrechnet / Reinvestierbar 
                                            kredit_gewinn_all += kredit_gewinn[rand]
                                    elif signal[rand] == "Kauf" and possible[rand] == "möglich":
                                        cash[rand] = 0
                                    else: 
                                        cash[rand] = cash[rand-1]
                                        kredit_cash[rand] = kredit_cash[rand-1]

        # 2. Möglichkeit

                                if 'zum Laufzeitende' in kredit_rueckzahlung:
                                    #Kreditaufnahme
                                    transaktionskosten_kummuliert[rand] += transaktionskosten_kummuliert[rand-1]
                                    transaktionskosten_kummuliert_kredit[rand] += transaktionskosten_kummuliert_kredit[rand-1]
                                    if kredit_ausloeser_signal and not kredit_aktiv and not kredit_ende and not rand == handelstage_gesamt-1:
                                        kreditlinie[rand] = kredit
                                        #kredit_position[rand] = (kreditlinie[rand]-(transaktionskosten + kreditlinie[rand] * transaktionskosten_relativ))/process[rand]
                                    
                                        if (signal[rand] == "Kauf" and possible[rand] == "möglich"):
                                            kredit_position[rand] = (kreditlinie[rand] - (kreditlinie[rand] * transaktionskosten_relativ))/process[rand]
                                            transaktionskosten_kummuliert[rand] += (kreditlinie[rand] * transaktionskosten_relativ)
                                       
                                        else:
                                            #transaktionskosten_kummuliert[rand] += transaktionskosten
                                            kredit_position[rand] = (kreditlinie[rand]-(transaktionskosten + kreditlinie[rand] * transaktionskosten_relativ))/process[rand]
                                            transaktionskosten_kummuliert_kredit[rand] += (transaktionskosten + kreditlinie[rand] * transaktionskosten_relativ)
                                           
                                 
                                        kredit_aktiv = True
                                    elif kredit_aktiv:
                                        kreditlinie[rand] = kreditlinie[rand-1] + kredit * kredit_kondition # Zinsen werden addiert
                                        kredit_kurs[rand] = kredit_position[rand] * process[rand]
                                        if kredit_ende:
                                            kredit_position[rand] = 0
                                        else:
                                            kredit_position[rand] = kredit_position[rand-1]
                                    else:
                                        kreditlinie[rand] = 0.0

                                    # Position aufbauen/abbauen, je nach Signal von oben (Signal + möglich)
                                    if signal[rand] == "Kauf" and possible[rand] == "möglich" and not rand == handelstage_gesamt-1:
                                        traded_ever = True
                                        transaktionskosten_kummuliert[rand] += (transaktionskosten + cash[rand-1] * transaktionskosten_relativ)  #nur zum Tracken der Kosten 
                                        position[rand] = (cash[rand-1]-(transaktionskosten + cash[rand-1] * transaktionskosten_relativ))/process[rand] 

                                    elif signal[rand] == "Verkauf" and possible[rand] == "möglich":
                                        position[rand] = 0
                                    else: 
                                        position[rand] = position[rand-1]

                                    # Cash
                                    if signal[rand] == "Verkauf" and possible[rand] == "möglich" or (rand == handelstage_gesamt-1 and position[rand] > 0): #and kredit_aktiv):
                                        cash[rand] = process[rand] * position[rand-1] - (transaktionskosten + (process[rand] * position[rand-1]) * transaktionskosten_relativ) 
                                        if (rand == handelstage_gesamt-1 and position[rand] > 0):
                                            sell_out = True
                                        transaktionskosten_kummuliert[rand] += (transaktionskosten + (process[rand] * position[rand-1]) * transaktionskosten_relativ)  
                                        position[rand] = 0
                                        
                                        if kredit_aktiv and not kredit_ende:
                                            kredit_cash[rand] = process[rand] * kredit_position[rand-1]
                                            kredit_aktiv = True # Der Kredit läuft weiter, die Rückzahlung erfolgt erst am Ende, nicht schon bei Verkauf, deshalb True
                                            kredit_gewinn_zw = kredit_cash[rand]
                                            if kredit_reinvest:
                                                cash[rand] += kredit_gewinn_zw
                                            kredit_ende = True  # einmaliger Kredit wurde verbraucht quasi

                                    elif signal[rand] == "Kauf" and possible[rand] == "möglich" and not rand == handelstage_gesamt-1:
                                        cash[rand] = 0

                                    elif (rand == handelstage_gesamt-1 and position[rand] == 0) and kredit_aktiv and not kredit_ende:
                                        
                                        kredit_cash[rand] = process[rand] * kredit_position[rand-1] - (transaktionskosten + (process[rand] * kredit_position[rand-1]) * transaktionskosten_relativ)  
                                        kredit_aktiv = True # Der Kredit läuft weiter, die Rückzahlung erfolgt erst am Ende, nicht schon bei Verkauf, deshalb True
                                        kredit_gewinn_zw = kredit_cash[rand]
                                        if kredit_reinvest:
                                                cash[rand] += kredit_gewinn_zw
                                        kredit_ende = True  # einmaliger Kredit wurde verbraucht quasi
                                        transaktionskosten_kummuliert[rand] += (transaktionskosten + (process[rand] * kredit_position[rand-1]) * transaktionskosten_relativ)  

                                    else: 
                                        cash[rand] = cash[rand-1] * (1 + cash_zins)
                                        kredit_cash[rand] = kredit_cash[rand-1]


                        

                            # Golden
                            if rand == handelstage_gesamt-1:
                                if sell_out:
                                    sell_out = False
                                    golden[rand] = cash[rand] + (transaktionskosten_kummuliert[rand]-transaktionskosten_kummuliert[rand-1]) #+ transaktionskosten
                                if not traded_ever:
                                    golden[rand] = 0
                                buy_and_hold_transaktionskosten_verkauf = (transaktionskosten + (process[rand] * buy_and_hold_position) * transaktionskosten_relativ)
                                buy_and_hold[rand] = process[rand] * buy_and_hold_position - (transaktionskosten + (process[rand] * buy_and_hold_position) * transaktionskosten_relativ)
                            elif position[rand] > 0:
                                golden[rand] = position[rand] * process[rand]
                            else:
                                golden[rand] = 0#cash[rand] 


    ### Ende eines jeden Simulationslaufes ### (letzer Handelstag)
        
                    # falls am Ende noch nicht verkauft wurde, wird es hier gemacht und der Kredit zurückgezahlt inkl. Zinsen    ggf. oben schon durchgeführt und hier obsolet     
                    if kredit_true:  
                        #if rand == (handelstage_gesamt-1) and kredit_aktiv and not kredit_ende:
                        #    kredit_cash[rand] = process[rand] * kredit_position[rand-1]
                        #    kredit_aktiv = True
                        #    kredit_gewinn_zw = kredit_cash[rand]
                        #    kredit_ende = True
                        if 'zum Laufzeitende' in kredit_rueckzahlung:
                            kredit_gewinn_all = kredit_gewinn_zw - kreditlinie[handelstage_gesamt-1]
                            kredit_gewinn[handelstage_gesamt-1] = kredit_gewinn_all


    ######### Übertragung der Endwerte #########
                        
                        betrag_kredit_gewinn_all += round(kredit_gewinn_all,2)
                        endwerte_sim[i][2] = kredit_gewinn_all # Trading nur mit Kredit

                        if kredit_reinvest:
                            kredit_gewinn_all = 0
                        #betragTS_mit_Leverage += round(golden[handelstage_gesamt-1]+kredit_gewinn_all,2)
                        ergebnis_array_kredit[1][1] += round(cash[handelstage_gesamt-1] + kredit_gewinn_all,2) #golden
                    
                        if (cash[handelstage_gesamt-1]+kredit_gewinn_all) > buy_and_hold[handelstage_gesamt-1]: #process[handelstage_gesamt-1]- 2*transaktionskosten: # 2mal minus transaktionskosten, da bei buy and hold am anfang und Ende die Aktie gekauft wird
                        #countTS_mit_leverage = countTS_mit_leverage +1
                            ergebnis_array_kredit[0][1] += 1
                        else:
                            #countBH_mit_leverage = countBH_mit_leverage +1
                            ergebnis_array_kredit[0][0] += 1

                        if not kredit_gewinn_all == 0:
                            countTS_kredit_aktiv += 1
                        if kredit_gewinn_all > 0:
                            countTS_Kredit_gewinn += 1


    #endwerte_sim[0][0] = BH-Endwert des ersten Simulationslaufs 
    #endwerte_sim[0][1] = TS-Endwert des ersten Simulationslaufs 
    #endwerte_sim[0][2] = Gewinn/Verlust nur durch Kredit bei TS über den ganzen ersten Simulationslauf                 

                    # Excel beispiel Rechnung zum nachvollziehen
                    if kredit_true: 
                        daten_klassisch = np.array([np.transpose(np.around(process, decimals=4)),np.transpose(np.around(buy_and_hold, decimals=4)), np.transpose(signal), np.transpose(possible), np.transpose(np.around(position, decimals=4)),np.transpose(np.around(cash, decimals=4)), np.transpose(np.around(golden, decimals=4)), np.transpose(np.around(kreditlinie, decimals=4)), np.transpose(np.around(kredit_position, decimals=4)), np.transpose(np.around(kredit_gewinn, decimals=4)), np.transpose(np.around(transaktionskosten_kummuliert, decimals=4)), np.transpose(np.around(transaktionskosten_kummuliert_kredit, decimals=4))])
                        column = ('Prozess', 'Buy and Hold', 'Signal', 'Kauf-Möglich?', 'Position (relativer Anteil vom Aktienkurs)', 'Cash-Bestand','Trading-Position', 'kreditlinie (zzgl. Zinsen)', 'Kredit-Position (relativer Anteil vom Aktienkurs)', 'Kredit_Gewinn', "Transaktionskosten_kummuliert", "Extra_Transaktionskosten_Kredit_Käufe")
                    else:
                        daten_klassisch = np.array([np.transpose(np.around(process, decimals=4)), np.transpose(np.around(buy_and_hold, decimals=4)), np.transpose(signal), np.transpose(possible), np.transpose(np.around(position, decimals=4)),np.transpose(np.around(cash, decimals=4)), np.transpose(np.around(golden, decimals=4)), np.transpose(np.around(transaktionskosten_kummuliert, decimals=4))])
                        column = ('Prozess', 'Buy and Hold', 'Signal', 'Kauf-Möglich?', 'Position (relativer Anteil vom Aktienkurs)', 'Cash-Bestand','Trading-Position', 'Transaktionskosten_kummuliert')
                    
                    daten_klassisch_transpose = np.transpose(daten_klassisch)
                    df3 = pd.DataFrame(data = daten_klassisch_transpose, columns = column)
                    df_array.append(df3)

                    daten_chart = np.transpose(np.around(process, decimals=4))
                    #column_chart = ("Kurs")
                    #df_chart = pd.DataFrame(data = np.transpose(daten_chart), columns = column_chart) 
                    kurs_trading_chart.append(daten_chart)
                    #csv_klassisch = df3.to_csv().encode('utf-8')
                 
                    endwerte_sim[i][0] = buy_and_hold[handelstage_gesamt-1] #process[handelstage_gesamt-1]-2*transaktionskosten # Buy and Hold
                    endwerte_sim[i][1] = cash[handelstage_gesamt-1] # Trading
                    endwerte_sim[i][3] = transaktionskosten_kummuliert[handelstage_gesamt-1]
                    endwerte_sim[i][4] = transaktionskosten_kummuliert_kredit[handelstage_gesamt-1]
                    endwerte_sim_ohne[i][0] = buy_and_hold[handelstage_gesamt-1] #process[handelstage_gesamt-1]-2*transaktionskosten # Buy and Hold
                    endwerte_sim_ohne[i][1] = cash[handelstage_gesamt-1]  # Trading
                    endwerte_sim_ohne[i][2] = transaktionskosten_kummuliert[handelstage_gesamt-1]
                    
                    #endwerte_sim_trading[i] = process[handelstage_gesamt-1]
                    #endwerte_sim_buyandhold[i] = golden[handelstage_gesamt-1]  

                    betragBH += round(buy_and_hold[handelstage_gesamt-1], 2) #round(process[handelstage_gesamt-1]-2*transaktionskosten,2)
                    betragTS += round(cash[handelstage_gesamt-1],2)
                    #betragBH_rund = round(betragBH,2)
                    #betragTS_rund = round(betragTS,2)
                    
                    if cash[handelstage_gesamt-1] > buy_and_hold[handelstage_gesamt-1]:  #process[handelstage_gesamt-1]-2*transaktionskosten:
                        #countTS = countTS +1
                        ergebnis_array[0][1] = ergebnis_array[0][1] + 1
                    else:
                        #countBH = countBH +1
                        ergebnis_array[0][0] = ergebnis_array[0][0] + 1
                   
                    ergebnis_array[3][0] += buy_and_hold_transaktionskosten_kauf + buy_and_hold_transaktionskosten_verkauf
                    ergebnis_array[3][1] += transaktionskosten_kummuliert[rand]
                    ergebnis_array[3][2] += transaktionskosten_kummuliert_kredit[rand]
                    transaktionskosten_array[i] = transaktionskosten_kummuliert[rand] 
                    transaktionskosten_array_kredit_only[i] = transaktionskosten_kummuliert_kredit[rand]

                    ergebnis_array[4][0] = price * np.exp(my * zeitraum) #erwarteter Schlusskurs
            

           #process[rand] = np.log(price) + m.exp((my - (sigma**2)/2) * t + sigma * m.sqrt(t) * norm.ppf(randomNum[rand]))

           # lognorm(tageschnitte_xx[rand], m.log(price)+(my+(sigma**2)/2)*rand*t, sigma * m.sqrt(rand*t))
            
           
            zw_prozess_1 = np.round( (np.log(price) + (my + (np.power(sigma,2))/2) * zeitraum),6) # ln(S0) + (µ + s²/2)*T 
            zw_prozess_2 = np.round(sigma * m.sqrt(zeitraum),6) # sigma * Wurzel(T)
            zw_prozess_3 = lognorm(ergebnis_array[4][0], zw_prozess_1, zw_prozess_2) 
            zw_prozess_4 = np.round(zw_prozess_3,6) #Prob(ST <= 149€)

            prozess_daten[0] = str(np.round( zw_prozess_1,2)) + "€" # ln(S0) + (µ + s²/2)*T 
            prozess_daten[1] = str(np.round( zw_prozess_2,2)) + "€" # sigma * Wurzel(T)
            prozess_daten[2] = str(np.round( zw_prozess_4 * 100,2)) + "%" #Prob(ST <= 149€)
            prozess_daten[3] = str(np.round((1 - zw_prozess_4)*100,2)) + "%" #Prob(ST > 149€)
            prozess_daten[4] = str(np.round(lognorminv(0.5, zw_prozess_1, zw_prozess_2),2)) + "€" #Median
            prozess_daten[5] = str(np.round((1 - lognorm((betragBH/anzahl_simulationen) ,zw_prozess_1, zw_prozess_2)) * 100,2)) + "%" #Prob(S > S(T)) bei "Buy and Hold"
            prozess_daten[6] = "Werte"
           



            ### Ende For Loop alle Simulationen durch ###   
            ### Ab hier: Auswertung der Ergebnisse ###
            st.session_state.prozess_daten = prozess_daten
            st.session_state.grunddaten = grunddaten
            st.session_state.ergebnis_array = ergebnis_array
            st.session_state.ergebnis_array_kredit = ergebnis_array_kredit
            st.session_state.endwerte_sim = endwerte_sim
            st.session_state.endwerte_sim_ohne = endwerte_sim_ohne
            st.session_state.anzahl_simulationen = anzahl_simulationen
            st.session_state.kredit_true = kredit_true
            st.session_state.betragBH = betragBH
            st.session_state.betragTS = betragTS
            st.session_state.betrag_kredit_gewinn_all = betrag_kredit_gewinn_all
            #st.session_state.csv_klassisch = csv_klassisch
            st.session_state.df3 = df_array #################################################
            st.session_state.kurs_trading_chart = kurs_trading_chart
            st.session_state.ausgewaehlte_strategie = ausgewaehlte_strategie
            st.session_state.transaktionskosten_array = transaktionskosten_array
            st.session_state.transaktionskosten_array_kredit_only = transaktionskosten_array_kredit_only
            st.session_state.reinvest = kredit_reinvest
     
            if "XX/YY Tagelinie" in ausgewaehlte_strategie:
                st.session_state.tageschnitte_xx = tageschnitte_xx
                st.session_state.tageschnitte_yy = tageschnitte_yy
                st.session_state.tageschnitte_zz = tageschnitte_zz
                st.session_state.signalgrenze_klein = signalgrenze_klein
                st.session_state.signalgrenze_groß = signalgrenze_groß
                st.session_state.kredit_ausloeser = kredit_ausloeser
                st.session_state.macd = 0
                st.session_state.macd_trigger = 0
                st.session_state.ema1 = 0
                st.session_state.ema2 = 0
                st.session_state.ema_trigger = 0
                st.session_state.macd_zero = False
            elif "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie:
                st.session_state.tageschnitte_xx = tageschnitte_xx
                st.session_state.tageschnitte_yy = 0
                st.session_state.tageschnitte_zz = 0
                st.session_state.signalgrenze_klein = signalgrenze_klein
                st.session_state.signalgrenze_groß = 0
                st.session_state.kredit_ausloeser = kredit_ausloeser
                st.session_state.macd = 0
                st.session_state.macd_trigger = 0
                st.session_state.ema1 = 0
                st.session_state.ema2 = 0
                st.session_state.ema_trigger = 0
                st.session_state.macd_zero = False
            elif "MACD" in ausgewaehlte_strategie:
                st.session_state.tageschnitte_xx = 0
                st.session_state.tageschnitte_yy = 0
                st.session_state.tageschnitte_zz = 0
                st.session_state.signalgrenze_klein = 0
                st.session_state.signalgrenze_groß = 0
                st.session_state.kredit_ausloeser = kredit_ausloeser
                st.session_state.macd = macd
                st.session_state.macd_trigger = macd_trigger
                st.session_state.ema1 = periodenlaenge_klein
                st.session_state.ema2 = periodenlaenge_groß
                st.session_state.ema_trigger = periodenlaenge_trigger
                st.session_state.macd_zero = macd_zero
            else:
                st.session_state.tageschnitte_xx = 0
                st.session_state.tageschnitte_yy = 0
                st.session_state.tageschnitte_zz = 0
                st.session_state.signalgrenze_klein = 0
                st.session_state.signalgrenze_groß = 0
                st.session_state.kredit_ausloeser = kredit_ausloeser
                st.session_state.macd = 0
                st.session_state.macd_trigger = 0
                st.session_state.ema1 = 0
                st.session_state.ema2 = 0
                st.session_state.ema_trigger = 0
                st.session_state.macd_zero = False

                
            #ergebnis_darstellung(ergebnis_array, ergebnis_array_kredit, endwerte_sim, endwerte_sim_ohne, anzahl_simulationen, kredit_true, betragBH, betragTS, betrag_kredit_gewinn_all, csv_klassisch, df3)
         # Ergebnis-Darstellungm, unabhängig ob Simulations-Button gedrückt wurde
        if not st.session_state.first_session:
         ergebnis_darstellung(st.session_state.prozess_daten, st.session_state.grunddaten, st.session_state.ergebnis_array, st.session_state.ergebnis_array_kredit, st.session_state.endwerte_sim, st.session_state.endwerte_sim_ohne, st.session_state.anzahl_simulationen, st.session_state.kredit_true, st.session_state.reinvest, st.session_state.betragBH, st.session_state.betragTS, st.session_state.betrag_kredit_gewinn_all, st.session_state.df3, st.session_state.kurs_trading_chart, st.session_state.ausgewaehlte_strategie, st.session_state.transaktionskosten_array, st.session_state.transaktionskosten_array_kredit_only, st.session_state.tageschnitte_yy, st.session_state.tageschnitte_xx, st.session_state.tageschnitte_zz, st.session_state.signalgrenze_klein, st.session_state.signalgrenze_groß, st.session_state.kredit_ausloeser, st.session_state.macd,  st.session_state.macd_trigger, st.session_state.ema_trigger, st.session_state.ema1, st.session_state.ema2, st.session_state.macd_zero)





### Diskrete Approximation ###
    if selected == "Simulation - Diskret":
        #st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
        diskret = '<p style="font-family:sans-serif; color:black; font-size: 30px;"><i>Simulation - Diskret (abzählbar)</i></p>'
        st.markdown(diskret, unsafe_allow_html=True)

        sigma_diskret = st.number_input('Volatilität/Sigma σ: ', 0.0, 1.0, value=0.2)
        mu_diskret = st.number_input('Müh σ: ', 0.0, 1.0, value=0.08)
        left_input, right_input = st.columns(2)
        with left_input:
            anzahl_basis = st.number_input('Basis T (Anzahl Bewegungen, 4=Quartalsweise, 12=Monatsweise...)', 1, 20, value=12)
            anzahl_down = st.number_input('Kaufen bei X Abwärtsbewegungen hintereinander', 0, 12)
        with right_input:
            start_kapital = st.number_input('Startkapital (in €)', 1, 10000, value=50)
            anzahl_up = st.number_input('Verkaufen bei X Aufwärtsbewegungen hintereinander',0,12)

        basis = 1/(anzahl_basis) #12
        startKapital = start_kapital
        optimale_Params_2 = np.zeros(shape=(500,6)) # 4096,12
        
        if st.button('Simulation durchführen'):
            v = 0
            up = kursentwicklung_up( sigma_diskret, basis)
            down = kursentwicklung_down(sigma_diskret, basis)    
            prop_up = ((mu_diskret/anzahl_basis)-(down-1))/((up-1)-(down-1))
            prop_down = 1 - prop_up

            my_bar_2 = st.progress(0)
         
            summe_buyAndHold_diskret_gewichtet = 0.0
            summe_trading_diskret_gewichtet = 0.0
            differenz = 0.0 #Endgültige Differenz Buy and Hold gegenüber Trading (inkl. Wahrscheinlichkeit bzw. mu)
            
            with st.spinner('Bitte warten...'):
                laenge = np.power(2,anzahl_basis)
                #print(laenge)
                verlaufArray = np.zeros(shape=(laenge,anzahl_basis)) # 4096,12
                ergebnis_array_diskret = np.zeros(shape=(laenge,2)) # 4096

                a = np.zeros(shape=(laenge,anzahl_basis)) #4096, 12
                #b = ["0"]*12           

                for t in range(laenge): #4096
                    x = str(binary(t, length=anzahl_basis))
                    for index, letter in enumerate(x):
                        if letter == "0":
                            a[t][index] = 0 
                            #c[t][index] = 'down'
                        else:
                            a[t][index] = 1
                            #c[t][index] = 'up'
                        #print(index, letter)

                for t in range(laenge): #4096
                    x = str(binary(t, length=anzahl_basis))
                    for index, letter in enumerate(x):
                        if letter == "0":
                            a[t][index] = 0 
                        else:
                            a[t][index] = 1

                # alle Kurse (4096 x 12) zu jedem Zeitpunkt berechnen
                endwerte = [0.0] * laenge #4096
                #endwerte_prop_bh = [0.0] * laenge #4096
                endwerte_prop = [0.0] * laenge #Wahrscheinlichkeiten für einen Kursverlauf unter berücksichtigung von mu/dem Drift
                differenz_prop = [0.0] * laenge #Differenzwert inkl. mu je Kursverlauf
                
                for t in range(laenge): #4096
                    wahrscheinlichkeit = 1.0
                    for d in range(anzahl_basis): #12
                        if a[t][d] == 0:
                            if d == 0:
                                verlaufArray[t][d] = startKapital * down 
                                wahrscheinlichkeit *= prop_down
                            else:
                                verlaufArray[t][d] = verlaufArray[t][d-1] * down 
                                wahrscheinlichkeit *= prop_down
                        else:
                            if d == 0:
                                verlaufArray[t][d] = startKapital * up 
                                wahrscheinlichkeit *= prop_up
                            else:
                                verlaufArray[t][d] = verlaufArray[t][d-1] * up 
                                wahrscheinlichkeit *= prop_up

                    endwerte_prop[t] = wahrscheinlichkeit
                    #endwerte_prop_bh[t] = verlaufArray[t][anzahl_basis-1] * wahrscheinlichkeit
                    endwerte[t] = round(verlaufArray[t][anzahl_basis-1], 8)  # 11, 2  Hier muss gerundet werden, evtl. schon früher da sonst mehr als 12 Entwerte herauskommen
             
                counter_indifferent_diskret = 0
                for z in range(laenge): #4096
                    comp = algoTrading(a[z], verlaufArray[z], anzahl_up, anzahl_down, anzahl_basis, start_kapital)
                    ergebnis_array_diskret[z][0] = comp
                    ergebnis_array_diskret[z][1] = endwerte[z]

                    differenz_prop[z] = (endwerte[z] - comp) * endwerte_prop[z]
                    differenz += differenz_prop[z]

                    bh_ergebnis_gewichtet = endwerte[z] * endwerte_prop[z]
                    td_ergebnis_gewichtet = comp * endwerte_prop[z]
                    summe_buyAndHold_diskret_gewichtet += endwerte[z] * endwerte_prop[z]
                    summe_trading_diskret_gewichtet += comp * endwerte_prop[z]

                    summe_buyAndHold_diskret += endwerte[z]
                    summe_trading_diskret += comp
                    if td_ergebnis_gewichtet > bh_ergebnis_gewichtet:
                        counter_trading_diskret += 1
                    if td_ergebnis_gewichtet < bh_ergebnis_gewichtet:
                        counter_buyAndHold_diskret += 1
                    if td_ergebnis_gewichtet == bh_ergebnis_gewichtet:
                        counter_indifferent_diskret += 1
                        summe_indifferent_diskret += comp
                    v += 1
                    my_bar_2.progress((v)/(laenge))


                daten_diskret = np.array([[counter_buyAndHold_diskret, counter_trading_diskret, counter_indifferent_diskret], [(counter_buyAndHold_diskret/(laenge - counter_indifferent_diskret))*100, (counter_trading_diskret/(laenge - counter_indifferent_diskret))*100, 0]])
                index_values2 = ['Höherer Schlusskurs (Häufigkeit):', 'Percentage of Outperformance in % (ohne Indifferenzen):']

                daten_diskret_betrag = np.array([[summe_buyAndHold_diskret_gewichtet, summe_trading_diskret_gewichtet], [differenz, 0]])
                index_values2_betrag = ['Höherer Schlusskurs (Betrag, Mittelwert):', 'Differenz:']
                
                
                df2 = pd.DataFrame(data = daten_diskret, 
                    index = index_values2, 
                    columns = ('Buy and Hold', 'Trading', 'Indifferent'))
                df_betrag = pd.DataFrame(data = daten_diskret_betrag, 
                    index = index_values2_betrag, 
                    columns = ('Buy and Hold', 'Trading'))

                df2.round(2)
                
                output = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Ergebnis (nach Häufigkeit):</i></p>'
                output_2 = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Ergebnis (nach Betrag):</i></p>'
                spalte_1, spalte_2 = st.columns(2)
                chart_data = pd.DataFrame(
                data = np.array([summe_buyAndHold_diskret_gewichtet, summe_trading_diskret_gewichtet]),
                columns=["Mittelwert der Schlusskurse"],
                index= ('Buy and Hold', 'Trading'))
    
            # csv = df2.to_excel("output.xlsx")
                #df2.to_csv().encode('utf-8')
                #csv = df2.to_csv().encode('utf-8')

                #c = alt.Chart(chart_data).mark_bar()
                #st.altair_chart(c, use_container_width=True)
                st.markdown("***")
                with spalte_1:
                    st.markdown(output, unsafe_allow_html=True)
                    st.dataframe(df2.style.format(subset=['Buy and Hold', 'Trading','Indifferent'], formatter="{:.0f}"))
                    df2_download = df2.to_csv().encode('utf-8')
                    st.download_button("Ergebnis als CSV/Excel herunterladen",df2_download,"file.csv","text/csv",key='download-csv')
                    
                   


                with spalte_2:
                    st.markdown(output_2, unsafe_allow_html=True)
                    st.dataframe(df_betrag.style.format(subset=['Buy and Hold', 'Trading'], formatter="{:.2f}€"))
                    df_betrag_download = df_betrag.to_csv().encode('utf-8')
                    st.download_button("Ergebnis als CSV/Excel herunterladen",df_betrag_download,"file.csv","text/csv",key='download-csv_2')
                    #st.bar_chart(chart_data)
                    
                    #st.markdown(get_table_download_link(df2), unsafe_allow_html=True)
        
        
           
       
    
            

 










            


def ergebnis_darstellung(prozess_daten, grunddaten, ergebnis_array, ergebnis_array_kredit, endwerte_sim, endwerte_sim_ohne, anzahl_simulationen, kredit_true, kredit_reinvest, betragBH, betragTS, betrag_kredit_gewinn_all, df3, kurs_trading_chart, ausgewaehlte_strategie, transaktionskosten_array, transaktionskosten_array_kredit_only, tageschnitte_yy, tageschnitte_xx, tageschnitte_zz, signalgrenze_klein, signalgrenze_groß, kredit_ausloeser, macd, macd_trigger, ema_trigger, ema1, ema2, macd_zero):

#Häufigkeiten
            ergebnis_array[0][2] = (ergebnis_array[0][0]/anzahl_simulationen)*100 # Häufigkeit relativ BH
            ergebnis_array[0][3] = 100 - ergebnis_array[0][2] # Häufigkeit relativ TS
            ergebnis_array[0][4] = ((ergebnis_array[0][3]/ergebnis_array[0][2]) - 1) * 100
            ergebnis_array_kredit[0][2] = (ergebnis_array_kredit[0][0]/anzahl_simulationen)*100 # Häufigkeit relativ BH
            ergebnis_array_kredit[0][3] = 100 - ergebnis_array_kredit[0][2] # Häufigkeit relativ TS
            ergebnis_array_kredit[0][4] = ((ergebnis_array_kredit[0][3]/ergebnis_array_kredit[0][2]) - 1) * 100
            
#Betrag
            ergebnis_array[1][0] = round(betragBH,2)
            ergebnis_array[1][1] = round(betragTS,2)
            quotient = (ergebnis_array[1][1])/(ergebnis_array[1][0])
            quotient_leverage = (ergebnis_array_kredit[1][1])/(ergebnis_array[1][0])
            ergebnis_array[1][3] = round(quotient*100,2) #relativ Betrag TS gegenüber 100% bzw. BH
            print(ergebnis_array[1][3])

            ergebnis_array[1][2] = round(100,2) # relativ BH (Benchmark mit 100%)
            ergebnis_array_kredit[1][0] = ergebnis_array[1][0] # Betrag BH (gleich wie bei ohne Kredit)
            ergebnis_array_kredit[1][3] = round(quotient_leverage*100,2) #relativ Betrag TS mit Kredit gegenüber 100% bzw. BH
            print(ergebnis_array_kredit[1][3])

            ergebnis_array_kredit[1][2] = round(100,2) # relativ BH mit Kredit (Benchmark mit 100%)
            ergebnis_array[1][4] = round((quotient-1) * 100, 2) 
            ergebnis_array_kredit[1][4] = round(((quotient_leverage-1)) * 100 ,2)

            ergebnis_array[2][0] = ergebnis_array[1][0]/anzahl_simulationen #Mittelwert Schlusskurse BH
            ergebnis_array[2][1] = ergebnis_array[1][1]/anzahl_simulationen #Mittelwert Schlusskurse Trading
            ergebnis_array_kredit[3][1] = ergebnis_array_kredit[1][1]/anzahl_simulationen #Mittelwert Schlusskurse Trading mit Kredit
            for h in range(int(anzahl_simulationen)):
                ergebnis_array[2][2] += np.power(endwerte_sim[h][0] - ergebnis_array[2][0],2) #Varianz Schlusskurse BH
                ergebnis_array[2][3] += np.power(endwerte_sim[h][1] - ergebnis_array[2][1],2) #Varianz Schlusskurse Trading
                if kredit_reinvest:
                    ergebnis_array_kredit[3][3] += np.power((endwerte_sim[h][1]) - ergebnis_array_kredit[3][1],2) #Varianz Schlusskurse Trading mit Kredit
                else:
                    ergebnis_array_kredit[3][3] += np.power((endwerte_sim[h][1] + endwerte_sim[h][2]) - ergebnis_array_kredit[3][1],2) #Varianz Schlusskurse Trading mit Kredit

            ergebnis_array[2][2] = np.sqrt(ergebnis_array[2][2]/anzahl_simulationen) #Standardabweichung
            ergebnis_array[2][3] = np.sqrt(ergebnis_array[2][3]/anzahl_simulationen)

            ergebnis_array_kredit[4][0] = ergebnis_array[3][0] #Transaktionskosten Buy and Hold Gesamt
            ergebnis_array_kredit[4][1] = ergebnis_array[3][2] + ergebnis_array[3][1]  #Transaktionskosten Trading Gesamt inkl. Kredit-Trading-Kosten
            ergebnis_array_kredit[4][2] = ergebnis_array_kredit[4][0]/anzahl_simulationen #Transaktionskosten Buy and Hold pro Simulation (Immer 2* transaktionskosten --> Buy and Sell at end)
            ergebnis_array_kredit[4][3] = ergebnis_array_kredit[4][1]/anzahl_simulationen # #Transaktionskosten Trading pro Simulation 

            ergebnis_array[3][2] = ergebnis_array[3][0]/anzahl_simulationen #Transaktionskosten Buy and Hold pro Simulation (Immer 2* transaktionskosten --> Buy and Sell at end)
            ergebnis_array[3][3] = ergebnis_array[3][1]/anzahl_simulationen # #Transaktionskosten Trading pro Simulation 
            ergebnis_array_kredit[3][3] = np.sqrt(ergebnis_array_kredit[3][3]/anzahl_simulationen) #Standardabweichung Trading mit Kredit
            ergebnis_array_kredit[3][0] = ergebnis_array[2][0] #Mittelwert BH (Wert wie bei ohne Kredit - identisch)
            ergebnis_array_kredit[3][2] = ergebnis_array[2][2] #Standardabweichung BH (Wert wie bei ohne Kredit - identisch)

            
            #if quotient_leverage >= 1:
            #    ergebnis_array_kredit[1][4] = round((1-(quotient_leverage))*100 ,2)
            #else:
            #    ergebnis_array_kredit[1][4] = round((1-(quotient_leverage))*-100 ,2)
            
            #betrag_kredit_gewinn_all_rund = round(betrag_kredit_gewinn_all,2)
            ergebnis_array_kredit[2][1] = round(betrag_kredit_gewinn_all,2)
  


### Ergebnisse präsentieren ###
            output = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Simulations-Ergebnisse:</i></p>'
            st.markdown(output, unsafe_allow_html=True)

### Ergebnisse ###
# ohne Kredit ergebnis_array
#[0][0-1] absolute Häufigkeit, 2  600 vs 400
#[0][2-3] relative Häufigkeit, 2  60% vs 40%
#[0][4] Performance Ts gegen BH,  -33,3%
#[1][0-1] absolute Summe der Schlusskurse, 2 15.000 vs 14.000
#[1][2-3] relative Summe der Schlusskurse, 2  100% vs 96%
#[1][4] Performance Ts gegen BH,  -4%
#[2][0-1] Mittelwert Schlusskurse
#[2][2-3] Standardabweichung Schlusskurse
#[3][0] Transaktionskosten BH immer 2*transaktionskosten, da Kauf und am Ende Verkauf Gesamt (alle Sims)
#[3][1] Transaktionskosten Trading Gesamt (alle Sims)
#[3][2] Transaktionskosten BH immer 2*transaktionskosten, da Kauf und am Ende Verkauf (DUrchschnitt)
#[3][3] Transaktionskosten Trading (DUrchschnitt)


# mit Kredit ergebnis_array_kredit
#[0][0-1] absolute Häufigkeit, 2  550 vs 450
#[0][2-3] relative Häufigkeit, 2  55% vs 45%
#[0][4] Performance Ts gegen BH,  -25,0%
#[1][0-1] absolute Summe der Schlusskurse, 2 15.000 vs 14.500
#[1][2-3] relative Summe der Schlusskurse, 2  100% vs 97,5%
#[1][4] Performance Ts gegen BH,  -2,5%
#[2][0] 0 Gewinn nur mit Kredit (BH)
#[2][1] Gewinn nur mit Kredit (TS)
#[3][0-1] Mittelwert Schlusskurse
#[3][2-3] Standardabweichung Schlusskurse

### check ###

# Vorschläge Performance Messung:
# Grunddaten nochmal auflisten, mu, vola und exp(St)...
# Nur für B&H Wahrscheinlichkeit S>St siehe Trading_Idea Excel
# Median und Durschnitts Kurs --> Kurse addieren und durch Anzahl Sims teilen
# durchschnittliche Gesamtrendite pro Simulation, 2x2 --> 20% vs 18% ((S(T)-S(0))/S(0) pro Sim. und dann den Durchschnitt oder umgekehrt)
# durchschnittliche Jahresrendite pro Simulation, 2x2 -||-

# Distance to B&H --> Wie groß ist der Kursunterschied am Ende einer jeden Sim. --> viele kleine Diffs oder wenige Große? --> evtl. als Balkendiagramm abbilden, z.B. >20, 10<20, <10...
# Vergleich der Max und Min werte, sprich höchste und niedrigster Kurs jeweils von allen Sim's

# Thema Statistische Signifikanz --> bezogen auf Anzahl an Simulationen
# Calmar Ratio --> Bei Trading dann nur die Tage in denen man investiert ist einbeziehen
# Maybe sharpe Ratio




            #End-Gesamtergebnisse als Tabelle  
          
            
    


            daten_häufigkeit = np.array([[ergebnis_array[0][0], ergebnis_array[0][1]], [ergebnis_array[0][2], ergebnis_array[0][3]], [0, ergebnis_array[0][4]]]) #Häufigkeit
            index_values = ['Vergleich: jeweils höherer Schlusskurs (Häufigkeit)', 'Vergleich: jeweils höherer Schlusskurs (in %)', 'Performance (Trading in %)']
            daten_betrag = np.array([ [ergebnis_array[1][0], ergebnis_array[1][1]], [ergebnis_array[1][2], ergebnis_array[1][3]], [0, ergebnis_array[1][4]], [ergebnis_array[2][0],ergebnis_array[2][1]], [ergebnis_array[2][2],ergebnis_array[2][3]],    [(ergebnis_array[2][0] - float(grunddaten[5])) ,(ergebnis_array[2][1]- float(grunddaten[5]))]    ,     [(np.power(((ergebnis_array[2][0])/float(grunddaten[5])), 1/float(grunddaten[0])) - 1)*100 , (np.power(((ergebnis_array[2][1])/float(grunddaten[5])), 1/float(grunddaten[0])) - 1)*100]      ,[ergebnis_array[3][0],ergebnis_array[3][1]], [ergebnis_array[3][2],ergebnis_array[3][3]] ]) #Betrag/Summe
            index_values_betrag = ['Schlusskurse in € (kummuliert)', 'Vergleich: Schlusskurse (in %)', 'Vergleich: Performance (Trading in %)', 'Mittelwert in € (erwartet: S0*EXP(µ*T) = '+str(np.round(ergebnis_array[4][0],2))+"€)", 'Standardabweichung', 'Profit in € (Mittelwert)', 'Rendite p.a. in %', 'Transaktionskosten in € (aller Simulationsläufe)', 'Transaktionskosten in € pro Simulationslauf']
            
            endwerte_sim_ohne_performance = np.zeros(shape=(int(anzahl_simulationen),4)) # 4096,12
            performance_diff_relativ = [0.0] * int(anzahl_simulationen)
            performance_diff_relativ_kredit = [0.0] * int(anzahl_simulationen)
            endwerte_sim_verteilung = np.zeros(shape=(3,int(anzahl_simulationen))) # 4096,12
            endwerte_sim_leverage = np.zeros(shape=(int(anzahl_simulationen),8)) # 4096,12
                


            if kredit_true:

                #End-Gesamtergebnisse als Tabelle  
                daten_kredit_häufigkeit = np.array([[ergebnis_array_kredit[0][0], ergebnis_array_kredit[0][1]], [ergebnis_array_kredit[0][2], ergebnis_array_kredit[0][3]], [0, ergebnis_array_kredit[0][4]]]) #Häufigkeit
                index_values_kredit = ['Vergleich: jeweils höherer Schlusskurs (Häufigkeit)', 'Vergleich: jeweils höherer Schlusskurs (in %)', 'Performance (Trading in %)']
                if kredit_reinvest:
                    daten_kredit_betrag = np.array([ [ergebnis_array_kredit[1][0], ergebnis_array_kredit[1][1]], [ergebnis_array_kredit[1][2], ergebnis_array_kredit[1][3]], [0, ergebnis_array_kredit[1][4]], [0, ergebnis_array_kredit[2][1]], [ergebnis_array_kredit[3][0], ergebnis_array_kredit[3][1]], [ergebnis_array_kredit[3][2],ergebnis_array_kredit[3][3]],     [(ergebnis_array_kredit[3][0] - float(grunddaten[5])) ,(ergebnis_array_kredit[3][1] - float(grunddaten[5]))],     [(np.power(((ergebnis_array_kredit[3][0])/float(grunddaten[5])), 1/float(grunddaten[0])) - 1)*100 ,(np.power(((ergebnis_array_kredit[3][1])/float(grunddaten[5])), 1/float(grunddaten[0])) - 1)*100],     [ergebnis_array_kredit[4][0],ergebnis_array_kredit[4][1]], [ergebnis_array_kredit[4][2],ergebnis_array_kredit[4][3]],  ]) #Betrag/Summe
                    index_values_kredit_betrag = ['Schlusskurse in € (kummuliert)', 'Vergleich: Schlusskurse (in %)', 'Vergleich: Performance (Trading in %)', 'Gewinn/Verlust durch Kredit in €',  'Mittelwert in € (erwartet: S0*EXP(µ*T) = '+str(np.round(ergebnis_array[4][0],2))+"€)", 'Standardabweichung', 'Profit in € (Mittelwert)','Rendite p.a. in %', 'Transaktionskosten in € (aller Simulationsläufe)', 'Transaktionskosten in € pro Simulationslauf']
                else:
                    daten_kredit_betrag = np.array([ [ergebnis_array_kredit[1][0], ergebnis_array[1][1], ergebnis_array_kredit[1][1]], [ergebnis_array_kredit[1][2], ergebnis_array[1][3], ergebnis_array_kredit[1][3]], [0, ergebnis_array[1][4], ergebnis_array_kredit[1][4]], [0,0, ergebnis_array_kredit[2][1]], [ergebnis_array_kredit[3][0],ergebnis_array[2][1], ergebnis_array_kredit[3][1]], [ergebnis_array_kredit[3][2],ergebnis_array[2][3],ergebnis_array_kredit[3][3]],     [(ergebnis_array_kredit[3][0] - float(grunddaten[5])), (ergebnis_array[2][1] - float(grunddaten[5])) ,(ergebnis_array_kredit[3][1] - float(grunddaten[5]))],     [(np.power(((ergebnis_array_kredit[3][0])/float(grunddaten[5])), 1/float(grunddaten[0])) - 1)*100 ,(np.power(((ergebnis_array[2][1])/float(grunddaten[5])), 1/float(grunddaten[0])) - 1)*100 ,(np.power(((ergebnis_array_kredit[3][1])/float(grunddaten[5])), 1/float(grunddaten[0])) - 1)*100],     [ergebnis_array_kredit[4][0],ergebnis_array[3][1],ergebnis_array_kredit[4][1]], [ergebnis_array_kredit[4][2],ergebnis_array[3][3],ergebnis_array_kredit[4][3]],  ]) #Betrag/Summe
                    index_values_kredit_betrag = ['Schlusskurse in € (kummuliert)', 'Vergleich: Schlusskurse (in %)', 'Vergleich: Performance (Trading in %)', 'Gewinn/Verlust durch Kredit in €',  'Mittelwert in € (erwartet: S0*EXP(µ*T) = '+str(np.round(ergebnis_array[4][0],2))+"€)", 'Standardabweichung', 'Profit in € (Mittelwert)','Rendite p.a. in %', 'Transaktionskosten in € (aller Simulationsläufe)', 'Transaktionskosten in € pro Simulationslauf']
                #    
                    
                #daten_kredit_betrag = np.array([ [ergebnis_array_kredit[1][0], ergebnis_array_kredit[1][1]], [ergebnis_array_kredit[1][2], ergebnis_array_kredit[1][3]], [0, ergebnis_array_kredit[1][4]], [0, ergebnis_array_kredit[2][1]], [ergebnis_array_kredit[3][0], ergebnis_array_kredit[3][1]], [ergebnis_array_kredit[3][2],ergebnis_array_kredit[3][3]], [ergebnis_array_kredit[4][0],ergebnis_array_kredit[4][1]], [ergebnis_array_kredit[4][2],ergebnis_array_kredit[4][3]],  ]) #Betrag/Summe
                #daten = np.array([[ergebnis_array_kredit[0][0], ergebnis_array_kredit[0][1]], [ergebnis_array[1][0], ergebnis_array[1][1]],[ergebnis_array[1][0],ergebnis_array_kredit[1][1] ], [0,ergebnis_array_kredit[2][1]]])
                #index_values = ['Vergleich: jeweils höherer Schlusskurs (Häufigkeit)','Vergleich: jeweils höherer Schlusskurs inkl. Leverage (Häufigkeit)', 'Vergleich: Schlusskurse (kummuliert)', 'Vergleich: Schlusskurse inkl. Leverage (kummuliert)', "Gewinn durch Leverage/Kredit"]
                
                if kredit_reinvest: 
                    data_endwerte_sim = endwerte_sim
                    #data_endwerte_sim[:,3] = 0
                    chart_data2 = pd.DataFrame(
                        data = np.array(data_endwerte_sim),
                        columns=["Buy and Hold", "Trading (inkl. Kredit)", "Kredit-Gewinn", "Transaktionskosten", "Extra_Transaktionskosten_Kredit_Käufe"],)
                else:
                    chart_data2 = pd.DataFrame(
                    data = np.array(endwerte_sim),
                    columns=["Buy and Hold", "Trading (mit Einbindung der Transaktionskosten)", "Kredit_Gewinn", "Transaktionskosten", "Extra_Transaktionskosten_Kredit_Käufe"],)


                col1, col2, col3, = st.columns(3)
                col1.metric("Buy and Hold als Benchmark (Mittelwert der Schlusskurse)", str(round(ergebnis_array[1][0]/anzahl_simulationen,2))+"€", str(np.round(((ergebnis_array[1][0]/(ergebnis_array[4][0]*anzahl_simulationen)-1)*100),2))+"% (vs. erwartet: " +str(np.round(ergebnis_array[4][0],2)) + ")")
                if kredit_reinvest:                
                    col2.metric("Trading (muss aus technischen Gründen separat simuliert werden)", "-")
                else:
                    col2.metric("Trading", str(round(ergebnis_array[1][1]/anzahl_simulationen,2))+"€", str(ergebnis_array[1][4])+"% (vs. Buy & Hold)")
                col3.metric("Trading inkl. Kredit-Gewinn", str(round(ergebnis_array_kredit[1][1]/anzahl_simulationen,2))+"€", str(ergebnis_array_kredit[1][4])+"% (vs. Buy & Hold)")
                

#########  Schlusskurse der Simulationen, auflisten in einem Array, inkl. Performance der Trading-Strategie gegenüber Benchmark  ################
                #Ergebnistabelle mit Kredit    
                
                for g in range(len(endwerte_sim_leverage)):
                    endwerte_sim_leverage[g][0] = endwerte_sim[g][0]
                    endwerte_sim_leverage[g][1] = endwerte_sim[g][1]
                    endwerte_sim_leverage[g][2] = endwerte_sim[g][2]

                    if kredit_reinvest:
                        endwerte_sim_leverage[g][3] = 0
                    else:
                        endwerte_sim_leverage[g][3] = round(endwerte_sim_leverage[g][1] + endwerte_sim_leverage[g][2], 2) 

                    endwerte_quotient = (endwerte_sim_leverage[g][1]/endwerte_sim_leverage[g][0]) 
                    endwerte_quotient_leverage = (endwerte_sim_leverage[g][3]/endwerte_sim_leverage[g][0]) 
                    relative_performance_alle = round(((endwerte_quotient-1))*100 ,2)
                    relative_performance_alle_leverage = round(((endwerte_quotient_leverage-1))*100 ,2)
                    #if endwerte_quotient >= 1:
                    #    relative_performance_alle = round((1-(endwerte_quotient))*-100 ,2)
                    #else:
                    #    relative_performance_alle = round((1-(endwerte_quotient))*-100 ,2)
                    #if endwerte_quotient_leverage >= 1:
                    #    relative_performance_alle_leverage = round((1-(endwerte_quotient_leverage))*-100 ,2)
                    #else:
                    #    relative_performance_alle_leverage = round((1-(endwerte_quotient_leverage))*-100 ,2)
                    endwerte_sim_leverage[g][4] = relative_performance_alle

                    if kredit_reinvest:
                        endwerte_sim_leverage[g][5] = 0
                    else:
                        endwerte_sim_leverage[g][5] = relative_performance_alle_leverage

                    endwerte_sim_leverage[g][6] = transaktionskosten_array[g]
                    endwerte_sim_leverage[g][7] = transaktionskosten_array_kredit_only[g]
                    performance_diff_relativ[g] = endwerte_sim_leverage[g][4]
                    performance_diff_relativ_kredit[g] = endwerte_sim_leverage[g][5]

                for tt in range(int(anzahl_simulationen)):
                    endwerte_sim_verteilung[0][tt] = endwerte_sim_ohne[tt][0]
                    endwerte_sim_verteilung[1][tt] = endwerte_sim_ohne[tt][1]
                    if kredit_reinvest:
                        endwerte_sim_verteilung[2][tt] = endwerte_sim_leverage[tt][1]
                    else:
                        endwerte_sim_verteilung[2][tt] = endwerte_sim_leverage[tt][3]
                        
                if kredit_reinvest:
                     df_gesamt = pd.DataFrame(data = endwerte_sim_leverage, 
                    columns = ('Buy and Hold',"Trading inkl. Leverage", "Leverage (Gewinn durch Kredit)", "-", "Trading Performance inkl. Leverage (gegenüber Benchmark)","--", "Transaktionskosten", "Transaktionskosten (Trades über Kredit)"))
                else:
                    df_gesamt = pd.DataFrame(data = endwerte_sim_leverage, 
                    columns = ('Buy and Hold', 'Trading', "Leverage (Gewinn durch Kredit)", "Trading (inkl. Leverage)", "Trading Performance (gegenüber Benchmark)","Trading Performance inkl. Leverage (gegenüber Benchmark)", "Transaktionskosten", "Transaktionskosten (Trades über Kredit)"))
                
                chart_data_diff_relativ = pd.DataFrame(
                    data = np.array(performance_diff_relativ),
                    columns=["Trading_Performance_gegenüber_Buy_and_Hold"],)
                chart_data_diff_relativ_kredit = pd.DataFrame(
                    data = np.array(performance_diff_relativ_kredit),
                    columns=["Trading_Performance_gegenüber_Buy_and_Hold_Kredit"],)
            else: 
                for g in range(len(endwerte_sim_ohne_performance)):
                    endwerte_sim_ohne_performance[g][0] = endwerte_sim_ohne[g][0]
                    endwerte_sim_ohne_performance[g][1] = endwerte_sim_ohne[g][1]
                    endwerte_quotient = (endwerte_sim_ohne[g][1]/endwerte_sim_ohne[g][0])
                    endwerte_sim_ohne_performance_alle = round(((endwerte_quotient-1))*100 ,2)
                    endwerte_sim_ohne_performance[g][2] = endwerte_sim_ohne_performance_alle
                    endwerte_sim_ohne_performance[g][3] = endwerte_sim_ohne[g][2]
                    performance_diff_relativ[g] = endwerte_sim_ohne_performance[g][2]

                for tt in range(int(anzahl_simulationen)):
                    endwerte_sim_verteilung[0][tt] = endwerte_sim_ohne[tt][0]
                    endwerte_sim_verteilung[1][tt] = endwerte_sim_ohne[tt][1]

                # Ergebnisse der Simulationsläufe für die Charts
                chart_data2 = pd.DataFrame(
                    data = np.array(endwerte_sim_ohne),
                    columns=["Buy and Hold", "Trading (mit Einbindung der Transaktionskosten)", "Transaktionskosten_kummuliert"],)
                col1, col2, = st.columns(2)
                col1.metric("Buy and Hold als Benchmark (Mittelwert der Schlusskurse)", str(round(ergebnis_array[1][0]/anzahl_simulationen,2))+"€", str(np.round(((ergebnis_array[1][0]/(ergebnis_array[4][0]*anzahl_simulationen)-1)*100),2))+"% (vs. erwartet: " +str(np.round(ergebnis_array[4][0],2)) + ")")
                col2.metric("Trading (Mittelwert der Schlusskurse)", str(round(ergebnis_array[1][1]/anzahl_simulationen,2))+"€", str(ergebnis_array[1][4])+"% (vs. Buy & Hold)")

                df_gesamt = pd.DataFrame(data = endwerte_sim_ohne_performance,  
                    columns = ('Buy and Hold', 'Trading', 'Trading Performance (gegenüber Benchmark)', 'Transaktionskosten'))

                chart_data_diff_relativ = pd.DataFrame(
                    data = np.array(performance_diff_relativ),
                    columns=["Trading_Performance_gegenüber_Buy_and_Hold"],)


###### Darstellung der Ergebnisse ########
            with st.expander("Ausgangsdaten & Einstellungen im Überblick"):
                df_grunddaten = pd.DataFrame(data = grunddaten, 
                        index= ('T', 'Anzahl Simulationen', "Handelstage p.a.", "Sigma", "µ", "Startkurs", "Transaktionskosten","Zufallszahlen", "Handelsstrategie", "Kreditoption", "Kreditgewinn reinvestierbar", "Kreditrückzahlung",'Konfiguration'))  
                df_grunddaten = np.transpose(df_grunddaten)
                df_grunddaten = df_grunddaten.set_index('Konfiguration')
               # st.markdown("Ausgangsdaten & Einstellungen")
                st.table(df_grunddaten) #.style.format(subset=['Buy and Hold', 'Trading'], formatter="{:.2f}"))


            with st.expander("Ergebnisse als Tabelle"):
                #Auflistung der Gesamtergebnisse
                #                
                st.markdown("Statistik-Kennzahlen in Bezug auf den Prozess")
                df_prozess = pd.DataFrame(data = prozess_daten, 
                    index = ('ln(S0) + (µ + sigma²/2)*T', 'sigma * Wurzel(T)', "Prob(ST <= 149€)", "Prob(ST > 149€)", "Median", "Prob(S > S(T)) bei Buy and Hold", "Werte"))
                df_prozess = np.transpose(df_prozess)
                df_prozess = df_prozess.set_index('Werte')
                st.table(df_prozess)
                #st.table(df_prozess.style.format(subset=['Werte'], formatter="{:.2f}"))



                links_H, rechts_B = st.columns(2)
                with links_H:
                    if not kredit_reinvest:
                        st.markdown("Ergebnisse: Häufigkeit")
                        df_häufigkeit = pd.DataFrame(data = daten_häufigkeit, 
                            index = index_values, 
                            columns = ('Buy and Hold', 'Trading'))
                        df_häufigkeit.round(2)
                        #st.dataframe(df_häufigkeit.style.format(subset=['Buy and Hold', 'Trading'], formatter="{:.2f}"))
                        st.table(df_häufigkeit.style.format(subset=['Buy and Hold', 'Trading'], formatter="{:.2f}"))
                    if kredit_true:
                        st.markdown("Ergebnisse: Häufigkeit (inkl. Kredit)")
                        df_kredit_häufigkeit = pd.DataFrame(data = daten_kredit_häufigkeit, 
                        index = index_values_kredit, 
                        columns = ('Buy and Hold', 'Trading'))
                        st.table(df_kredit_häufigkeit.style.format(subset=['Buy and Hold', 'Trading'], formatter="{:.2f}"))

                with rechts_B:
                    if kredit_true:
                        st.markdown("Ergebnisse: Betrag (inkl. Kredit beim Trading)")
                        if kredit_reinvest:
                            df_kredit_betrag = pd.DataFrame(data = daten_kredit_betrag, 
                            index = index_values_kredit_betrag, 
                            columns = ('Buy and Hold','Trading inkl. Kredit'))
                            st.table(df_kredit_betrag.style.format(subset=['Buy and Hold','Trading inkl. Kredit'], formatter="{:.2f}"))
                        else:
                            df_kredit_betrag = pd.DataFrame(data = daten_kredit_betrag, 
                            index = index_values_kredit_betrag, 
                            columns = ('Buy and Hold', 'Trading','Trading inkl. Kredit'))
                            st.table(df_kredit_betrag.style.format(subset=['Buy and Hold', 'Trading','Trading inkl. Kredit'], formatter="{:.2f}"))
                    else:
                        st.markdown("Ergebnisse: Betrag")
                        df_betrag = pd.DataFrame(data = daten_betrag, 
                        index = index_values_betrag, 
                        columns = ('Buy and Hold', 'Trading'))
                        st.table(df_betrag.style.format(subset=['Buy and Hold', 'Trading'], formatter="{:.2f}"))

                    
                st.markdown("***")
                #Auflistung der einzelnen Simulationsergebnisse
                st.markdown("Einzelergebnisse (Schlusskurse je Simulationslauf)")
                #st.dataframe(df_gesamt)#.style.format(subset=['Buy and Hold', 'Trading'], formatter="{:.2f}"))
                if kredit_true:
                    if kredit_reinvest:
                        
                        st.dataframe(df_gesamt.style.format({'Buy and Hold': '{:.2f}€', 'Trading inkl. Leverage': '{:.2f}€', "Leverage (Gewinn durch Kredit)": '{:.2f}€', "-": '{:.2f}€', "Trading Performance inkl. Leverage (gegenüber Benchmark)": '{:.2f}%', '--': '{:.2f}%', "Transaktionskosten": '{:.2f}€', "Transaktionskosten (Trades über Kredit)": '{:.2f}€'}, subset=['Buy and Hold', 'Trading inkl. Leverage',"Leverage (Gewinn durch Kredit)", "-", "--","Trading Performance inkl. Leverage (gegenüber Benchmark)", "Transaktionskosten", "Transaktionskosten (Trades über Kredit)"]))
                    else:
                        st.dataframe(df_gesamt.style.format({'Buy and Hold': '{:.2f}€', 'Trading': '{:.2f}€', "Leverage (Gewinn durch Kredit)": '{:.2f}€', "Trading (inkl. Leverage)": '{:.2f}€', 'Trading Performance (gegenüber Benchmark)': '{:.2f}%', "Trading Performance (gegenüber Benchmark)": '{:.2f}%', "Trading Performance inkl. Leverage (gegenüber Benchmark)": '{:.2f}%', "Transaktionskosten": '{:.2f}€', "Transaktionskosten (Trades über Kredit)": '{:.2f}€'}, subset=['Buy and Hold', 'Trading',"Leverage (Gewinn durch Kredit)", 'Trading Performance (gegenüber Benchmark)', "Trading (inkl. Leverage)", "Trading Performance (gegenüber Benchmark)","Trading Performance inkl. Leverage (gegenüber Benchmark)", "Transaktionskosten", "Transaktionskosten (Trades über Kredit)"]))
                else:
                    st.dataframe(df_gesamt.style.format({'Buy and Hold': '{:.2f}€', 'Trading': '{:.2f}€', 'Trading Performance (gegenüber Benchmark)': '{:.2f}%', 'Transaktionskosten': '{:.2f}€'}, subset=['Buy and Hold', 'Trading','Trading Performance (gegenüber Benchmark)','Transaktionskosten'])) #formatter={0: '{:.2f}', 1: '{:.2f}', 2: '{:.2f}%'})) #"{:.2f} %"))




            with st.expander("Simulations-Ergebnisse als Charts"):

                erklaerung_bar = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Bar-Chart: Vergleich "Trading vs. Buy and Hold" je Simulationslauf</i></p>'
                st.markdown(erklaerung_bar, unsafe_allow_html=True)
                st.bar_chart(chart_data2)


                erklaerung_bar = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Verteilungsdiagramm: "Trading vs. Buy and Hold" je Simulationslauf</i></p>'
                st.markdown(erklaerung_bar, unsafe_allow_html=True)
                if kredit_true:
                    hist_data = [endwerte_sim_verteilung[0], endwerte_sim_verteilung[1],endwerte_sim_verteilung[2]]
                    group_labels = [ "Buy and Hold", "Trading (Performance im Verhältnis zu Buy and Hold)", "Trading inkl. Kredit (Performance im Verhältnis zu Buy and Hold" ]
                    fig = ff.create_distplot(hist_data, group_labels, bin_size=[2,2,2], show_hist=False)
                    schnitt_bh = np.round(np.average(endwerte_sim_verteilung[0]),2)
                    schnitt_td = np.round(np.average(endwerte_sim_verteilung[1]),2)
                    schnitt_tk = np.round(np.average(endwerte_sim_verteilung[2]),2)
                    st.markdown("Mittelwerte: Buy and Hold: " + str(schnitt_bh)+ "€ | Trading: "+ str(schnitt_td)+"€ | Trading (inkl. Kredit): " +str(schnitt_tk)+"€" )
                    #st.markdown("Durchschnitt Buy and Hold: " + str(schnitt))
                    #st.markdown("Durchschnitt Buy and Hold: " + str(schnitt))
                else:     
                    hist_data = [endwerte_sim_verteilung[0], endwerte_sim_verteilung[1]]
                    group_labels = [ "Buy and Hold", "Trading (Performance im Verhältnis zu Buy and Hold)"]
                    fig = ff.create_distplot(hist_data, group_labels, bin_size=[2,2], show_hist=False)
                    schnitt_bh = np.round(np.average(endwerte_sim_verteilung[0]),2)
                    schnitt_td = np.round(np.average(endwerte_sim_verteilung[1]),2)
                    st.markdown("Mittelwerte: Buy and Hold: " + str(schnitt_bh)+ "€ | Trading: "+ str(schnitt_td)+"€")
                st.plotly_chart(fig, use_container_width=True)


                erklaerung_area = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Area-Chart: Vergleich "Trading vs. Buy and Hold" je Simulationslauf</i></p>'
                st.markdown(erklaerung_area, unsafe_allow_html=True)
                st.area_chart(chart_data2)
                erklaerung_line = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Line-Chart: Vergleich "Trading vs. Buy and Hold" je Simulationslauf</i></p>'
                st.markdown(erklaerung_line, unsafe_allow_html=True)
                st.line_chart(chart_data2)
                
                
            with st.expander("Trading-Performance im Verhältnis zu Buy and Hold (als Charts)"):
                erklaerung_line = '<p style="font-family:sans-serif; color:black; font-size: 20px;"><i>Performance-Vergleich: Trading gegenüber Buy and Hold als Benchmark</i></p>'
                st.markdown(erklaerung_line, unsafe_allow_html=True)
                erklaerung_line = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Performance Trading gegenüber Buy and Hold" je Simulationslauf</i></p>'
                st.markdown(erklaerung_line, unsafe_allow_html=True)
                st.bar_chart(chart_data_diff_relativ)
                if kredit_true and not kredit_reinvest:
                    erklaerung_line = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i> ...inkl. Kredit</i></p>'
                    st.markdown(erklaerung_line, unsafe_allow_html=True)
                    st.bar_chart(chart_data_diff_relativ_kredit)
                
                #st.markdown("***")
                erklaerung_line = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Verteilungsdiagramm: Performance Trading gegenüber Buy and Hold</i></p>'
                st.markdown(erklaerung_line, unsafe_allow_html=True)
                if kredit_true:
                    if kredit_reinvest:
                        hist_data = [performance_diff_relativ]
                        group_labels = [ "Trading inkl. Kredit (Performance im Verhältnis zu Buy and Hold" ]
                        fig = ff.create_distplot(hist_data, group_labels, bin_size=[1,1], show_hist=False)
                        #fig.add_violin()
                        schnitt = np.round(np.average(performance_diff_relativ),2)
                        st.markdown("Durchschnittliche Performance Differenz von Trading gegenüber Buy and Hold: " + str(schnitt) + "€")

                    else:
                        hist_data = [performance_diff_relativ, performance_diff_relativ_kredit]
                        group_labels = [ "Trading (Performance im Verhältnis zu Buy and Hold", "...inkl. Kredit" ]
                        fig = ff.create_distplot(hist_data, group_labels, bin_size=[2,2], show_hist=False)
                        #fig.add_violin()
                        schnitt = np.round(np.average(performance_diff_relativ),2)
                        schnitt_kredit = np.round(np.average(performance_diff_relativ_kredit),2)
                        st.markdown("Durchschnittliche Performance Differenz von Trading gegenüber Buy and Hold: " + str(schnitt) + "€ | inkl. Kredit: " + str(schnitt_kredit)+"€")

                else:
                    hist_data = [performance_diff_relativ]
                    #print(np.average(performance_diff_relativ))
                    group_labels = [ "Trading (Performance im Verhältnis zu Buy and Hold"]
                    fig = ff.create_distplot(hist_data, group_labels, bin_size=[2], show_hist=False)
                    schnitt = np.round(np.average(performance_diff_relativ),2)
                    st.markdown("Durchschnittliche Performance Trading gegenüber Buy and Hold: " + str(schnitt)+ "€")
                    #fig_version_2 = px.histogram(performance_diff_relativ, marginal="box",) # or violin, rug
                    #st.plotly_chart(fig_version_2, use_container_width=True)
                st.plotly_chart(fig, use_container_width=True)
                   
                                    

                # Group data together
                #dd = performance_diff_relativ
                #hist_data = [[dd]]

                # Create distplot with custom bin_size
                #fig = ff.create_distplot(
                #        hist_data, group_labels, bin_size=[.15])
                
                #hist_data = [performance_diff_relativ]
                #group_labels = [ "Ohne" ]
                #fig = ff.create_distplot(hist_data, group_labels, bin_size=[2])
                #st.plotly_chart(fig, use_container_width=True)

                #erklaerung_line = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Performance-Übersicht: "Trading vs. Buy and Hold" je Simulationslauf</i></p>'
                #st.markdown(erklaerung_line, unsafe_allow_html=True)
                #st.bar_chart(chart_data_diff_relativ)
                #if kredit_true:
                #    erklaerung_line = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i> ...inkl. Kredit</i></p>'
                #    st.markdown(erklaerung_line, unsafe_allow_html=True)
                #    st.bar_chart(chart_data_diff_relativ_kredit)

           

            with st.expander("Downloads "):
                if "XX/YY Tagelinie" in ausgewaehlte_strategie:
                    if kredit_true:
                        tageschnitte = np.zeros(shape=(int(len(tageschnitte_xx)),4))
                        for t in range(len(tageschnitte)):
                            tageschnitte[t][0] = tageschnitte_yy[t]
                            tageschnitte[t][1] = tageschnitte_xx[t]
                            tageschnitte[t][2] = tageschnitte_zz[t]
                            tageschnitte[t][3] = kurs_trading_chart[int(anzahl_simulationen)-1][t]

                        chart_data_tageschnitte = pd.DataFrame(
                            data = np.array(tageschnitte),
                            columns=[str(signalgrenze_groß)+"-Tagelinie", str(signalgrenze_klein)+"-Tagelinie", str(kredit_ausloeser)+"-Tagelinie", "Kurs"],)
                    else:
                        tageschnitte = np.zeros(shape=(int(len(tageschnitte_xx)),3))
                        for t in range(len(tageschnitte)):
                            tageschnitte[t][0] = tageschnitte_yy[t]
                            tageschnitte[t][1] = tageschnitte_xx[t]
                            tageschnitte[t][2] = kurs_trading_chart[int(anzahl_simulationen)-1][t] #df3[int(anzahl_simulationen)-1][0]

                        chart_data_tageschnitte = pd.DataFrame(
                            data = np.array(tageschnitte),
                            columns=[str(signalgrenze_groß)+"-Tagelinie", str(signalgrenze_klein)+"-Tagelinie", "Kurs"],)

                    erklaerung_tageslinien = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Line-Chart: Die beiden Tageslinien des letzten Simulationslaufes</i></p>'
                    st.markdown(erklaerung_tageslinien, unsafe_allow_html=True)
                    st.line_chart(chart_data_tageschnitte)

                elif "XX Tagelinie als Kurs-Basis für Signalgrenzen mit Wahrscheinlichkeiten" in ausgewaehlte_strategie:

                    tageschnitte = np.zeros(shape=(int(len(tageschnitte_xx)),2))
                    for t in range(len(tageschnitte)):
                        tageschnitte[t][0] = tageschnitte_xx[t]
                        tageschnitte[t][1] = kurs_trading_chart[int(anzahl_simulationen)-1][t]
                    chart_data_tageschnitte = pd.DataFrame(
                        data = np.array(tageschnitte),
                        columns=[str(signalgrenze_klein)+"-Tagelinie", "Kurs"],)

                    erklaerung_tageslinien = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Line-Chart: Die beiden Tageslinien des letzten Simulationslaufes</i></p>'
                    st.markdown(erklaerung_tageslinien, unsafe_allow_html=True)
                    st.line_chart(chart_data_tageschnitte)


                elif "MACD" in ausgewaehlte_strategie:
                   # if kredit_true: #hier kein extra Variable bei Kredit-Fall --> keine EInstellungen möglich da bei MACD einfach nicht sinnvoll bzw. möglich
                    if macd_zero:
                        macd_linien = np.zeros(shape=(int(len(macd)),2))
                        for t in range(len(macd_linien)):
                            macd_linien[t][0] = macd[t]
                            macd_linien[t][1] = macd_trigger[t]
                        chart_data_macd_linien = pd.DataFrame(
                            data = np.array(macd_linien),
                            columns=[str(ema1)+"/"+str(ema2)+"-MACD", str(ema_trigger)+"-MACD-Trigger"],)
                    else: # kein extra EMA-Trigger
                        macd_linien = np.zeros(shape=(int(len(macd)),1))
                        for t in range(len(macd_linien)):
                            macd_linien[t][0] = macd[t]
                        chart_data_macd_linien = pd.DataFrame(
                            data = np.array(macd_linien),
                            columns=[str(ema1)+"/"+str(ema2)+"-MACD"],)

                    erklaerung_tageslinien = '<p style="font-family:sans-serif; color:black; font-size: 18px;"><i>Line-Chart: Der Verlauf der MACD und MACD-Trigger Linie des letzten Simulationslaufes</i></p>'
                    st.markdown(erklaerung_tageslinien, unsafe_allow_html=True)
                    st.line_chart(chart_data_macd_linien)
                    
                    
                    #st.download_button(
                    #"Verlauf der allerletzten Simulation als CSV/Excel herunterladen (Zweck: Veranschaulichung der Simulation)",
                    #csv_klassisch,
                    #"file.csv",
                    #"text/csv",
                    #key='download-csv'
                    #)
                st.dataframe(df3[int(anzahl_simulationen)-1])
                grunddaten_download = df_grunddaten.to_csv().encode('utf-8')
                st.download_button(  "Simulationskonfiguration",
                        grunddaten_download,
                        "file.csv",
                        "text/csv",
                        key='download-csv-konfig')

                for p in range(int(anzahl_simulationen)):
                    csv_klassisch = df3[p].to_csv().encode('utf-8')
                    st.download_button(
                        "Simulation Nr. "+str(p),
                        csv_klassisch,
                        "file.csv",
                        "text/csv",
                        key='download-csv'+str(p))











#def get_table_download_link(df):
#    #Generates a link allowing the data in a given panda dataframe to be downloaded
#    #in:  dataframe
#    #out: href string
#    csv = df.to_excel("output.xlsx")
#    #b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
#    href = f'<a href="data:file/xlsx;base64,{csv}">Download csv file</a>'
#    return href


def kursentwicklung_up(sigma, basis):
    up_1 = np.exp(sigma * np.sqrt(basis))
    #print(up_1)
    return up_1


def kursentwicklung_down(sigma, basis):
    down_1 = np.exp(-sigma * np.sqrt(basis))
    #print(down_1)
    return down_1

def algoTrading(array1, kurs, ups, downs, anzahl_basis2, start_kapital): # 6 - 0
    #strategie = 3
    strategie_ups = ups
    strategie_downs = downs
    kapital = start_kapital #50.00 # entweder realitätsnah, indem Aktien stückelbar sind und gewinne reinvestiert werden oder man nimmt den profit/verlust immer raus und kuaft/verkauft zu dem kurs, egal wie viel gesamtkapital man hat
    anteil = 1.0
    market_in = False 
    if strategie_ups == 0 and strategie_downs == 0: # D.h. immer direkt Verkaufen und Kaufen --> 50€ 
        return round(kapital,2)

    for u in range((anzahl_basis2)): # 12
        trading_buy = True
        trading_sell = True

        # For downs --> wann kaufen  
        if u >= strategie_downs-1:
            for e in range(strategie_downs):
                if array1[u - e] == 1:
                    trading_buy = False
            if trading_buy and not market_in:
                # buy
                anteil = kapital/kurs[u]
                market_in = True

        # For ups --> wann verkaufen
        if u >= strategie_ups-1:
            for e in range(strategie_ups):
                if array1[u - e] == 0:
                    trading_sell = False
            if trading_sell and market_in:
                # sell
                market_in = False
                #kapital = kurs[u]

        if market_in:  # Platzierung evtl. oberhalb sinnvoller?
            kapital = anteil * kurs[u]

        # if u >= strategie-1:  # Old Stuff bei einer Strategie (parralell up/down)
        #      trading_buy = True
        #  trading_sell = True
        #  for e in range(strategie):
        #      if array1[u - e] == 1:
        #          trading_buy = False
        #      if array1[u - e] == 0:
        #          trading_sell = False
        #  if trading_buy and not market_in:
        #    # buy
        #      anteil = kapital/kurs[u]
        #     market_in = True
        # if trading_sell and market_in:
        #     # sell
        #     market_in = False
        #     #kapital = kurs[u]

    #print(kapital)
    return round(kapital,4) #ergebnis








if __name__ == "__main__":
    main()