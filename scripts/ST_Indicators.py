import pandas as pd
import requests
from datetime import datetime
import time
import pandas_ta as ta 
import math
import pytz
import os
import logging as log
import json
from datetime import datetime
from src.Posicion import Posicion
from requests.exceptions import RequestException
from websocket._exceptions import WebSocketException


'''
###################################################################################
[Proposito]: Función para calcular el tamaño de cada posición para cada uuna de las monedas.
[Parámetros]: cliente (Informacion del cliente de bybit).
[Retorna]: Retorna las cantidades de cada moneda que deben comprarse para seguir con nuestro modelo de 2% de riesgo.
####################################################################################
'''
# Calcula la cantidad de la moneda que se va a comprar o vender cada vez
def calcular_qty_posicion(cliente):
    
    # Llamado a la función para retornar el balance actual
    wallet_balance = float(Get_Balance(cliente,"USDT"))
    
    # Retorna el precio de la moneda requerida
    ticker_xrp = cliente.get_tickers(
        testnet = False,
        category = "linear",
        symbol = "XRPUSDT",
    )
    mark_price_xrp = float(ticker_xrp['result']['list'][0]['markPrice'])   
    ticker_one = cliente.get_tickers(
        testnet = False,
        category = "linear",
        symbol = "ONEUSDT",
    )
    mark_price_one = float(ticker_one['result']['list'][0]['markPrice'])   
    
    # Cantidades de aproximadamente el 2% y 3% de nuestro balance total en 'xrp' y 'one' respectivamente
    qty_xrp = math.ceil(((wallet_balance*0.02)/mark_price_xrp)*69)
    qty_one = math.ceil(((wallet_balance*0.03)/mark_price_one)*25)
    
    if(qty_xrp <= 1):
        qty_xrp = 2*qty_xrp
        
    if(qty_one <= 1):
        qty_one = 2*qty_one

    return (qty_xrp, qty_one)

    
'''
###################################################################################
[Proposito]: Funcion para limpiar la entrada de la informacion del cliente y proveer la informacion de cuenta
[Parametros]: cliente (Informacion del cliente de bybit),
              symbol(Stock por la cual se quiere filtrar, Ejemplo : USDT),
[Retorna]: Retorna valor 'float' del balance de la moneda asignada por parametro en la cuenta
###################################################################################
'''
def Get_Balance(cliente,symbol: str):
    filt_Balance = -1
    while(filt_Balance == -1):
      try:
        balance = cliente.get_coin_balance(accountType="CONTRACT", coin=symbol)
        if balance is not None:
          filt_Balance = balance["result"]["balance"]["walletBalance"]
      except RequestException as e:
        log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
        time.sleep(10)
      except WebSocketException as e:
        log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
        time.sleep(10)
      except Exception as e:
        log.error(f"Ha ocurrido un error inesperado:{e}. Reintentando en 10 segundos...\n")
        time.sleep(10)
            
    return filt_Balance

