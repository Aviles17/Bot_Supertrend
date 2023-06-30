import pandas as pd
import requests
from datetime import datetime
import time
import pandas_ta as ta 
import numpy as np
import pytz
from Posicion import Posicion

#Direccion donde se quieren almacenar los archivos de Log en formato txt (Llenar dependiendo de su dispositivo local)
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
[Parametros]: symbol (Simbolo de la moneda que se quiere analizar, Ejemplo : BTCUSDT),
              interval (String que representa el intervalo en el que se van a trabajar los datos, Ejemplo: '15' para 15 minutos)
[Retorno]: Dataframe de pandas con la informacion solicitada
###################################################################################
'''
def get_data(symbol: str,interval: str,unixtimeinterval: int = 1800000):

  list_registers = []
  DATA_200 = 180000
  now = datetime.now()
  unixtime = int(time.mktime(now.timetuple()))
  since = unixtime
  while(unixtimeinterval != 0):
    start= str(since - unixtimeinterval)
    url = 'http://api.bybit.com/public/linear/kline?symbol='+symbol+'&interval='+interval+'&from='+str(start)
    while(True):
      try:
        data = requests.get(url).json()
        break
      except requests.exceptions.ConnectionError as e:
        print(f"Connection error occurred: {e}, Retrying in 10 seconds...\n")
        time.sleep(10)
      except requests.RequestException as e:
        print(f"Error occurred: {e}, Retrying in 10 seconds...\n")
        time.sleep(10)
    df = pd.DataFrame(data['result'])
    df = df.drop_duplicates()
    df['open_time'] = df['open_time'].apply(lambda x: datetime.fromtimestamp(x, tz=pytz.UTC))
    target_timezone = pytz.timezone('Etc/GMT+5')
    df['open_time'] = df['open_time'].apply(lambda x: x.astimezone(target_timezone))
    df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume','open_time':'Time'}, inplace=True)
    df = df.drop(columns=['symbol','interval','period','turnover','start_at','id'])
    list_registers.append(df)
    unixtimeinterval = unixtimeinterval - DATA_200
    
  concatenated_df = pd.concat([list_registers[0], list_registers[1], list_registers[2], list_registers[3], list_registers[4], list_registers[5], list_registers[6], list_registers[7], list_registers[8], list_registers[9]], axis=0)
  concatenated_df = concatenated_df.reset_index(drop=True)

  return concatenated_df

'''
###################################################################################
[Proposito]: Funcion para calcular las lineas que representan el SuperTrend superior e inferior, sus etiquetas e indicadores correspondientes
[Parametros]: symbol (String que representa la moneda a la que se va a suscribir), 
              df (Dataframe con la informacion del activo), 
              mult (Multiplicador para calcular SuperTrend)
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

'''
###################################################################################
[Proposito]: Funcion para escribir los registros de las ordenes que se han hecho en formato txt segun el PATH seleccionado
[Parametros]: Contador (Numero entero que determina en que registro se esta), 
              df (Dataframe con la informacion del activo), 
              tipo (El tipo de transaccion que se hizo, apertura o cerrar), 
              side (Lado o tipo de orden que se ejecuto, Buy or Sell), 
              mensaje (El mensaje de retorno de la peticion HTTP de bybit)
[Retorno]: Retorna la variable Contador con la informacion actualizada de que se añadio
###################################################################################
'''
def EscribirRegistros(Contador : int, df : pd.DataFrame, tipo: str, side: str, mensaje: str):
  edit = open(PATH + str(Contador) + ".txt",'w')
  #Si la operacion que se hizo fue abrir una posicion
  if(tipo == 'Open'):
    #Escribir registros de un Close
    if(side == 'Buy'):
      edit.write("Open | " + str(df['Time'].iloc[-2]) + " | LONG \n")
      edit.write(mensaje + "\n")
      edit.write("Close_Price: {Price}, Supertrend: {Supertrend}, Polaridad: {Polaridad}\n".format(Price = str(df['Close'].iloc[-2]),
                                                                                                 Supertrend = str(df['Supertrend'].iloc[-2]),
                                                                                                 Polaridad = str(df['Polaridad'].iloc[-2])))
      edit.write("#FIN#\n")
      
      Contador += 1
      edit.close()
      return Contador
      
    #Escribir registros de un Short  
    if(side == 'Sell'):
      edit.write("Open | " + str(df['Time'].iloc[-2]) + " | SHORT \n")
      edit.write(mensaje + "\n")
      edit.write("Close_Price: {Price}, Supertrend: {Supertrend}, Polaridad: {Polaridad}\n".format(Price = str(df['Close'].iloc[-2]),
                                                                                                 Supertrend = str(df['Supertrend'].iloc[-2]),
                                                                                                 Polaridad = str(df['Polaridad'].iloc[-2])))
      edit.write("#FIN#\n")
      
      Contador += 1
      edit.close()
      return Contador  
    
  #Si la operacion que se hizo fue cerrar una posicion    
  elif(tipo == 'Close'):
    if(side == 'Buy'):
      edit.write("Close | " + str(df['Time'].iloc[-2]) + " | LONG \n")
      edit.write(mensaje + "\n")
      edit.write("Close_Price: {Price}, Supertrend: {Supertrend}, Polaridad: {Polaridad}\n".format(Price = str(df['Close'].iloc[-2]),
                                                                                                 Supertrend = str(df['Supertrend'].iloc[-2]),
                                                                                                 Polaridad = str(df['Polaridad'].iloc[-2])))
      edit.write("#FIN#\n")
      
      Contador += 1
      edit.close()
      return Contador 
      
    if(side == 'Sell'):
      
      edit.write("Close | " + str(df['Time'].iloc[-2]) + " | SHORT \n")
      edit.write(mensaje)
      edit.write("Close_Price: {Price}, Supertrend: {Supertrend}, Polaridad: {Polaridad}\n".format(Price = str(df['Close'].iloc[-2]),
                                                                                                 Supertrend = str(df['Supertrend'].iloc[-2]),
                                                                                                 Polaridad = str(df['Polaridad'].iloc[-2])))
      edit.write("#FIN#\n")
      
      Contador += 1
      edit.close()
      return Contador 
    
  
  else:
    print("La solicitud es incorrecta")
    edit.close()  
    return Contador
  
