import pandas as pd
import requests
from datetime import datetime
import time
import pandas_ta as ta 
import numpy as np
import pytz
import os
import json
from datetime import datetime
from src.Posicion import Posicion


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
def EscribirRegistros(order: Posicion, tipo: str, mensaje: str, close_order_price= 0):
  
  #Si la operacion que se hizo fue abrir una posicion
  if(tipo == 'Open'):
    #Path para escribir los registros de apertura
    PATH_OPEN = "./Aperturas"
    # Verificar si el directorio existe
    if not os.path.exists(PATH_OPEN):
        os.makedirs(PATH_OPEN)
    #Escribir registros de un Close
    if(order.side == 'Buy'):
      data = {"status": "Open", "symbol": order.symbol, "side": order.side, "close_price": order.price, "polaridad": order.label, "stoploss": order.stoploss ,"res_msg": mensaje }
      with open(os.path.join(PATH_OPEN, str(datetime.now()) + "_LONG.json"), 'w') as file:
        json.dump(data, file)
      
    #Escribir registros de un Short  
    if(order.side == 'Sell'):
      data = {"status": "Open", "symbol": order.symbol, "side": order.side, "close_price": order.price, "polaridad": order.label, "stoploss": order.stoploss ,"res_msg": mensaje }
      with open(os.path.join(PATH_OPEN, str(datetime.now()) + "_SHORT.json"), 'w') as file:
        json.dump(data, file)
    
  #Si la operacion que se hizo fue cerrar una posicion    
  elif(tipo == 'Close' and close_order_price != 0):
    #Path para escribir los registros de apertura
    PATH_CLOSE = "./Cerradas"
    # Verificar si el directorio existe
    if not os.path.exists(PATH_CLOSE):
        os.makedirs(PATH_CLOSE)
    if(order.side == 'Buy'):
      data = {"status": "Close", "symbol": order.symbol, "side": order.side, "close_price": close_order_price, "polaridad": order.label, "P&L": (((close_order_price - order.price)/order.price)*100)*100 ,"res_msg": mensaje}
      with open(os.path.join(PATH_CLOSE, str(datetime.now()) + "_LONG.json"), 'w') as file:
        json.dump(data, file)
      
    if(order.side == 'Sell'):
      data = {"status": "Close", "symbol": order.symbol, "side": order.side, "close_price": close_order_price, "polaridad": order.label, "P&L": (((close_order_price - order.price)/order.price)*100)*-100 ,"res_msg": mensaje}
      with open(os.path.join(PATH_CLOSE, str(datetime.now()) + "_LONG.json"), 'w') as file:
        json.dump(data, file)
    
  else:
    print("La solicitud es incorrecta")
  
'''
###################################################################################
[Proposito]: Funcion para revisar las ordenes en cola que aun no se han vendido
[Parametros]: arr (Arreglo con las ordenes que se han hecho), df (Dataframe con la informacion del activo), 
              client (Cliente de Bybit creado en el archivo principal "Bot_SuperTrend.py"), 
              contador (Variable numerica que determina el registro en el que se esta)
[Retorno]: Retorna el arreglo con las ordenes que no se ejecutaron y el contador actualizado
###################################################################################
'''
def Revisar_Arreglo(arr, df : pd.DataFrame, client, symb: str):
  updated_arr = [] #Nuevo contenedor [Normlamente retorna vacio]
  if(len(arr) != 0):
    print("______________________________________________________________________________")
    print(f"INICIO INFORME POR CUADRO TEMPORAL DE {symb} a las {df['Time'].iloc[-1]}")
    print(f"Cantidad de ordenes en el arreglo: {len(arr)}")
    for posicion in arr:
      if(posicion.symbol == symb):
        print(f"Orden: {posicion} | Esta en profit: {posicion.is_profit(float(df['Close'].iloc[-1]))} | Polaridad actual {df['Polaridad'].iloc[-2]}")
        #Caso donde ya la mitad se ha vendido y ya se ha subido el stoploss
        if(posicion.label != df['Polaridad'].iloc[-2] and posicion.is_profit(float(df['Close'].iloc[-1])) and posicion.time != df['Time'].iloc[-1]):
          res = posicion.close_order(client)
          EscribirRegistros(posicion,'Close', str(res), close_order_price= float(df['Close'].iloc[-1]))
          
        elif(posicion.side == 'Buy' and float(posicion.stoploss) >= df['Close'].iloc[-2]):
          #Caso Stoploss para ordenes Long
          EscribirRegistros(posicion,'Close', "Cerrada por Stoploss", close_order_price= float(df['Close'].iloc[-1]))
          
        elif(posicion.side == 'Sell' and float(posicion.stoploss) <= df['Close'].iloc[-2]):
          #Caso Stoploss para ordenes Short
          EscribirRegistros(posicion,'Close', "Cerrada por Stoploss", close_order_price= float(df['Close'].iloc[-1]))
        else:
          #Caso venta mitad de la posicion en profit 
          if(posicion.half_order == False):
            if(posicion.side == 'Buy' and posicion.half_price <= df['Close'].iloc[-1]):
              #Caso venta mitad de la posicion Long
              posicion.sell_half(client)
              posicion.modificar_stoploss(client, posicion.id, str(df['Close'].iloc[-1]))
              print("Se ha vendido la mitad de la posicion Long")
              updated_arr.append(posicion)
            elif(posicion.side == 'Sell' and posicion.half_price >= df['Close'].iloc[-1]):
              #Caso venta mitad de la posicion Long
              posicion.sell_half(client)
              posicion.modificar_stoploss(client, posicion.id, str(df['Close'].iloc[-1]))
              print("Se ha vendido la mitad de la posicion Long")
              updated_arr.append(posicion)
          else:
            updated_arr.append(posicion)
      else:
        print("El simbolo que se esta analizando no coincide con la posicion")
    print("##FIN REPORTE##")
    print("______________________________________________________________________________")
  else:
    print("NO HAY ORDENES")
  return updated_arr