'''
###################################################################################
[Proposito]: Funcion para obtener todas las ordenes activas en Bybit (Tiempo real)
[Parametros]: client (Objeto HTTP creado por la biblioteca pybit para acceder al API)
[Retorno]: Lista con los objetos Posicion creados
###################################################################################
'''
def get_live_orders(client, qty_xrp, qty_one):
  ret_list = None
  try:
    while(True):
      ret_list = client.get_open_orders(category="linear",settleCoin='USDT',openOnly=0)
      break
  except RequestException as e:
    log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
    time.sleep(10)
  except WebSocketException as e:
    log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
    time.sleep(10)
  except Exception as e:
    log.error(f"Se encontro un error inesperado {e}.\n")
    raise

  if ret_list != None:
    result = []
    iterable = ret_list['result']['list']
    if len(iterable) > 0:
      for order in iterable:
        if order['side'] == 'Sell': #Si es Sell en Bybit implica to be Sell -> Por ende es un Long
          ori_side = 'Buy'
          label = 1
        elif order['side'] == 'Buy': #Si es Buy en Bybit implica to be Buy -> Por ende es un Short
          ori_side = 'Sell'
          label = -1
        else:
          label = 0
        #Modificar el tiempo a formato estandar
        utc_transform = datetime.fromtimestamp(int(order['createdTime']) / 1000, tz=pytz.UTC)
        target_timezone = pytz.timezone('Etc/GMT+5')
        order_time = utc_transform.astimezone(target_timezone)
        #Si la posición es recuperada los datos de apertura no pueden ser recuperados (No son responsabilidad del programa)
        pos = Posicion(ori_side,order['symbol'],float(order['qty']),label,order['triggerPrice'],float(order['lastPriceOnCreated']),order_time,None,None,None,None,None)
        pos.id = order['orderId']
        #Correccion de integridad de los datos para eventos locales (Llegar a halfprice)
        if pos.symbol == 'XRPUSDT':
          if pos.amount <= (int(qty_xrp/2)):
            pos.half_order = True
        elif pos.symbol == 'ONEUSDT':
          if pos.amount < (int(qty_one/2)):
            pos.half_order = True

        result.append(pos)
    return result
  
  else:
    return None


'''
###################################################################################
[Proposito]: Funcion para obtener informacion cada minuto de una moneda en especifico
[Parametros]: symbol (Simbolo de la moneda que se quiere analizar, Ejemplo : BTCUSDT),
              interval (String que representa el intervalo en el que se van a trabajar los datos, Ejemplo: '15' para 15 minutos)
              unixtimeinterval (Tiempo en segundos que se quiere obtener de informacion, Ejemplo: 1800000)
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
    url = 'http://api.bybit.com/v5/market/kline?symbol='+symbol+'&interval='+interval+'&from='+str(start)
    while(True):
      try:
        data = requests.get(url).json()
        if data["retMsg"] == "OK":
          df = pd.DataFrame(data['result']["list"], columns=['Time','Open','High','Low','Close','Volume', 'Turnover'])
          break
        else:
          raise Exception(f"Error general en la solicitud de datos {data}")
      except requests.exceptions.ConnectionError as e:
        log.error(f"Connection error occurred: {e}, Retrying in 10 seconds...\n")
        time.sleep(10)
      except requests.RequestException as e:
        log.error(f"Error occurred: {e}, Retrying in 10 seconds...\n")
        time.sleep(10)
      except Exception as e:
        log.error(f"Error occurred: {e}, Retrying in 10 seconds...\n")
        time.sleep(10)
    df['Time'] = pd.to_numeric(df['Time'])
    df = df.drop_duplicates()
    df['Time'] = df['Time'].apply(lambda x: datetime.fromtimestamp(x / 1000, tz=pytz.UTC))
    target_timezone = pytz.timezone('Etc/GMT+5')
    df['Time'] = df['Time'].apply(lambda x: x.astimezone(target_timezone))
    df = df.drop(columns=['Turnover'])
    list_registers.append(df)
    unixtimeinterval = unixtimeinterval - DATA_200
    
  concatenated_df = pd.concat([list_registers[0], list_registers[1], list_registers[2], list_registers[3], list_registers[4], list_registers[5], list_registers[6], list_registers[7], list_registers[8], list_registers[9]], axis=0)
  concatenated_df = concatenated_df.reset_index(drop=True)
  float_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
  concatenated_df[float_columns] = concatenated_df[float_columns].astype(float)
  return concatenated_df

    
'''
###################################################################################
[Proposito]: Funcion para calcular las lineas que representan el SuperTrend superior e inferior, sus etiquetas e indicadores correspondientes
[Parametros]: df (Dataframe con la informacion del activo)
[Retorno]: Retorna el dataframe modificado, con columnas añadidas 
###################################################################################
'''
def CalculateSupertrend(data: pd.DataFrame):
  reversed_df = data.iloc[::-1]
  Temp_Trend = ta.supertrend(
    high= reversed_df['High'], 
    low = reversed_df['Low'], 
    close = reversed_df['Close'], 
    period=10, 
    multiplier=3)
  # Calcular DEMA800
  ema1 = ema(reversed_df['Close'], length=800)
  ema2 = ema(ema1, length=800)
  Temp_Trend['DEMA800'] = 2 * ema2 - ema1 
  Temp_Trend = Temp_Trend.rename(columns={'SUPERT_7_3.0':'Supertrend','SUPERTd_7_3.0':'Polaridad','SUPERTl_7_3.0':'ST_Inferior','SUPERTs_7_3.0':'ST_Superior'})
  df_merge = pd.merge(data,Temp_Trend,left_index=True, right_index=True)
  return df_merge


'''
###################################################################################
[Proposito]: Funcion auxiliar para calcular el Exponential Moving Average (EMA) de una serie Pandas
[Parametros]: source (pandas.Series que representa el precio de cierre o con lo que se calculara el EMA), 
              length (La ventana de tiempo del EMA a calcular), 
