import time
class Posicion:
    #Constructor del Objeto
    def __init__(self,side: str, symbol: str, amount: float, label: int, stoploss: str):
        self.side = side
        self.symbol = symbol
        self.amount = amount
        self.label = label
        self.stoploss = stoploss
    
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
                    return res
                except OSError as e:
                    print(f"Encountered connection error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10)
                except Exception as e:
                    print(f"Encountered error: {e}. Retrying in 10 seconds...\n")
                    time.sleep(10)
        
        else:
            res = 'La orden seleccionada no se ha creado correctamente'
            return res
            
            
    
        