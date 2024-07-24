import unittest
from pybit.unified_trading import HTTP
import time
import os
from src.Posicion import Posicion
from scripts.ST_Indicators import get_data
from scripts.ST_Indicators import CalculateSupertrend
import scripts.ST_Indicators as op
from dotenv import load_dotenv

class TestPosicions(unittest.TestCase):
    
    def setUp(self):
        df = get_data('XRPUSDT', '15') #XRPUSDT fue seleccionado para la prueba debido a su bajo costo
        self.stock_df = CalculateSupertrend(df)
        load_dotenv()
        Api_Key = os.getenv('Api_Key')
        Api_Secret = os.getenv('Api_Secret')
        self.client = HTTP(testnet=False, api_key=Api_Key, api_secret=Api_Secret)
        self.qty_xrp = 10 #Valor minimo y fijo para tests con XRPUSDT
        time.sleep(15)
        
        
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion make_order y close_order del archivo Posicion
    [Prueba]: Se espera que la orden se abra y se cierre correctamente, ambas con un retorno de 'OK'
    ###################################################################################
    '''
    def test_make_close_order(self):
        if self.stock_df["Polaridad"].iloc[1] == 1:
            order = Posicion('Buy','XRPUSDT',self.qty_xrp, self.stock_df["Polaridad"].iloc[1],str(round(float(self.stock_df['Supertrend'].iloc[0]),4)),float(self.stock_df['Close'].iloc[0]), str(self.stock_df['Time'].iloc[0]), float(self.stock_df['Open'].iloc[0]), float(self.stock_df['High'].iloc[0]), float(self.stock_df['Low'].iloc[0]), float(self.stock_df['Volume'].iloc[0]), float(self.stock_df['DEMA800'].iloc[0]))
        elif self.stock_df["Polaridad"].iloc[1] == -1:
            order = Posicion('Sell','XRPUSDT',self.qty_xrp, self.stock_df["Polaridad"].iloc[1],str(round(float(self.stock_df['Supertrend'].iloc[0]),4)),float(self.stock_df['Close'].iloc[0]), str(self.stock_df['Time'].iloc[0]), float(self.stock_df['Open'].iloc[0]), float(self.stock_df['High'].iloc[0]), float(self.stock_df['Low'].iloc[0]), float(self.stock_df['Volume'].iloc[0]), float(self.stock_df['DEMA800'].iloc[0]))
        
        res = order.make_order(self.client)
        self.assertEqual(res['retMsg'], 'OK')
        time.sleep(15) #Espera 15 segundos para cerrar la orden
        res = order.close_order(self.client, float(self.stock_df['Close'].iloc[0]))
        self.assertEqual(res['retMsg'], 'OK')
    
    
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion is_profit del archivo Posicion
    [Prueba]: Se espera que el retorno sea booleano y que sea True si la orden es de compra, y el precio actual es mayor al precio de compra
    ###################################################################################
    '''
    def test_is_profit(self):
        if self.stock_df["Polaridad"].iloc[1] == 1:
            order = Posicion('Buy','XRPUSDT',self.qty_xrp, self.stock_df["Polaridad"].iloc[1],str(round(float(self.stock_df['Supertrend'].iloc[0]),4)),float(self.stock_df['Close'].iloc[0]), str(self.stock_df['Time'].iloc[0]), float(self.stock_df['Open'].iloc[0]), float(self.stock_df['High'].iloc[0]), float(self.stock_df['Low'].iloc[0]), float(self.stock_df['Volume'].iloc[0]), float(self.stock_df['DEMA800'].iloc[0]))
            res = order.is_profit(float(self.stock_df['Close'].iloc[10]))
            self.assertIsInstance(res, bool)
            if order.price < float(self.stock_df['Close'].iloc[10]):
                self.assertEqual(res, True)
            else:
                self.assertEqual(res, False)
        elif self.stock_df["Polaridad"].iloc[1] == -1:
            order = Posicion('Sell','XRPUSDT',self.qty_xrp, self.stock_df["Polaridad"].iloc[1],str(round(float(self.stock_df['Supertrend'].iloc[0]),4)),float(self.stock_df['Close'].iloc[0]), str(self.stock_df['Time'].iloc[0]), float(self.stock_df['Open'].iloc[0]), float(self.stock_df['High'].iloc[0]), float(self.stock_df['Low'].iloc[0]), float(self.stock_df['Volume'].iloc[0]), float(self.stock_df['DEMA800'].iloc[0]))
            res = order.is_profit(float(self.stock_df['Close'].iloc[10]))
            self.assertIsInstance(res, bool)
            if order.price > float(self.stock_df['Close'].iloc[10]):
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
        if self.stock_df["Polaridad"].iloc[1] == 1:
            order = Posicion('Buy','XRPUSDT',self.qty_xrp, self.stock_df["Polaridad"].iloc[1],str(round(float(self.stock_df['Supertrend'].iloc[0]),4)),float(self.stock_df['Close'].iloc[0]), str(self.stock_df['Time'].iloc[0]), float(self.stock_df['Open'].iloc[0]), float(self.stock_df['High'].iloc[0]), float(self.stock_df['Low'].iloc[0]), float(self.stock_df['Volume'].iloc[0]), float(self.stock_df['DEMA800'].iloc[0]))
            order.make_order(self.client)
            time.sleep(15) #Espera 15 segundos para vender la mitad
            res = order.sell_half(self.client)
            self.assertEqual(res['retMsg'], 'OK')
        elif self.stock_df["Polaridad"].iloc[2] == -1:
            order = Posicion('Sell','XRPUSDT',self.qty_xrp, self.stock_df["Polaridad"].iloc[1],str(round(float(self.stock_df['Supertrend'].iloc[0]),4)),float(self.stock_df['Close'].iloc[0]), str(self.stock_df['Time'].iloc[0]), float(self.stock_df['Open'].iloc[0]), float(self.stock_df['High'].iloc[0]), float(self.stock_df['Low'].iloc[0]), float(self.stock_df['Volume'].iloc[0]), float(self.stock_df['DEMA800'].iloc[0]))
            order.make_order(self.client)
            time.sleep(15) #Espera 15 segundos para vender la mitad
            res = order.sell_half(self.client)
            self.assertEqual(res['retMsg'], 'OK')
            
        time.sleep(15) #Espera 15 segundos para cerrar la orden
        res = order.close_order(self.client, float(self.stock_df['Close'].iloc[0]))
        self.assertEqual(res['retMsg'], 'OK')
        
    
    
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion modificar_stoploss del archivo Posicion
    [Prueba]: Se espera que se modifique el valor del stoploss y que el retorno sea 'OK'
    ###################################################################################
    '''
    def test_modificar_stoploss(self):
        if self.stock_df["Polaridad"].iloc[2] == 1:
            order = Posicion('Buy','XRPUSDT',self.qty_xrp, self.stock_df["Polaridad"].iloc[1],str(round(float(self.stock_df['Supertrend'].iloc[0]),4)),float(self.stock_df['Close'].iloc[0]), str(self.stock_df['Time'].iloc[0]), float(self.stock_df['Open'].iloc[0]), float(self.stock_df['High'].iloc[0]), float(self.stock_df['Low'].iloc[0]), float(self.stock_df['Volume'].iloc[0]), float(self.stock_df['DEMA800'].iloc[0]))
            order.make_order(self.client)
            new_stoploss = float(order.stoploss) + (float(order.stoploss)*0.1) #Mover 10% del stoploss
            time.sleep(15) #Espera 15 segundos para vender la mitad
        elif self.stock_df["Polaridad"].iloc[2] == -1:
            order = Posicion('Sell','XRPUSDT',self.qty_xrp, self.stock_df["Polaridad"].iloc[1],str(round(float(self.stock_df['Supertrend'].iloc[0]),4)),float(self.stock_df['Close'].iloc[0]), str(self.stock_df['Time'].iloc[0]), float(self.stock_df['Open'].iloc[0]), float(self.stock_df['High'].iloc[0]), float(self.stock_df['Low'].iloc[0]), float(self.stock_df['Volume'].iloc[0]), float(self.stock_df['DEMA800'].iloc[0]))
            order.make_order(self.client)
            new_stoploss = float(order.stoploss) - (float(order.stoploss)*0.1) #Mover 10% del stoploss
            time.sleep(15) #Espera 15 segundos para vender la mitad
        
        res = order.modificar_stoploss(self.client, str(round(new_stoploss,4)))
        self.assertEqual(res['retMsg'], 'OK')
        time.sleep(15)
        res = order.close_order(self.client, float(self.stock_df['Close'].iloc[0]))
        self.assertEqual(res['retMsg'], 'OK')


if __name__ == '__main__':
    unittest.main()