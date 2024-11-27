import pandas as pd
import requests
from datetime import datetime
import time
import pandas_ta as ta
import math
import pytz
import logging as log
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


def calcular_qty_posicion(cliente, COIN_SYMBOL: str, entry: float, stoploss:float, risk:float = 0.02) -> list:

    # Llamado a la función para retornar el balance actual
    wallet_balance = float(Get_Balance(cliente, "USDT"))

    ticker_info = cliente.get_tickers(
        testnet=False,
        category="linear",
        symbol=COIN_SYMBOL,
    )
    mark_price = float(ticker_info['result']['list'][0]['markPrice'])

    stop_loss_proportion = abs((entry - stoploss) / entry)
    order_size = (wallet_balance * risk) / stop_loss_proportion
    if (order_size / mark_price) < 1:
        factor = 10 ** 2
        qty = math.floor(order_size * factor) / factor
    else:
        qty = math.floor(order_size / mark_price)

    # Aplicar Null safty para evitar errores en la ejecución de ordenes (Condición > 5 USDT)
    if order_size <= 5:
        qty = int(round((6/mark_price), 0))
    if (wallet_balance - order_size) <= 0:
        qty = None

    return qty


'''
###################################################################################
[Proposito]: Funcion para limpiar la entrada de la informacion del cliente y proveer la informacion de cuenta
[Parametros]: cliente (Informacion del cliente de bybit),
              symbol(Stock por la cual se quiere filtrar, Ejemplo : USDT),
[Retorna]: Retorna valor 'float' del balance de la moneda asignada por parametro en la cuenta
###################################################################################
'''