[Retorno]: Retorna serie de pandas con el EMA calculado
###################################################################################
'''
def ema(source, length):     

  #Calcular factor de suavisado (alpha)
  alpha = 2 / (length + 1)
  #Inicializar el EMA con el primer valor de la fuente
  ema = source.iloc[0]      
  #Calcular EMA para cada valor en la fuente
  ema_values = []    
  for value in source:         
    ema = alpha * value + (1 - alpha) * ema         
    ema_values.append(ema)
  ema_values = ema_values
  # Convertir lista a serie de pandas 
  ema_series = pd.Series(ema_values)          
  return ema_series

'''
###################################################################################
[Proposito]: Funcion para revisar las ordenes en cola que aun no se han vendido
[Parametros]: arr (Arreglo con las ordenes que se han hecho), 
              df (Dataframe con la informacion del activo), 
              client (Cliente de Bybit creado en el archivo principal "Bot_SuperTrend.py"),
              symb (Simbolo de la moneda que se quiere analizar, Ejemplo : BTCUSDT)
[Retorno]: Retorna el arreglo con las ordenes que no se ejecutaron y el contador actualizado
###################################################################################
'''
def Revisar_Arreglo(arr: list, df : pd.DataFrame, client, symb: str):
  updated_arr = [] #Nuevo contenedor [Normlamente retorna vacio]
  if(len(arr) != 0): #Si el arreglo contiene alguna orden
    for posicion in arr: #Iterar por cada una de las ordenes 
      if(posicion.symbol == symb): #Si la orden es de la moneda que se esta analizando
        
        #Caso de venta de la orden por stoploss
        if posicion.stop_loss_reached(float(df['High'].iloc[0]), float(df['Low'].iloc[0])):
          log.info(f"Stoploss alcanzado para la orden: {posicion.id}|{posicion.symbol}|{posicion.side}|{posicion.price}")
          posicion.crear_csv_ordenes(False) #Crear fragmento de data con target false -> siendo que se perdio
          
        #Revision normal de las condiciones de venta (Profit, polaridad distinta y tiempo distinto al de la orden)
        elif(posicion.label != df['Polaridad'].iloc[1] and posicion.is_profit(float(df['Close'].iloc[0])) and posicion.time != df['Time'].iloc[0]):
          log.info(f"La posición {posicion.id} con simbolo {posicion.symbol} ha cumplido las condiciones para ser cerrada en profit")
          res = posicion.close_order(client, float(df['Close'].iloc[0]))
          if res['retMsg'] == 'OK':
            log.info(f"La posicion [{str(posicion)}] se ha cerrado exitosamente a un precio de {df['Close'].iloc[0]}")
          else:
            log.error(f"Error al cerrar la orden: {res}")
          
        else:
          #Caso venta mitad de la posicion en profit 
          if(posicion.half_order == False):
            if(posicion.side == 'Buy' and posicion.half_price <= df['High'].iloc[0]):
              #Caso venta mitad de la posicion Long
              posicion.sell_half(client)
              posicion.modificar_stoploss(client, posicion.price)
              updated_arr.append(posicion)
              
            elif(posicion.side == 'Sell' and posicion.half_price >= df['Low'].iloc[0]):
              #Caso venta mitad de la posicion Sell
              posicion.sell_half(client)
              posicion.modificar_stoploss(client, posicion.price)
              updated_arr.append(posicion)
            else:
              updated_arr.append(posicion)
          else:
            #Caso en el que el stoploss de la orden este pendiente a resolución
            if(posicion.stoploss_pending == True):
              res = posicion.modificar_stoploss(client, posicion.price)
              if res != None:
                posicion.stoploss_pending = False #Indicar que el stoploss fue resuelto bajo las reglas de negocio
              updated_arr.append(posicion)
            else:
              updated_arr.append(posicion)
      else:
        updated_arr.append(posicion)
  log.info(f"El arreglo de ordenes activas contiene {len(updated_arr)}")      
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
    return df["Polaridad"].iloc[1]
  elif(Polaridad != 0 and Polaridad != df["Polaridad"].iloc[1]):
    Polaridad = df["Polaridad"].iloc[1]
    return Polaridad
  elif(Polaridad != 0 and Polaridad == df["Polaridad"].iloc[1]):
    return Polaridad
  
'''
###################################################################################
[Proposito]: Funcion para determinar que moneda se va a trabajar con su cantidad correspondiente y actualizar el contador
[Parametros]: cont (Contador de simbolos, indicador de que moneda se esta trabajando),
              symb_list (Lista de simbolos de la moneda con la que se quiere trabajar, Ejemplo : BTCUSDT),
              MAX_CURRENCY (Numero entero que representa el maximo de monedas que se van a trabajar),
              cantidades_simetricas (Lista de cantidades que se van a trabajar por moneda)