'''
###################################################################################
[Proposito]: Actualizar la polaridad que regula el sistema aunque no exista una compra
[Parametros]: Polaridad (Valor de la polaridad del Dataframe de la moneda, Ejemplo: 1,-1 o 0)
              df(Pandas Dataframe que contiene la información de la moneda)
[Retorno]: Retorna la modificación o version actualizada del valor de la Polaridad
###################################################################################
'''
def Polaridad_Manage(Polaridad: int, df: pd.DataFrame):
  if(Polaridad == 0):
    #return Polaridad
    return df["Polaridad"].iloc[-2]
  elif(Polaridad != 0 and Polaridad != df["Polaridad"].iloc[-2]):
    Polaridad = df["Polaridad"].iloc[-2]
    return Polaridad
  elif(Polaridad != 0 and Polaridad == df["Polaridad"].iloc[-2]):
    return Polaridad
  
'''
###################################################################################
[Proposito]: 
[Parametros]:
[Retorno]:
###################################################################################
'''
def get_symb(cont: int, symb_list: list, MAX_CURRENCY: int, cantidades_simetricas: list):
  symb = symb_list[cont]
  cantidades = cantidades_simetricas[cont]
  if(cont == MAX_CURRENCY):
    return symb, 0, cantidades
  else:
    cont += 1
    return symb, cont, cantidades
        
'''
###################################################################################
[Proposito]: Funcion para poner en funcionamiento el bot
[Parametros]: symb (Simbolo de la moneda con la que se quiere trabajar, Ejemplo : BTCUSDT), 
              client (Cliente de Bybit creado en el archivo principal "Bot_SuperTrend.py"), 
              interval (String que representa el intervalo en el que se van a trabajar los datos, Ejemplo: '15' para 15 minutos)
[Retorno]: No tiene retorno, es un bucle infinito
###################################################################################
'''       

def Trading(symb_list: list, interval: str,client, MAX_CURRENCY: int, cantidades_simetricas: list):
  posicion_list = [] #Lista que contendra las ordenes
  Polaridad_l = [0] * (MAX_CURRENCY + 1) #Lista donde se van a guardar las polaridades respectivas de cada moneda
  symb_cont = 0 #Contador de symbolos (Determina cual stock observar)
  while(True):
    symb, symb_cont, cantidad = get_symb(symb_cont, symb_list, MAX_CURRENCY, cantidades_simetricas)
    time.sleep(60)
    df = get_data(symb, interval)
    df = CalculateSupertrend(df)
    posicion_list = Revisar_Arreglo(posicion_list, df, client, symb)
    if(Polaridad_l[symb_cont] != df['Polaridad'].iloc[-2]):
      '''
      Caso 1 : Para compra long en futures
      '''
      if(df['Close'].iloc[-2] >= df['Supertrend'].iloc[-2] and df['Polaridad'].iloc[-2] == 1 and df['Polaridad'].iloc[-2] != df['Polaridad'].iloc[-3]):
        if(df['Close'].iloc[-2] >= df['DEMA800'].iloc[-2]):
          #cantidad = float(Get_Balance(client,'USDT'))*0.02
          order = Posicion('Buy',symb,cantidad,df['Polaridad'].iloc[-2],str(round(float(df['Supertrend'].iloc[-2]),4)), float(df['Close'].iloc[-1]), str(df['Time'].iloc[-1]))
          res = order.make_order(client)
          EscribirRegistros(order,'Open', str(res))
          posicion_list.append(order)
          Polaridad_l[symb_cont] = df['Polaridad'].iloc[-2]
          
      '''
      Caso 2 : Para compra shorts en futures
      '''
      if(df['Close'].iloc[-2] <= df['Supertrend'].iloc[-2] and df['Polaridad'].iloc[-2] == -1 and df['Polaridad'].iloc[-2] != df['Polaridad'].iloc[-3]):
        if(df['Close'].iloc[-2] <= df['DEMA800'].iloc[-2]):
          #cantidad = float(Get_Balance(client,'USDT'))*0.02
          order = Posicion('Sell',symb,cantidad,df['Polaridad'].iloc[-2],str(round(float(df['Supertrend'].iloc[-1]),4)), float(df['Close'].iloc[-1]), str(df['Time'].iloc[-1]))
          res = order.make_order(client)
          EscribirRegistros(order,'Open',str(res))
          posicion_list.append(order)
          Polaridad_l[symb_cont] = df['Polaridad'].iloc[-2]
      '''
      Caso 3 : Ninguna compra, actualizar polaridad si es que cambia
      '''
      Polaridad_l[symb_cont] = Polaridad_Manage(Polaridad_l[symb_cont], df)
      
          
      
    
