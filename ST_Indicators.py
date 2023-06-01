import pandas as pd
import requests
from datetime import datetime
import time
import pandas_ta as ta 
import numpy as np
import pytz
import Posicion

PATH = ""

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

        
def EscribirRegistros(Contador : int, df : pd.DataFrame, tipo: str, side: str, mensaje: str):
  edit = open(PATH + str(Contador) + ".txt",'w')
  #Si la operacion que se hizo fue abrir una posicion
  if(tipo == 'Open'):
    #Escribir registros de un Close
    if(side == 'Buy'):
      edit.write("Open| " + str(df['Time'].iloc[-1]) + " | LONG \n")
      edit.write(mensaje)
      edit.write("Close_Price: {Price}, Supertrend: {Supertrend}, Polaridad: {Polaridad}".format(Price = str(df['Close'].iloc[-1]),
                                                                                                 Supertrend = str(df['Supertrend'].iloc[-1]),
                                                                                                 Polaridad = str(df['Polaridad'].iloc[-1])))
      edit.write("#FIN#")
      
      Contador += 1
      edit.close()
      return Contador
      
    #Escribir registros de un Short  
    if(side == 'Sell'):
      edit.write("Open| " + str(df['Time'].iloc[-1]) + " | SHORT \n")
      edit.write(mensaje)
      edit.write("Close_Price: {Price}, Supertrend: {Supertrend}, Polaridad: {Polaridad}".format(Price = str(df['Close'].iloc[-1]),
                                                                                                 Supertrend = str(df['Supertrend'].iloc[-1]),
                                                                                                 Polaridad = str(df['Polaridad'].iloc[-1])))
      edit.write("#FIN#")
      
      Contador += 1
      edit.close()
      return Contador  
    
  #Si la operacion que se hizo fue cerrar una posicion    
  elif(tipo == 'Close'):
    if(side == 'Buy'):
      edit.write("Close| " + str(df['Time'].iloc[-1]) + " | LONG \n")
      edit.write(mensaje)
      edit.write("Close_Price: {Price}, Supertrend: {Supertrend}, Polaridad: {Polaridad}".format(Price = str(df['Close'].iloc[-1]),
                                                                                                 Supertrend = str(df['Supertrend'].iloc[-1]),
                                                                                                 Polaridad = str(df['Polaridad'].iloc[-1])))
      edit.write("#FIN#")
      
      Contador += 1
      edit.close()
      return Contador 
      
    if(side == 'Sell'):
      
      edit.write("Close| " + str(df['Time'].iloc[-1]) + " | SHORT \n")
      edit.write(mensaje)
      edit.write("Close_Price: {Price}, Supertrend: {Supertrend}, Polaridad: {Polaridad}".format(Price = str(df['Close'].iloc[-1]),
                                                                                                 Supertrend = str(df['Supertrend'].iloc[-1]),
                                                                                                 Polaridad = str(df['Polaridad'].iloc[-1])))
      edit.write("#FIN#")
      
      Contador += 1
      edit.close()
      return Contador 
    
  
  else:
    print("La solicitud es incorrecta")
    edit.close()  
    return Contador
  
  
def Revisar_Arreglo(arr, df : pd.DataFrame, client, contador : int):
  if(len(arr) != 0 or contador == 0):
    for posicion in arr:
      if(posicion.label != df['Polaridad'].iloc[-1]):
        res = posicion.close_order(client)
        EscribirRegistros(contador,df,'Close', posicion.side, str(res))
    


def Trading(symb: str, interval: str,client):
  Polaridad = "" #Valor del close para comparar registros y evitar repeticiones
  Cont = 0 #Contador para poder generar registros consecutivos en archivos externos
  posicion_list = [] #Lista que contendra las ordenes 
  while(True):
    time.sleep(10)
    df = get_data(symb, interval)
    df = CalculateSupertrend(df)
    Revisar_Arreglo(posicion_list,df,client,Cont)
    if(Polaridad != df['Polaridad'].iloc[-1]):
      '''
      Caso 1 : Para compra long en futures
      '''
      if(df['Close'].iloc[-1] >= df['Supertrend'].iloc[-1] and df['Polaridad'].iloc[-1] == 1):
        if(df['Close'].iloc[-1] >= df['DEMA800'].iloc[-1]):
          #cantidad = float(Get_Balance(client,'USDT'))*0.02
          cantidad = 0.01
          order = Posicion('Buy',symb,cantidad,df['Polaridad'].iloc[-1])
          res = order.make_order(str(int(df['Supertrend'].iloc[-1])), client)
          Cont = EscribirRegistros(Cont, df,'Open',order.side,str(res))
          posicion_list.append(order)
          Polaridad = df['Polaridad'].iloc[-1]
          if(Cont >= 10):
            Cont = 0
          
      '''
      Caso 2 : Para compra shorts en futures
      '''
      if(df['Close'].iloc[-1] <= df['Supertrend'].iloc[-1] and df['Polaridad'].iloc[-1] == -1):
        if(df['Close'].iloc[-1] <= df['DEMA800'].iloc[-1]):
          #cantidad = float(Get_Balance(client,'USDT'))*0.02
          cantidad = 0.01
          order = Posicion('Sell',symb,cantidad,df['Polaridad'].iloc[-1])
          res = order.make_order(str(int(df['Supertrend'].iloc[-1])), client)
          Cont = EscribirRegistros(Cont, df,'Open',order.side,str(res))
          posicion_list.append(order)
          Polaridad = df['Polaridad'].iloc[-1]
          if(Cont >= 10):
            Cont = 0
          
      
    
