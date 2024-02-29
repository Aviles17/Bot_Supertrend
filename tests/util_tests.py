import unittest
from pybit.unified_trading import HTTP
import pandas as pd
from scripts.ST_Indicators import Get_Balance
from scripts.ST_Indicators import get_data
from scripts.ST_Indicators import CalculateSupertrend
import config.Credenciales as id


class TestST_Indicators_Util(unittest.TestCase):
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion Get_Balance del archivo ST_Indicators
    [Prueba]: Se espera que el balance sea un float y que sea mayor a 0
    ###################################################################################
    '''
    def test_get_balance(self):
        client = HTTP(testnet=False, api_key=id.Api_Key, api_secret=id.Api_Secret)
        balance = Get_Balance(client, 'USDT')
        self.assertIsInstance(float(balance), float)
        self.assertGreater(float(balance), 0.0)
        
        
    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion get_data del archivo ST_Indicators
    [Prueba]: Se espera que el dataframe sea de tipo pandas.core.frame.DataFrame y que este no este vacio
    ###################################################################################
    '''
    def test_get_data(self):
        df = get_data('ETHUSDT', '15')
        self.assertIsInstance(df, pd.core.frame.DataFrame)
        self.assertFalse(df.empty)
        

    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion CalculateSupertrend del archivo ST_Indicators
    [Prueba]: Se espera que el dataframe sea de tipo pandas.core.frame.DataFrame y que este contenga las columnas adecuadas
    ###################################################################################
    '''
    def test_calculate_supertrend(self):
        df = get_data('ETHUSDT', '15')
        df = CalculateSupertrend(df)
        self.assertIsInstance(df, pd.core.frame.DataFrame)
        self.assertFalse(df.empty)
        self.assertIn('Supertrend', df.columns)
        self.assertIn('Polaridad', df.columns)
        self.assertIn('ST_Inferior', df.columns)
        self.assertIn('ST_Superior', df.columns)
        
        
if __name__ == '__main__':
    unittest.main()