def Get_Balance(cliente, symbol: str):
    filt_Balance = -1
    while (filt_Balance == -1):
        try:
            balance = cliente.get_coin_balance(
                accountType="CONTRACT", coin=symbol)
            if balance is not None:
                filt_Balance = balance["result"]["balance"]["walletBalance"]
        except RequestException as e:
            log.error(
                f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
            time.sleep(10)
        except WebSocketException as e:
            log.error(
                f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
            time.sleep(10)
        except Exception as e:
            log.error(
                f"Ha ocurrido un error inesperado:{e}. Reintentando en 10 segundos...\n")
            time.sleep(10)

    return filt_Balance


'''
###################################################################################
[Proposito]: Funcion para obtener todas las ordenes activas en Bybit (Tiempo real)
[Parametros]: client (Objeto HTTP creado por la biblioteca pybit para acceder al API)
[Retorno]: Lista con los objetos Posicion creados
###################################################################################
'''


def get_live_orders(client, COIN_SUPPORT: list, Polaridad_l: list):
    ret_list = None
    try:
        while (True):
            ret_list = client.get_open_orders(
                category="linear", settleCoin='USDT', openOnly=0)
            break
    except RequestException as e:
        log.error(
            f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
        time.sleep(10)
    except WebSocketException as e:
        log.error(
            f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
        time.sleep(10)
    except Exception as e:
        log.error(f"Se encontro un error inesperado {e}.\n")
        raise

    if ret_list != None:
        result = []
        iterable = ret_list['result']['list']
        if len(iterable) > 0:
            for order in iterable:
                # Si es Sell en Bybit implica to be Sell -> Por ende es un Long
                if order['side'] == 'Sell':
                    ori_side = 'Buy'
                    label = 1
                    Polaridad_l[COIN_SUPPORT.index(order['symbol'])] = label
                # Si es Buy en Bybit implica to be Buy -> Por ende es un Short
                elif order['side'] == 'Buy':
                    ori_side = 'Sell'
                    label = -1
                    Polaridad_l[COIN_SUPPORT.index(order['symbol'])] = label
                else:
                    label = 0
                # Modificar el tiempo a formato estandar
                utc_transform = datetime.fromtimestamp(
                    int(order['createdTime']) / 1000, tz=pytz.UTC)
                target_timezone = pytz.timezone('Etc/GMT+5')
                order_time = utc_transform.astimezone(target_timezone)
                # Si la posición es recuperada los datos de apertura no pueden ser recuperados (No son responsabilidad del programa)
                pos = Posicion(ori_side, order['symbol'], float(order['qty']), label, order['triggerPrice'], float(
                    order['lastPriceOnCreated']), order_time, None, None, None, None, None)
                pos.id = order['orderId']

                # Correccion de integridad de los datos para eventos locales (Llegar a halfprice)
                if float(pos.price) <= float(pos.stoploss) or int(order['createdTime']) < int(order['updatedTime']):
                    pos.half_order = True

                result.append(pos)
        return result, Polaridad_l

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


def get_data(symbol: str, interval: str):
    list_registers = []
    unix_endtime = None
    for i in range(0, 3):
        if i == 0:  # Primer llamado: Historial de mercado con tiempo actual
            url = 'http://api.bybit.com/v5/market/kline?symbol=' + \
                symbol+'&interval='+interval+'&limit='+str(1000)
            while (True):
                try:
                    data = requests.get(url).json()
                    unix_endtime = data['result']["list"][-1][0]
                    break
                except requests.exceptions.ConnectionError as e:
                    print(
                        f"Connection error occurred: {e}, Retrying in 10 seconds...\n")
                    time.sleep(10)
                except requests.RequestException as e:
                    print(
                        f"Connection error occurred: {e}, Retrying in 10 seconds...\n")
                    time.sleep(10)
                except Exception as e:
                    print(
                        f"An error occurred: {e}, Retrying in 10 seconds...\n")
                    time.sleep(10)
        if i == 1 and unix_endtime != None:
            url = 'http://api.bybit.com/v5/market/kline?symbol='+symbol + \
                '&interval='+interval+'&limit=' + \
                str(1000)+'&end='+str(unix_endtime)
            while (True):
                try:
                    data = requests.get(url).json()
                    unix_endtime = data['result']["list"][-1][0]
                    break
                except requests.exceptions.ConnectionError as e:
                    print(
                        f"Connection error occurred: {e}, Retrying in 10 seconds...\n")
                    time.sleep(10)
                except requests.RequestException as e:
                    print(
                        f"Connection error occurred: {e}, Retrying in 10 seconds...\n")
                    time.sleep(10)
        if i == 2 and unix_endtime != None:
            url = 'http://api.bybit.com/v5/market/kline?symbol='+symbol + \
                '&interval='+interval+'&limit=' + \
                str(200)+'&end='+str(unix_endtime)
            while (True):
                try:
                    data = requests.get(url).json()
                    break
                except requests.exceptions.ConnectionError as e:
                    print(
                        f"Connection error occurred: {e}, Retrying in 10 seconds...\n")
                    time.sleep(10)
                except requests.RequestException as e:
                    print(
                        f"Connection error occurred: {e}, Retrying in 10 seconds...\n")
                    time.sleep(10)
        # Crear proto dataframe y añadir a lista
        df = pd.DataFrame(data['result']["list"], columns=[
                          'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover'])
        df['Time'] = pd.to_numeric(df['Time'])
        df = df.drop_duplicates()
        df['Time'] = df['Time'].apply(
            lambda x: datetime.fromtimestamp(x / 1000, tz=pytz.UTC))
        target_timezone = pytz.timezone('Etc/GMT+5')
        df['Time'] = df['Time'].apply(lambda x: x.astimezone(target_timezone))
        df = df.drop(columns=['Turnover'])
        list_registers.append(df)

    concatenated_df = pd.concat(
        [list_registers[0], list_registers[1], list_registers[2]], axis=0)
    concatenated_df = concatenated_df.reset_index(drop=True)
    float_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    concatenated_df[float_columns] = concatenated_df[float_columns].astype(
        float)
    concatenated_df = concatenated_df.drop_duplicates()
    return concatenated_df


'''
###################################################################################
[Propósito]: Función auxiliar para calcular la Media Móvil Simple (SMA) de una serie de Pandas
[Parámetros]: 
    source (pandas.Series): Representa el precio de cierre o los datos para calcular la SMA
    length (int): La ventana de tiempo para el cálculo de la SMA
    rounded (int, opcional): Número de decimales para redondear el resultado. Por defecto es 7.
[Retorna]: Valor flotante que representa la SMA calculada
###################################################################################
'''


def ta_sma(source, length, rounded=7) -> float:

    sum_length = sum(source)
    SMA = round(sum_length/length, rounded)

    return SMA


"""
###################################################################################
[Propósito]: Calcular la Media Móvil Exponencial (EMA) para una serie de Pandas dada
[Parámetros]:
    source (pd.Series): La serie de datos de entrada, típicamente precios de cierre
    length (int): El periodo sobre el cual calcular la EMA
    rounded (int, opcional): Número de decimales para redondear. Por defecto es 7.
[Retorna]: Lista que contiene los valores de EMA calculados
###################################################################################
"""


def ta_ema(source: pd.Series, length: int, rounded=7, ):

    alpha = 2 / (length + 1)

    SMA = []
    EMA = []

    aux = 0
    prev_ema = 0

    for close_price in source:

        aux = aux + 1

        if (aux < length):
            SMA.append(close_price)
            EMA.append(None)
            continue

        elif (aux == length):
            prev_ema = ta_sma(SMA, length)
            EMA.append(prev_ema)
            continue

        elif (aux > length):
            close_price = round(close_price, rounded)
            prev_ema = round(
                (alpha * close_price + (1 - alpha) * prev_ema), rounded)
            EMA.append(prev_ema)

    return EMA


"""
###################################################################################
[Propósito]: Calcular una Media Móvil Exponencial (EMA) de segundo nivel basada en una EMA previamente calculada
[Parámetros]:
    source: Los datos de entrada, típicamente una EMA previamente calculada
    length (int): El periodo sobre el cual calcular esta segunda EMA
    rounded (int, opcional): Número de decimales para redondear. Por defecto es 7.
[Retorna]: Lista que contiene los valores de la EMA de segundo nivel calculados
###################################################################################
"""


def ta_second_ema(source, length, rounded=7):

    alpha = 2 / (length + 1)

    SMA = []
    EMA2 = []

    aux = 0
    prev_ema2 = 0

    for ema_value in source:

        if (ema_value == None):
            EMA2.append(None)
            continue

        elif (ema_value != None):

            aux = aux + 1

            if (aux < length):
                SMA.append(ema_value)
                EMA2.append(None)
                continue

            elif (aux == length):
                prev_ema2 = ta_sma(SMA, length)
                EMA2.append(prev_ema2)
                continue

            elif (aux > length):
                prev_ema2 = round(
                    (alpha * ema_value + (1 - alpha) * prev_ema2), rounded)
                EMA2.append(prev_ema2)

    return EMA2


"""
###################################################################################
[Propósito]: Calcular la Media Móvil Exponencial Doble (DEMA) para un DataFrame dado
[Parámetros]:
    df (pd.DataFrame): DataFrame de entrada que contiene datos de precios
    length (int, opcional): El periodo sobre el cual calcular la DEMA. Por defecto es 800.
    rounded (int, opcional): Número de decimales para redondear. Por defecto es 7.
[Retorna]: Lista que contiene los valores de DEMA calculados
###################################################################################
"""


def dema(df: pd.DataFrame, length: int = 800, rounded=7):

    src = df['Close']

    e1 = ta_ema(src, length)
    e2 = ta_second_ema(e1, length)

    dema = []

    for a, b in zip(e1, e2):

        if a is None or b is None:
            dema.append(None)

        else:
            result = round(2 * a - b, rounded)
            dema.append(result)

    return dema


"""
###################################################################################
[Propósito]: Actualizar un DataFrame existente con valores recalculados de EMA y DEMA
[Parámetros]:
    data (pd.DataFrame): DataFrame de entrada que contiene datos de precios OHLC
    test_length (int, opcional): Longitud para los cálculos de EMA y DEMA. Por defecto es 800.
[Retorna]: DataFrame actualizado con columnas de EMA y DEMA recalculadas
###################################################################################
"""


def update_df(data: pd.DataFrame, test_length: int = 800):

    kline = data.iloc[::-1].reset_index(drop=True)

    _ema = ta_ema(kline['Close'], test_length)
    _dema = dema(kline, test_length)

    kline["EMA"] = _ema
    kline["DEMA800"] = _dema

    FULL_original_order_kline = kline.iloc[::-1].reset_index(drop=True)

    return FULL_original_order_kline


"""
###################################################################################
[Propósito]: Calcular el indicador SuperTrend y medias móviles adicionales para un DataFrame dado
[Parámetros]:
    data (pd.DataFrame): DataFrame de entrada que contiene datos de precios OHLC
    test_length (int, opcional): Longitud para los cálculos de EMA y DEMA. Por defecto es 800.
[Retorna]: DataFrame con columnas añadidas para el indicador SuperTrend, EMA y DEMA
###################################################################################
"""


def CalculateSupertrend(data: pd.DataFrame, mult: float, periodo: int):

    reversed_df = data.iloc[::-1]
    Temp_Trend = ta.supertrend(
        high=reversed_df['High'],
        low=reversed_df['Low'],
        close=reversed_df['Close'],
        period=periodo,
        multiplier=mult)

    Temp_Trend = Temp_Trend.rename(columns={f'SUPERT_7_{mult}': 'Supertrend', f'SUPERTd_7_{mult}': 'Polaridad',
                                   f'SUPERTl_7_{mult}': 'ST_Inferior', f'SUPERTs_7_{mult}': 'ST_Superior'})

    df_merge = pd.merge(data, Temp_Trend, left_index=True, right_index=True)

    df_merge_ma_final = update_df(df_merge) # Actualizar el dataframe con las medias moviles (EMA , DEMA)
    return df_merge_ma_final


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


def Revisar_Arreglo(arr: list, df: pd.DataFrame, client, symb: str):
    updated_arr = []  # Nuevo contenedor [Normlamente retorna vacio]
    if (len(arr) != 0):  # Si el arreglo contiene alguna orden
        for posicion in arr:  # Iterar por cada una de las ordenes
            if (posicion.symbol == symb):  # Si la orden es de la moneda que se esta analizando

                # Caso de venta de la orden por stoploss
                if posicion.stop_loss_reached(float(df['High'].iloc[0]), float(df['Low'].iloc[0])):
                    log.info(
                        f"Stoploss alcanzado para la orden: {posicion.id}|{posicion.symbol}|{posicion.side}|{posicion.price}")
                    # Crear fragmento de data con target false -> siendo que se perdio
                    posicion.crear_csv_ordenes(False)

                # Revision normal de las condiciones de venta (Profit, polaridad distinta y tiempo distinto al de la orden)
                elif (posicion.label != df['Polaridad'].iloc[1] and posicion.is_profit(float(df['Close'].iloc[0])) and posicion.time != df['Time'].iloc[0]):
                    log.info(
                        f"La posición {posicion.id} con simbolo {posicion.symbol} ha cumplido las condiciones para ser cerrada en profit")
                    res = posicion.close_order(
                        client, float(df['Close'].iloc[0]))
                    if res['retMsg'] == 'OK':
                        log.info(
                            f"La posicion [{str(posicion)}] se ha cerrado exitosamente a un precio de {df['Close'].iloc[0]}")
                    else:
                        log.error(f"Error al cerrar la orden: {res}")

                else:
                    # Caso venta mitad de la posicion en profit
                    if (posicion.half_order == False):
                        if (posicion.side == 'Buy' and posicion.half_price <= df['High'].iloc[0]):
                            # Caso venta mitad de la posicion Long
                            posicion.sell_half(client)
                            posicion.modificar_stoploss(client, posicion.price)
                            updated_arr.append(posicion)

                        elif (posicion.side == 'Sell' and posicion.half_price >= df['Low'].iloc[0]):
                            # Caso venta mitad de la posicion Sell
                            posicion.sell_half(client)
                            posicion.modificar_stoploss(client, posicion.price)
                            updated_arr.append(posicion)
                        else:
                            updated_arr.append(posicion)
                    else:
                        # Caso en el que el stoploss de la orden este pendiente a resolución
                        if (posicion.stoploss_pending == True):
                            res = posicion.modificar_stoploss(
                                client, posicion.price)
                            if res != None:
                                # Indicar que el stoploss fue resuelto bajo las reglas de negocio
                                posicion.stoploss_pending = False
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
    if (Polaridad == 0):
        # return Polaridad
        return df["Polaridad"].iloc[1]
    elif (Polaridad != 0 and Polaridad != df["Polaridad"].iloc[1]):
        Polaridad = df["Polaridad"].iloc[1]
        return Polaridad
    elif (Polaridad != 0 and Polaridad == df["Polaridad"].iloc[1]):
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


def get_symb(cont: int, symb_list: list, MAX_CURRENCY: int):
    symb = symb_list[cont]
    if (cont == MAX_CURRENCY):
        return symb, 0
    else:
        cont += 1
        return symb, cont


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


def Trading_logic(client, symb_list: list, interval: str, MAX_CURRENCY: int, Polaridad_l: list, posicion_list: list, symb_cont: int):
    symb, symb_cont = get_symb(symb_cont, symb_list, MAX_CURRENCY)
    df = get_data(symb, interval)
    df = CalculateSupertrend(df, 3.215,12) # Calcular el indicador de SuperTrend con multiplicador 3-215 y periodo 12
    posicion_list = Revisar_Arreglo(posicion_list, df, client, symb)
    if (Polaridad_l[symb_cont] != df['Polaridad'].iloc[1]):
        log.info(
            f"La polaridad de {symb} guardada {Polaridad_l[symb_cont]} es diferente  {df['Polaridad'].iloc[1]} [Primer Tier")
        '''
    Caso 1 : Para compra long en futures
    '''
        if (df['Close'].iloc[1] >= df['Supertrend'].iloc[1] and df['Polaridad'].iloc[1] == 1 and df['Polaridad'].iloc[1] != df['Polaridad'].iloc[2]):
            log.info(
                f"El close del symbolo {symb} es mayor a la supertrend ({df['Close'].iloc[1]} > {df['Supertrend'].iloc[1]}), la polaridad es {df['Polaridad'].iloc[1]} y diferente a el anterior registro {df['Polaridad'].iloc[2]} [Segundo Tier]")
            if (df['Close'].iloc[1] >= df['DEMA800'].iloc[1]):
                log.info(
                    f"El valor del close del stock {symb} es mayor al DEMA800 ({df['Close'].iloc[1]} > {df['DEMA800'].iloc[1]})[Tercer Tier]")
                cantidad = calcular_qty_posicion(client, symb, float(df['Close'].iloc[0]), float(df['Supertrend'].iloc[0]))
                if cantidad == None:
                    log.info(
                        f"El balance de la cuenta es insuficiente para comprar {symb} [Quinto Tier]")
                    return posicion_list, Polaridad_l, symb_cont
                order = Posicion('Buy', symb, cantidad, df['Polaridad'].iloc[1], str(round(float(df['Supertrend'].iloc[0]), 4)), float(df['Close'].iloc[0]), str(
                    df['Time'].iloc[0]), float(df['Open'].iloc[0]), float(df['High'].iloc[0]), float(df['Low'].iloc[0]), float(df['Volume'].iloc[0]), float(df['DEMA800'].iloc[0]))
                res = order.make_order(client)
                log.info(f"La orden [{str(order)}] se ha abierto exitosamente")
                posicion_list.append(order)
                Polaridad_l[symb_cont] = df['Polaridad'].iloc[1]
                log.info(
                    f"Orden de compra realizada con exito para {symb} [Cuarto Tier]")
                return posicion_list, Polaridad_l, symb_cont
        '''
    Caso 2 : Para compra shorts en futures
    '''
        if (df['Close'].iloc[1] <= df['Supertrend'].iloc[1] and df['Polaridad'].iloc[1] == -1 and df['Polaridad'].iloc[1] != df['Polaridad'].iloc[2]):
            log.info(
                f"El close del symbolo {symb} es menor a la supertrend ({df['Close'].iloc[1]} < {df['Supertrend'].iloc[1]}), la polaridad es {df['Polaridad'].iloc[1]} y diferente a el anterior registro {df['Polaridad'].iloc[2]} [Segundo Tier]")
            if (df['Close'].iloc[1] <= df['DEMA800'].iloc[1]):
                log.info(
                    f"El valor del close del stock {symb} es menor al DEMA800 ({df['Close'].iloc[1]} < {df['DEMA800'].iloc[1]})[Tercer Tier]")
                cantidad = calcular_qty_posicion(client, symb, float(df['Close'].iloc[0]), float(df['Supertrend'].iloc[0]))
                if cantidad == None:
                    log.info(
                        f"El balance de la cuenta es insuficiente para comprar {symb} [Quinto Tier]")
                    return posicion_list, Polaridad_l, symb_cont
                order = Posicion('Sell', symb, cantidad, df['Polaridad'].iloc[1], str(round(float(df['Supertrend'].iloc[0]), 4)), float(df['Close'].iloc[0]), str(
                    df['Time'].iloc[0]), float(df['Open'].iloc[0]), float(df['High'].iloc[0]), float(df['Low'].iloc[0]), float(df['Volume'].iloc[0]), float(df['DEMA800'].iloc[0]))
                res = order.make_order(client)
                log.info(f"La orden [{str(order)}] se ha abierto exitosamente")
                posicion_list.append(order)
                Polaridad_l[symb_cont] = df['Polaridad'].iloc[1]
                log.info(
                    f"Orden de compra realizada con exito para {symb} [Cuarto Tier]")
                return posicion_list, Polaridad_l, symb_cont
        '''
    Caso 3 : Ninguna compra, actualizar polaridad si es que cambia
    '''
        log.info(
            f"La polaridad cambia pero no se ejecuta ninguna orden, actualización de variables [Tier 2.1]")
        Polaridad_l[symb_cont] = Polaridad_Manage(Polaridad_l[symb_cont], df)
        return posicion_list, Polaridad_l, symb_cont

    else:  # Si la polaridad no cambia
        log.info(
            f"La polaridad no cambia por lo que no se realizan ordenes o ninguna actualización [Tier 1.1]")
        return posicion_list, Polaridad_l, symb_cont
