import pandas as pd
import requests
from datetime import datetime
import time
import pandas_ta as ta 
import numpy as np
import pytz

'''
###################################################################################
[Proposito]: Funcion para limpiar la entrada de la informacion del cliente y proveer la informacion de cuenta
[Parametros]: symbol(Stock por la cual se quiere filtrar, Ejemplo : USDT), cliente (Informacion del cliente de bybit)
[Retorna]: Retorna valor 'float' del balance de la moneda asignada por parametro en la cuenta
###################################################################################
'''
def Get_Balance(cliente,symbol: str):
    filt_Balance = 0
    while(filt_Balance == 0):
        balance = cliente.Wallet.Wallet_getBalance(coin=symbol).result()
        if balance is not None:
            filt_Balance = balance[0].get('result').get(symbol).get('available_balance')
        else:
            filt_Balance = 0
            
    return filt_Balance

'''
###################################################################################
[Proposito]: Funcion para obtener informacion cada minuto de una moneda en especifico
[Parametros]: symbol (Simbolo de la moneda que se quiere analizar, Ejemplo : BTCUSDT)
[Retorno]: Dataframe de pandas con la informacion solicitada
###################################################################################
'''
def get_data(symbol: str,interval: str,unixtimeinterval: int = 1080000):

  list_registers = []
  DATA_200 = 180000
  now = datetime.now()
  unixtime = int(time.mktime(now.timetuple()))
  since = unixtime
  while(unixtimeinterval != 0):
    start= str(since - unixtimeinterval)
    url = 'http://api.bybit.com/public/linear/kline?symbol='+symbol+'&interval='+interval+'&from='+str(start)
    data = requests.get(url).json()
    df = pd.DataFrame(data['result'])
    df = df.drop_duplicates()
    df['open_time'] = df['open_time'].apply(lambda x: datetime.fromtimestamp(x, tz=pytz.UTC))
    target_timezone = pytz.timezone('Etc/GMT+5')
    df['open_time'] = df['open_time'].apply(lambda x: x.astimezone(target_timezone))
    df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume','open_time':'Time'}, inplace=True)
    df = df.drop(columns=['symbol','interval','period','turnover','start_at','id'])
    list_registers.append(df)
    unixtimeinterval = unixtimeinterval - DATA_200
    
  concatenated_df = pd.concat([list_registers[0], list_registers[1], list_registers[2], list_registers[3], list_registers[4], list_registers[5]], axis=0)
  concatenated_df = concatenated_df.reset_index(drop=True)

  return concatenated_df

'''
###################################################################################
[Proposito]: Funcion para calcular las lineas que representan el SuperTrend superior e inferior y sus etiquetas
[Parametros]: symbol (String que representa la moneda a la que se va a suscribir), df (Dataframe con la informacion del activo), mult (Multiplicador para calcular SuperTrend)
[Retorno]: Retorna el dataframe modificado, con columnas añadidas 
###################################################################################

'''
def CalculateSupertrend(data: pd.DataFrame):
  Temp_Trend = ta.supertrend(
    high= data['High'], 
    low = data['Low'], 
    close = data['Close'], 
    period=10, 
    multiplier=3)
  Temp_Trend = Temp_Trend.rename(columns={'SUPERT_7_3.0':'Supertrend','SUPERTd_7_3.0':'Polaridad','SUPERTl_7_3.0':'ST_Inferior','SUPERTs_7_3.0':'ST_Superior'})
  df_merge = pd.merge(data,Temp_Trend,left_index=True, right_index=True)
  df_merge['DEMA800'] = ta.dema(df_merge['Close'], length=800)
  return df_merge




def Trading(symb: str, interval: str,client):
  Polaridad = "" #Valor del close para comparar registros y evitar repeticiones
  Cont = 0 #Contador para poder generar registros consecutivos en archivos externos
  while(True):
    df = get_data(symb, interval)
    df = CalculateSupertrend(df)
    time.sleep(10)
    edit = open("PATH" + str(Cont) + ".txt",'w')
    if(Polaridad != df['Polaridad'].iloc[-1]):
      '''
      Caso 1 : Para compra long en futures
      '''
      if(df['Close'].iloc[-1] >= df['Supertrend'].iloc[-1] and df['Polaridad'].iloc[-1] == 1):
        if(df['Close'].iloc[-1] >= df['DEMA800'].iloc[-1]):
          edit.write("3_L| " + str(df['Time'].iloc[-1]) + " | LONG \n")
          #cantidad = float(Get_Balance(client,'USDT'))
          #client.LinearOrder.LinearOrder_new(side='Buy', symbol='ETHUSDT', qty=cantidad*0.02, order_type='Market', time_in_force='GoodTillCancel', reduce_only=False, close_on_trigger=False, order_link_id=None, take_profit= str(int(WinRate_L)), stop_loss= str(Stoploss_L), tp_trigger_by='LastPrice', sl_trigger_by='MarkPrice', price=None).result()
          res = client.LinearOrder.LinearOrder_new(side='Buy', 
                                                   symbol=symb, 
                                                   qty=0.01, 
                                                   order_type='Market', 
                                                   time_in_force='GoodTillCancel', 
                                                   reduce_only=False, 
                                                   close_on_trigger=False, 
                                                   order_link_id=None, 
                                                   stop_loss= str(df['Supertrend'].iloc[-1]), 
                                                   tp_trigger_by='LastPrice', 
                                                   sl_trigger_by='MarkPrice', 
                                                   price=None).result()
          
          edit.write(str(res))
          Cont += 1
          Polaridad = df['Polaridad'].iloc[-1]
          if(Cont >= 10):
            Cont = 0
          
      '''
      Caso 2 : Para compra shorts en futures
      '''
      if(df['Close'].iloc[-1] <= df['Supertrend'].iloc[-1] and df['Polaridad'].iloc[-1] == -1):
        if(df['Close'].iloc[-1] <= df['DEMA800'].iloc[-1]):
          edit.write("3_S| " + str(df['Time'].iloc[-1]) + " | SHORT \n")
          res = client.LinearOrder.LinearOrder_new(side='Sell', 
                                                   symbol=symb, 
                                                   qty=0.01, 
                                                   order_type='Market', 
                                                   time_in_force='GoodTillCancel', 
                                                   reduce_only=False, 
                                                   close_on_trigger=False, 
                                                   order_link_id=None, 
                                                   stop_loss= str(df['Supertrend'].iloc[-1]), 
                                                   tp_trigger_by='LastPrice', 
                                                   sl_trigger_by='MarkPrice', 
                                                   price=None).result()
          edit.write(str(res))
          Cont += 1
          Polaridad = df['Polaridad'].iloc[-1]
          if(Cont >= 10):
            Cont = 0
            
            
      edit.close()  
          
      
    