[Retorno]: Retorna el simbolo de la moneda, el contador actualizado y la cantidad correspondiente
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
[Parametros]: client (Cliente de Bybit creado en el archivo principal "Bot_SuperTrend.py"),
              symb_list (Lista de simbolos de la moneda con la que se quiere trabajar, Ejemplo : BTCUSDT), 
              interval (String que representa el intervalo en el que se van a trabajar los datos, Ejemplo: '15' para 15 minutos)
              MAX_CURRENCY (Numero entero que representa el maximo de monedas que se van a trabajar),
              cantidades_simetricas (Lista de cantidades que se van a trabajar por moneda),
              Polaridad_l (Lista de polaridades que se van a trabajar por moneda),
              posicion_list (Lista de posiciones que se han hecho),
              symb_cont (Contador de simbolos, indicador de que moneda se esta trabajando)
[Retorno]: Retorna actualizaciones de las listas de posiciones, polaridades y el contador de simbolos
###################################################################################
'''       

def Trading_logic(client, symb_list: list, interval: str, MAX_CURRENCY: int, cantidades_simetricas: list, Polaridad_l: list, posicion_list: list, symb_cont: int):
  symb, symb_cont, cantidad = get_symb(symb_cont, symb_list, MAX_CURRENCY, cantidades_simetricas)
  df = get_data(symb, interval)
  df = CalculateSupertrend(df)
  posicion_list = Revisar_Arreglo(posicion_list, df, client, symb)
  if(Polaridad_l[symb_cont] != df['Polaridad'].iloc[1]):
    log.info(f"La polaridad de {symb} guardada {Polaridad_l[symb_cont]} es diferenre  {df['Polaridad'].iloc[1]} [Primer Tier")
    '''
    Caso 1 : Para compra long en futures
    '''
    if(df['Close'].iloc[1] >= df['Supertrend'].iloc[1] and df['Polaridad'].iloc[1] == 1 and df['Polaridad'].iloc[1] != df['Polaridad'].iloc[2]):
      log.info(f"El close del symbolo {symb} es mayor a la supertrend ({df['Close'].iloc[1]} > {df['Supertrend'].iloc[1]}), la polaridad es {df['Polaridad'].iloc[1]} y diferente a el anterior registro {df['Polaridad'].iloc[2]} [Segundo Tier]")
      if(df['Close'].iloc[1] >= df['DEMA800'].iloc[1]):
        log.info(f"El valor del close del stock {symb} es mayor al DEMA800 ({df['Close'].iloc[1]} > {df['DEMA800'].iloc[1]})[Tercer Tier]")
        order = Posicion('Buy',symb,cantidad,df['Polaridad'].iloc[1],str(round(float(df['Supertrend'].iloc[0]),4)), float(df['Close'].iloc[0]), str(df['Time'].iloc[0]), float(df['Open'].iloc[0]), float(df['High'].iloc[0]), float(df['Low'].iloc[0]), float(df['Volume'].iloc[0]), float(df['DEMA800'].iloc[0]))
        res = order.make_order(client)
        log.info(f"La orden [{str(order)}] se ha abierto exitosamente")
        posicion_list.append(order)
        Polaridad_l[symb_cont] = df['Polaridad'].iloc[1]
        log.info(f"Orden de compra realizada con exito para {symb} [Cuarto Tier]")
        return posicion_list, Polaridad_l, symb_cont
    '''
    Caso 2 : Para compra shorts en futures
    '''
    if(df['Close'].iloc[1] <= df['Supertrend'].iloc[1] and df['Polaridad'].iloc[1] == -1 and df['Polaridad'].iloc[1] != df['Polaridad'].iloc[2]):
      log.info(f"El close del symbolo {symb} es menor a la supertrend ({df['Close'].iloc[1]} < {df['Supertrend'].iloc[1]}), la polaridad es {df['Polaridad'].iloc[1]} y diferente a el anterior registro {df['Polaridad'].iloc[2]} [Segundo Tier]")
      if(df['Close'].iloc[1] <= df['DEMA800'].iloc[1]):
        log.info(f"El valor del close del stock {symb} es menor al DEMA800 ({df['Close'].iloc[1]} < {df['DEMA800'].iloc[1]})[Tercer Tier]")
        order = Posicion('Sell',symb,cantidad,df['Polaridad'].iloc[1],str(round(float(df['Supertrend'].iloc[0]),4)), float(df['Close'].iloc[0]), str(df['Time'].iloc[0]), float(df['Open'].iloc[0]), float(df['High'].iloc[0]), float(df['Low'].iloc[0]), float(df['Volume'].iloc[0]), float(df['DEMA800'].iloc[0]))
        res = order.make_order(client)
        log.info(f"La orden [{str(order)}] se ha abierto exitosamente")
        posicion_list.append(order)
        Polaridad_l[symb_cont] = df['Polaridad'].iloc[1]
        log.info(f"Orden de compra realizada con exito para {symb} [Cuarto Tier]")
        return posicion_list, Polaridad_l, symb_cont
    '''
    Caso 3 : Ninguna compra, actualizar polaridad si es que cambia
    '''
    log.info(f"La polaridad cambia pero no se ejecuta ninguna orden, actualización de variables [Tier 2.1]")
    Polaridad_l[symb_cont] = Polaridad_Manage(Polaridad_l[symb_cont], df)
    return posicion_list, Polaridad_l, symb_cont
  
  else: #Si la polaridad no cambia
    log.info(f"La polaridad no cambia por lo que no se realizan ordenes o ninguna actualización [Tier 1.1]")
    return posicion_list, Polaridad_l, symb_cont
          
      
    
