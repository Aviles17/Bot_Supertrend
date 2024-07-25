import time
import logging as log
import math
import os
import csv
from requests.exceptions import RequestException
from websocket._exceptions import WebSocketException

class Posicion:
    #Constructor del Objeto
    def __init__(self,side: str, symbol: str, amount: float, label: int, stoploss: str, price: float, order_time: str, open: float, high: float, low: float, volume: float, dema800: float):
        #Variables necesarias para crear la orden y seguir con la logica de negocio
        self.id = None
        self.position_idx = None
        self.side = side
        self.symbol = symbol
        self.amount = amount
        self.label = label
        self.stoploss = stoploss
        self.price = price
        self.time = order_time
        self.half_price = (2*price) - float(stoploss)
        self.half_order = False
        self.stoploss_pending = False
        #Atributos requeridos para inteligencia o BD
        self.open = open
        self.high = high
        self.low = low
        self.volume = volume
        self.dema800 = dema800
        self.supertrend = stoploss
    
    def __str__(self):
        return f"Posicion(id={self.id}, side={self.side}, symbol={self.symbol}, amount={self.amount}, label={self.label}, stoploss={self.stoploss}, price={self.price}, time={self.time}, half_price={self.half_price}, half_order_made={self.half_order})"


    def make_order(self, client):
        retry = False
        if self.side == 'Buy':
            self.position_idx = 1
        elif self.side == 'Sell':
            self.position_idx = 2
        else:
            log.error('La orden seleccionada no se ha creado correctamente [El lado de la orden no es valido]')
            return None
        while(True):
            try:
                res = client.place_order(
                    category = "linear",
                    symbol = self.symbol,
                    side = self.side,
                    orderType="Market",
                    qty= self.amount,
                    timeInForce='GoodTillCancel',
                    reduceOnly=False,
                    closeOnTrigger= False,
                    stopLoss = self.stoploss,
                    tpTriggerBy = 'LastPrice',
                    slTriggerBy = 'MarkPrice',
                    positionIdx = self.position_idx
                )
                self.id = res['result']['orderId']
                break
            except RequestException as e:
                log.error(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                time.sleep(10)
            except WebSocketException as e:
                    log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
                    time.sleep(10)
            except Exception as e:
                if isinstance(e, KeyError) and retry == False:
                    retry = True
                    log.error(f"Se encontro un error inesperado accediendo a la informacion {e}. Reintentando en 10 segundos...\n")
                    time.sleep(10)
                else:
                    print(f"Error en make_order {e.with_traceback()}")   
                    log.error(f"Se encontro un error inesperado despues del reintento: {e}.\n")
                    break
                    raise
        time.sleep(15) #Esperar 15 segundos para que la acción se complete en el portal
        self.coordinate_order(client) #Coordinar información con API
        log.info(f"Orden {res['result']['orderId']} creada correctamente en BYBIT : {res} de {self.symbol}")
        return res
    
    def coordinate_order(self, client):
        retry = False #Variable de control para reintentos en caso de error al no encontrar la información en el API
        if self.id != None:
            while(True):
                try:
                    res = client.get_order_history(category="linear",orderId=self.id)['result']['list'][0]
                    if res['orderId'] == self.id:
                        if res['avgPrice'] != self.price or float(res['stopLoss']) != self.stoploss:
                            #Revisar y actualizar datos de la posición con relación a la información live
                            if res['avgPrice'] != None:
                                self.price = float(res['avgPrice'])
                                log.info(f"La orden {self.id} se actualizo con relación al precio de Bybit correctamente a {self.price} antes de ser cargada a memoria")
                            if res['stopLoss'] != None:
                                self.stoploss = res['stopLoss']
                                log.info(f"La orden {self.id} se actualizo con stoploss con relación al precio de Bybit correctamente a {self.stoploss} antes de ser cargada a memoria")
                            self.half_price = (2*self.price) - float(self.stoploss)
                            log.info(f"La orden {self.id} se actualizo el valor del halfprice con relación a la información en Bybit correctamente a {self.half_price} antes de ser cargada a memoria")
                            break
                    else:
                        log.error(f'La orden seleccionada {self.id} no se ha encontrado en Bybit {res['orderId']} [El ID de la orden no se encuentra o no concuerda]')
                        break
                except RequestException as e:
                    log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
                    time.sleep(10)
                except WebSocketException as e:
                    log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
                    time.sleep(10)
                except Exception as e:
                    if isinstance(e, KeyError) and retry == False:
                        retry = True
                        log.error(f"Se encontro un error inesperado accediendo a la informacion {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    elif isinstance(e, IndexError) and retry == False:
                        retry = True
                        print(f"Error con reintento en coordinate {e.with_traceback()}") 
                        log.error(f"Se encontro un error inesperado accediendo a la informacion {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    else:
                        print(f"Error en coordinate {e.with_traceback()}")      
                        log.error(f"Se encontro un error inesperado despues del reintento: {e}.\n")
                        break
                        raise
        else:
            log.error('La orden seleccionada no se ha creado correctamente [El ID de la orden no es valido]')
    
    def close_order(self, client, current_pice: float):
        #En el caso de un Long
        if self.id != None:  
            if(self.side == 'Buy'):
                while(True):
                    try:
                        res =  client.place_order(
                                category="linear",
                                symbol=self.symbol,
                                side="Sell",
                                orderType="Market",
                                qty=self.amount,
                                reduceOnly=True,
                                positionIdx = 1
                            )
                        break
                    except RequestException as e:
                        log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    except WebSocketException as e:
                        log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    except Exception as e:
                        log.error(f"Se encontro un error inesperado {e}.\n")
                        break
                        raise
                log.info(f"Orden {self.id} cerrada correctamente en BYBIT : {res}")
                #Crear registro de salida
                self.crear_csv_ordenes(self.is_profit(current_pice))
                return res
            #En el caso de un Short
            elif(self.side == 'Sell'):
                while(True):
                    try:
                        res = client.place_order(
                                category="linear",
                                symbol=self.symbol,
                                side="Buy",
                                orderType="Market",
                                qty=self.amount,
                                reduceOnly=True,
                                positionIdx = 2
                            )
                        break
                    except RequestException as e:
                        log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    except WebSocketException as e:
                        log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    except Exception as e:
                        log.error(f"Se encontro un error inesperado {e}.\n")
                        break
                        raise
                log.info(f"Orden {self.id} cerrada correctamente en BYBIT : {res} de {self.symbol}")
                #Crear registro de salida
                self.crear_csv_ordenes(self.is_profit(current_pice))
                return res
            else:
                log.error('La orden seleccionada no se ha creado correctamente [El lado de la orden no es valido]')
                return None
        else:
            log.error('La orden seleccionada no se ha creado correctamente [El ID de la orden no es valido]')
            return None

    def is_profit(self, current_pice: float):
        if self.side == 'Buy':
            if self.price < current_pice:
                return True
            else:
                return False
        elif self.side == 'Sell':
            if self.price > current_pice:
                return True
            else:
                return False
        else:
            log.error('La orden seleccionada no se ha creado correctamente [El lado de la orden no es valido]')
            return None
        
        
    def stop_loss_reached(self, current_high: float, current_low: float):
        if self.side == 'Buy':
            if float(self.stoploss) >= current_low:
                return True
            else:
                return False
        elif self.side == 'Sell':
            if float(self.stoploss) <= current_high:
                return True
            else:
                return False
        else:
            log.error('La orden seleccionada no se ha creado correctamente [El lado de la orden no es valido]')
            return None
        
        
    def sell_half(self, client):
        half_amount = math.ceil(self.amount/2)
        if self.id != None and self.half_order == False:
            #En el caso de un Long
            if(self.side == 'Buy'):
                while(True):
                    try:
                        res =  client.place_order(
                                category="linear",
                                symbol=self.symbol,
                                side="Sell",
                                orderType="Market",
                                qty=half_amount,
                                reduceOnly=True,
                                positionIdx = 1
                            )
                        break
                    except RequestException as e:
                        log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    except WebSocketException as e:
                        log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    except Exception as e:
                        log.error(f"Se encontro un error inesperado {e}.\n")
                        break
                        raise
                self.half_order = True
                self.amount = half_amount
                log.info(f"Orden {self.id} cerrada a la mitad correctamente en BYBIT : {res} de {self.symbol}")
                return res
            #En el caso de un Short
            elif(self.side == 'Sell'):
                while(True):
                    try:
                        res = client.place_order(
                                category="linear",
                                symbol=self.symbol,
                                side="Buy",
                                orderType="Market",
                                qty=half_amount,
                                reduceOnly=True,
                                positionIdx = 2
                            )
                        break
                    except RequestException as e:
                        log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    except WebSocketException as e:
                        log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
                        time.sleep(10)
                    except Exception as e:
                        log.error(f"Se encontro un error inesperado {e}.\n")
                        break
                        raise
                self.half_order = True
                self.amount = half_amount
                log.info(f"Orden {self.id} cerrada a la mitad correctamente en BYBIT : {res}")
                return res
            else:
                log.error('La orden seleccionada no se ha creado correctamente [El lado de la orden no es valido]')
                return None
        else:
            log.error('La orden seleccionada no se ha creado correctamente [El ID de la orden no es valido]')
            return None
        
    def modificar_stoploss(self, client, nuevo_stoploss: str):
        default_stoploss = nuevo_stoploss
        if self.side == 'Buy':
            nuevo_stoploss = str(float(nuevo_stoploss) + ((self.amount*float(nuevo_stoploss))*round((0.055/100),3)))
        elif self.side == 'Sell':
            nuevo_stoploss = str(float(nuevo_stoploss) - ((self.amount*float(nuevo_stoploss))*round((0.055/100),3)))
        else:
            log.error('La orden seleccionada no se ha creado correctamente [El lado de la orden no es valido]')
            return None
        while(True):
            try:
                res = client.set_trading_stop(
                    category= "linear",
                    symbol= self.symbol, 
                    side=self.side,
                    stopLoss=nuevo_stoploss,
                    positionIdx=self.position_idx
                )
                self.stoploss = nuevo_stoploss
                break
            except RequestException as e:
                log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
                time.sleep(10)
            except WebSocketException as e:
                log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
                time.sleep(10)
            except Exception as e:
                log.error(f"Se encontro un error inesperado, se tratara de usar el stoploss por defecto {default_stoploss}. Error: {e}.\n")
                if self.stoploss_pending == False:
                    self.stoploss_pending = True
                    #Normalmente sera un error de parametros por lo que se maneja con el stoploss por defecto
                    while(True):
                        try:
                            res = client.set_trading_stop(
                            category= "linear",
                            symbol= self.symbol, 
                            side=self.side,
                            stopLoss=default_stoploss,
                            positionIdx=self.position_idx
                            )
                            self.stoploss = default_stoploss
                            break
                        except RequestException as e:
                            log.error(f"Se encontro un error de conexión {e}. Reintentando en 10 segundos...\n")
                            time.sleep(10)
                        except WebSocketException as e:
                            log.error(f"Se encontro un error de WebSocket {e}. Reintentando en 10 segundos...\n")
                            time.sleep(10)
                        except Exception as e:
                            log.error(f"Se encontro un error inesperado usando el stoploss por defecto {e}.\n")
                            res = None
                            break
                            raise
                else:
                    res = None
                    break
                    raise
        if res != None:
            log.info(f"Stoploss de la orden {self.id} modificado correctamente en BYBIT : {res} de {self.symbol}")
        else:
            log.error(f"No fue possible cambiar el stoploss ni a la version modificada ni al default para la orden {self.id}")
            
        return res

    def crear_csv_ordenes(self, profit: bool):
        if not os.path.exists("data"):
            os.makedirs("data")
        
        filepath = os.path.join("data","history.csv")
        fileexist = os.path.isfile(filepath)
        headers = ['Id','Time','Symbol', 'Open', 'High', 'Low', 'Close', 'Volume', 'Supertrend',
                'Polaridad', 'DEMA800', "Half-Order", "Profit"]
        
        with open(filepath, mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not fileexist:
                writer.writerow(headers)
            writer.writerow([self.id,self.time,self.symbol,self.open,self.high,self.price,self.volume,self.supertrend,self.side,self.dema800,self.half_order,profit])
