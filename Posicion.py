class Posicion:
    #Constructor del Objeto
    def __init__(self,side: str, symbol: str, amount: float, label: int):
        self.side = side
        self.symbol = symbol
        self.amount = amount
        self.label = label
    
    def make_order(self,stoploss:str, client):
        res = client.LinearOrder.LinearOrder_new(
            side = self.side,
            symbol = self.symbol, 
            qty = self.amount, 
            order_type='Market', 
            time_in_force='GoodTillCancel', 
            reduce_only=False, 
            close_on_trigger=False, 
            order_link_id=None, 
            stop_loss= stoploss, 
            tp_trigger_by='LastPrice', 
            sl_trigger_by='MarkPrice', 
            price=None).result()
        
        return res 
    
    def close_order(self, client):
        #En el caso de un Long
        if(self.side == 'Buy'):
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
            return res
        #En el caso de un Short
        elif(self.side == 'Sell'):
            
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
        
        else:
            res = 'La orden seleccionada no se ha creado correctamente'
            return res
            
            
    
        