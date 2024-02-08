import unittest
import bybit
import time
from src.Posicion import Posicion
from scripts.ST_Indicators import get_data
from scripts.ST_Indicators import CalculateSupertrend
import config.Credenciales as id

class TestST_Indicators_Util(unittest.TestCase):
    
    def setUp(self):
        df = get_data('XRPUSDT', '15') #XRPUSDT fue seleccionado para la prueba debido a su bajo costo
        self.stock_df = CalculateSupertrend(df)
        self.client = bybit.bybit(test=False, api_key= id.Api_Key, api_secret=id.Api_Secret)
        
        
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion make_order y close_order del archivo Posicion
    [Prueba]: Se espera que la orden se abra y se cierre correctamente, ambas con un retorno de 'OK'
    ###################################################################################
    '''
    def test_make_close_order(self):
        if self.stock_df["Polaridad"].iloc[-2] == 1:
            order = Posicion('Buy','XRPUSDT',30, self.stock_df["Polaridad"].iloc[-2],str(round(float(self.stock_df['Supertrend'].iloc[-2]),4)),float(self.stock_df['Close'].iloc[-2]), str(self.stock_df['Time'].iloc[-2]))
        elif self.stock_df["Polaridad"].iloc[-2] == -1:
            order = Posicion('Sell','XRPUSDT',30, self.stock_df["Polaridad"].iloc[-2],str(round(float(self.stock_df['Supertrend'].iloc[-2]),4)),float(self.stock_df['Close'].iloc[-2]), str(self.stock_df['Time'].iloc[-2]))
        
        res = order.make_order(self.client)
        self.assertEqual(res[0]['ret_msg'], 'OK')
        time.sleep(60) #Espera 60 segundos para cerrar la orden
        res = order.close_order(self.client)
        self.assertEqual(res[0]['ret_msg'], 'OK')
    
    
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion is_profit del archivo Posicion
    [Prueba]: Se espera que el retorno sea booleano y que sea True si la orden es de compra, y el precio actual es mayor al precio de compra
    ###################################################################################
    '''
    def test_is_profit(self):
        if self.stock_df["Polaridad"].iloc[-2] == 1:
            order = Posicion('Buy','XRPUSDT',30, self.stock_df["Polaridad"].iloc[-2],str(round(float(self.stock_df['Supertrend'].iloc[-2]),4)),float(self.stock_df['Close'].iloc[-2]), str(self.stock_df['Time'].iloc[-2]))
            res = order.is_profit(float(self.stock_df['Close'].iloc[-10]))
            self.assertIsInstance(res, bool)
            if order.price > float(self.stock_df['Close'].iloc[-10]):
                self.assertEqual(res, True)
            else:
                self.assertEqual(res, False)
        elif self.stock_df["Polaridad"].iloc[-2] == -1:
            order = Posicion('Sell','XRPUSDT',30, self.stock_df["Polaridad"].iloc[-2],str(round(float(self.stock_df['Supertrend'].iloc[-2]),4)),float(self.stock_df['Close'].iloc[-2]), str(self.stock_df['Time'].iloc[-2]))
            res = order.is_profit(float(self.stock_df['Close'].iloc[-10]))
            self.assertIsInstance(res, bool)
            if order.price < float(self.stock_df['Close'].iloc[-10]):
                self.assertEqual(res, True)
            else:
                self.assertEqual(res, False)
    
    
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion sell_half del archivo Posicion
    [Prueba]: Se espera que se venda la mitad de la posicion y que el retorno sea 'OK'
    ###################################################################################
    '''
    def test_sell_half(self):
        if self.stock_df["Polaridad"].iloc[-2] == 1:
            order = Posicion('Buy','XRPUSDT',30, self.stock_df["Polaridad"].iloc[-2],str(round(float(self.stock_df['Supertrend'].iloc[-2]),4)),float(self.stock_df['Close'].iloc[-2]), str(self.stock_df['Time'].iloc[-2]))
            order.make_order(self.client)
            time.sleep(60) #Espera 60 segundos para vender la mitad
            res = order.sell_half(self.client)
            self.assertEqual(res[0]['ret_msg'], 'OK')
        elif self.stock_df["Polaridad"].iloc[-2] == -1:
            order = Posicion('Sell','XRPUSDT',30, self.stock_df["Polaridad"].iloc[-2],str(round(float(self.stock_df['Supertrend'].iloc[-2]),4)),float(self.stock_df['Close'].iloc[-2]), str(self.stock_df['Time'].iloc[-2]))
            order.make_order(self.client)
            time.sleep(60) #Espera 60 segundos para vender la mitad
            res = order.sell_half(self.client)
            self.assertEqual(res[0]['ret_msg'], 'OK')
            
        time.sleep(60) #Espera 60 segundos para cerrar la orden
        res = order.close_order(self.client)
        self.assertEqual(res[0]['ret_msg'], 'OK')
        
    
    
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion modificar_stoploss del archivo Posicion
    [Prueba]: Se espera que se modifique el valor del stoploss y que el retorno sea 'OK'
    ###################################################################################
    '''
    def test_modificar_stoploss(self):
        if self.stock_df["Polaridad"].iloc[-2] == 1:
            order = Posicion('Buy','XRPUSDT',30, self.stock_df["Polaridad"].iloc[-2],str(round(float(self.stock_df['Supertrend'].iloc[-2]),4)),float(self.stock_df['Close'].iloc[-2]), str(self.stock_df['Time'].iloc[-2]))
            order.make_order(self.client)
            time.sleep(60) #Espera 60 segundos para vender la mitad
        elif self.stock_df["Polaridad"].iloc[-2] == -1:
            order = Posicion('Sell','XRPUSDT',30, self.stock_df["Polaridad"].iloc[-2],str(round(float(self.stock_df['Supertrend'].iloc[-2]),4)),float(self.stock_df['Close'].iloc[-2]), str(self.stock_df['Time'].iloc[-2]))
            order.make_order(self.client)
            time.sleep(60) #Espera 60 segundos para vender la mitad
        new_stoploss = (order.price + float(order.stoploss))/2 # Se calcula el nuevo stoploss con el promedio
        
        res = order.modificar_stoploss(self.client, str(round(new_stoploss,4)))
        self.assertEqual(res[0]['ret_msg'], 'OK')
        time.sleep(60)
        res = order.close_order(self.client)
        self.assertEqual(res[0]['ret_msg'], 'OK')


if __name__ == '__main__':
    unittest.main()