'''
###################################################################################
[Proposito]: Funcion para revisar las ordenes en cola que aun no se han vendido
[Parametros]: arr (Arreglo con las ordenes que se han hecho), df (Dataframe con la informacion del activo), 
              client (Cliente de Bybit creado en el archivo principal "Bot_SuperTrend.py"), 
              contador (Variable numerica que determina el registro en el que se esta)
[Retorno]: Retorna el arreglo con las ordenes que no se ejecutaron y el contador actualizado
###################################################################################
'''
def Revisar_Arreglo(arr, df : pd.DataFrame, client, contador : int):
  Cont = contador
  updated_arr = [] #Nuevo contenedor [Normlamente retorna vacio]
  if(len(arr) != 0):
    for posicion in arr:
      if(posicion.label != df['Polaridad'].iloc[-2]):
        res = posicion.close_order(client)
        Cont = EscribirRegistros(Cont,df,'Close', posicion.side, str(res))
      elif(posicion.side == 'Buy' and float(posicion.stoploss) >= df['Close'].iloc[-2]):
        #Orden cierra auto
        Cont = EscribirRegistros(Cont,df,'Close', posicion.side, "Cerrada por Stoploss")
      elif(posicion.side == 'Sell' and float(posicion.stoploss) <= df['Close'].iloc[-2]):
        #Orden cierra auto
        Cont = EscribirRegistros(Cont,df,'Close', posicion.side, "Cerrada por Stoploss")
      else:
        updated_arr.append(posicion)
        
  return updated_arr, Cont 
'''
[Proposito]:
[Parametros]:
[Retorno]: 
'''
def Polaridad_Manage(Polaridad: int, df: pd.DataFrame):
  if(Polaridad == 0):
    return Polaridad
  elif(Polaridad != 0 and Polaridad != df["Polaridad"].iloc[-2]):
    Polaridad = df["Polaridad"].iloc[-2]
    return Polaridad
  elif(Polaridad != 0 and Polaridad == df["Polaridad"].iloc[-2]):
    return Polaridad
        
'''
###################################################################################
[Proposito]: Funcion para poner en funcionamiento el bot
[Parametros]: symb (Simbolo de la moneda con la que se quiere trabajar, Ejemplo : BTCUSDT), 
              client (Cliente de Bybit creado en el archivo principal "Bot_SuperTrend.py"), 
              interval (String que representa el intervalo en el que se van a trabajar los datos, Ejemplo: '15' para 15 minutos)
[Retorno]: No tiene retorno, es un bucle infinito
###################################################################################
'''       

def Trading(symb: str, interval: str,client):
  Polaridad = 0 #Valor del close para comparar registros y evitar repeticiones
  Cont = 0 #Contador para poder generar registros consecutivos en archivos externos
  posicion_list = [] #Lista que contendra las ordenes 
  while(True):
    time.sleep(60)
    df = get_data(symb, interval)
    df = CalculateSupertrend(df)
    posicion_list, Cont = Revisar_Arreglo(posicion_list,df,client,Cont)
    if(Polaridad != df['Polaridad'].iloc[-2]):
      '''
      Caso 1 : Para compra long en futures
      '''
      if(df['Close'].iloc[-2] >= df['Supertrend'].iloc[-2] and df['Polaridad'].iloc[-2] == 1 and df['Polaridad'].iloc[-2] != df['Polaridad'].iloc[-3]):
        if(df['Close'].iloc[-2] >= df['DEMA800'].iloc[-2]):
          #cantidad = float(Get_Balance(client,'USDT'))*0.02
          cantidad = 0.01
          order = Posicion('Buy',symb,cantidad,df['Polaridad'].iloc[-2],str(int(df['Supertrend'].iloc[-2])))
          res = order.make_order(client)
          Cont = EscribirRegistros(Cont, df,'Open',order.side,str(res))
          posicion_list.append(order)
          Polaridad = df['Polaridad'].iloc[-2]
          if(Cont >= 10):
            Cont = 0
          
      '''
      Caso 2 : Para compra shorts en futures
      '''
      if(df['Close'].iloc[-2] <= df['Supertrend'].iloc[-2] and df['Polaridad'].iloc[-2] == -1 and df['Polaridad'].iloc[-2] != df['Polaridad'].iloc[-3]):
        if(df['Close'].iloc[-2] <= df['DEMA800'].iloc[-2]):
          #cantidad = float(Get_Balance(client,'USDT'))*0.02
          cantidad = 0.01
          order = Posicion('Sell',symb,cantidad,df['Polaridad'].iloc[-2],str(int(df['Supertrend'].iloc[-2])))
          res = order.make_order(client)
          Cont = EscribirRegistros(Cont, df,'Open',order.side,str(res))
          posicion_list.append(order)
          Polaridad = df['Polaridad'].iloc[-2]
          if(Cont >= 10):
            Cont = 0
      '''
      Caso 3 : Ninguna compra, actualizar polaridad si es que cambia
      '''
      Polaridad = Polaridad_Manage(Polaridad, df)
      
          
      
    
