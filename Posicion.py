import time
class Posicion:
    #Constructor del Objeto
    def __init__(self,side: str, symbol: str, amount: float, label: int, stoploss: str, price: float, order_time: str):
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
        return f"Posicion(side={self.side}, symbol={self.symbol}, amount={self.amount}, label={self.label}, stoploss={self.stoploss}, price={self.price}, time={self.time})"
        
    
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
                print(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                time.sleep(10)
            except Exception as e:
                print(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                time.sleep(10) 
        return res
    
    def close_order(self, client):
        #En el caso de un Long
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
                    print(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10)
                except Exception as e:
                    print(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10) 
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
                    print(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10)
                except Exception as e:
                    print(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10)
            return res
        
        else:
            res = 'La orden seleccionada no se ha creado correctamente'
            return res
            
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
            print('La orden seleccionada no se ha creado correctamente')
            return None
        
    def sell_half(self, client):
        half_amount = self.amount/2
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
                    print(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10)
                except Exception as e:
                    print(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10) 
            self.half_order = True
            self.amount = half_amount
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
                    print(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10)
                except Exception as e:
                    print(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10)
            self.half_order = True
            self.amount = half_amount
            return res
        
        else:
            res = 'La orden seleccionada no se ha creado correctamente'
            return res
        
    '''
    def modificar_stoploss(client, order_id, nuevo_stoploss):
    while(True):
        try:
            res = client.LinearOrder.LinearOrder_replace(
                order_id = order_id,
                stop_loss = nuevo_stoploss
            ).result()
            break
        except OSError as e:
            print(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
            time.sleep(10)
        except Exception as e:
            print(f"Encountered error: {e}. Retrying in 10 seconds...\n")
            time.sleep(10) 
    return res
    '''
            
            
        
            
            
    
        