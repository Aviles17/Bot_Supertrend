import time
import logging as log
class Posicion:
    #Constructor del Objeto
    def __init__(self,side: str, symbol: str, amount: float, label: int, stoploss: str, price: float, order_time: str):
        self.id = None
        self.side = side
        self.symbol = symbol
        self.amount = amount
        self.label = label
        self.stoploss = stoploss
        self.price = price
        self.time = order_time
        self.half_price = (2*price) - float(stoploss)
        self.half_order = False
    
    def __str__(self):
        return f"Posicion(id={self.id}, side={self.side}, symbol={self.symbol}, amount={self.amount}, label={self.label}, stoploss={self.stoploss}, price={self.price}, time={self.time}, half_price={self.half_price}, half_order_made={self.half_order})"
        
    
    def make_order(self, client):
        while(True):
            try:
                res = client.LinearOrder.LinearOrder_new(
                    side = self.side,
                    symbol = self.symbol, 
                    qty = self.amount, 
                    order_type='Market', 
                    time_in_force='GoodTillCancel', 
                    reduce_only=False, 
                    close_on_trigger=False, 
                    order_link_id=None, 
                    stop_loss= self.stoploss, 
                    tp_trigger_by='LastPrice', 
                    sl_trigger_by='MarkPrice', 
                    price=None).result()
                break
            except OSError as e:
                log.error(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                time.sleep(10)
            except Exception as e:
                log.error(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                time.sleep(10) 
        self.id = res[0]['result']['order_id']
        log.info(f"Orden {res[0]['result']['order_id']} creada correctamente en BYBIT : {res}")
        return res
    
    def close_order(self, client):
        #En el caso de un Long
        if self.id != None:  
            if(self.side == 'Buy'):
                while(True):
                    try:
                        res = client.LinearOrder.LinearOrder_new(
                            side='Sell',  # Opposite side to close the position
                            symbol = self.symbol,
                            qty = self.amount,
                            order_type='Market',
                            time_in_force='GoodTillCancel',
                            reduce_only=True,  # Set to True to indicate it's a closing order
                            close_on_trigger=False,
                            order_link_id=None,
                            stop_loss=None,  # Remove stop loss if not needed
                            tp_trigger_by='LastPrice',
                            sl_trigger_by='MarkPrice',
                            price=None
                            ).result()
                        break
                    except OSError as e:
                        log.error(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                        time.sleep(10)
                    except Exception as e:
                        log.error(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                        time.sleep(10) 
                log.info(f"Orden {self.id} cerrada correctamente en BYBIT : {res}")
                return res
            #En el caso de un Short
            elif(self.side == 'Sell'):
                while(True):
                    try:
                        res = client.LinearOrder.LinearOrder_new(
                            side='Buy',  # Opposite side to close the position
                            symbol = self.symbol,
                            qty = self.amount,
                            order_type='Market',
                            time_in_force='GoodTillCancel',
                            reduce_only=True,  # Set to True to indicate it's a closing order
                            close_on_trigger=False,
                            order_link_id=None,
                            stop_loss=None,  # Remove stop loss if not needed
                            tp_trigger_by='LastPrice',
                            sl_trigger_by='MarkPrice',
                            price=None
                            ).result()
                        break
                    except OSError as e:
                        log.error(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                        time.sleep(10)
                    except Exception as e:
                        log.error(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                        time.sleep(10)
                log.info(f"Orden {self.id} cerrada correctamente en BYBIT : {res}")
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
        
        
    def stop_loss_reached(self, current_pice: float):
        if self.side == 'Buy':
            if float(self.stoploss) > current_pice:
                return True
            else:
                return False
        elif self.side == 'Sell':
            if float(self.stoploss) < current_pice:
                return True
            else:
                return False
        else:
            log.error('La orden seleccionada no se ha creado correctamente [El lado de la orden no es valido]')
            return None
        
        
    def sell_half(self, client):
        half_amount = self.amount/2
        if self.id != None and self.half_order == False:
            #En el caso de un Long
            if(self.side == 'Buy'):
                while(True):
                    try:
                        res = client.LinearOrder.LinearOrder_new(
                            side='Sell',  # Opposite side to close the position
                            symbol = self.symbol,
                            qty = half_amount,
                            order_type='Market',
                            time_in_force='GoodTillCancel',
                            reduce_only=True,  # Set to True to indicate it's a closing order
                            close_on_trigger=False,
                            order_link_id=None,
                            stop_loss=None,  # Remove stop loss if not needed
                            tp_trigger_by='LastPrice',
                            sl_trigger_by='MarkPrice',
                            price=None
                            ).result()
                        break
                    except OSError as e:
                        log.error(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                        time.sleep(10)
                    except Exception as e:
                        log.error(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                        time.sleep(10)
                self.half_order = True
                self.amount = half_amount
                log.info(f"Orden {self.id} cerrada a la mitad correctamente en BYBIT : {res}")
                return res
            #En el caso de un Short
            elif(self.side == 'Sell'):
                while(True):
                    try:
                        res = client.LinearOrder.LinearOrder_new(
                            side='Buy',  # Opposite side to close the position
                            symbol = self.symbol,
                            qty = half_amount,
                            order_type='Market',
                            time_in_force='GoodTillCancel',
                            reduce_only=True,  # Set to True to indicate it's a closing order
                            close_on_trigger=False,
                            order_link_id=None,
                            stop_loss=None,  # Remove stop loss if not needed
                            tp_trigger_by='LastPrice',
                            sl_trigger_by='MarkPrice',
                            price=None
                            ).result()
                        break
                    except OSError as e:
                        log.error(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                        time.sleep(10)
                    except Exception as e:
                        log.error(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                        time.sleep(10)
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
        
    def modificar_stoploss(self, client, nuevo_stoploss):
        while(True):
            try:
                res = client.LinearPositions.LinearPositions_tradingStop(
                    symbol= self.symbol, 
                    side=self.side,
                    stop_loss=nuevo_stoploss
                ).result()
                break
            except OSError as e:
                log.error(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                time.sleep(10)
            except Exception as e:
                log.error(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                time.sleep(10) 
        log.info(f"Stoploss de la orden {self.id} modificado correctamente en BYBIT : {res}")
        return res