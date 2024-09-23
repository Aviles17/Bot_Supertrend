import unittest
from pybit.unified_trading import HTTP
import pandas as pd
import os
from scripts.ST_Indicators import Get_Balance
from scripts.ST_Indicators import get_data
from scripts.ST_Indicators import CalculateSupertrend
from dotenv import load_dotenv


class TestST_Indicators_Util(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        Api_Key = os.getenv('Api_Key')
        Api_Secret = os.getenv('Api_Secret')
        self.client = HTTP(testnet=False, api_key=Api_Key,
                           api_secret=Api_Secret)

    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion Get_Balance del archivo ST_Indicators
    [Prueba]: Se espera que el balance sea un float y que sea mayor a 0
    ###################################################################################
    '''

    def test_get_balance(self):
        balance = Get_Balance(self.client, 'USDT')
        self.assertIsInstance(float(balance), float)
        self.assertGreater(float(balance), 0.0)

    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion get_data del archivo ST_Indicators
    [Prueba]: Se espera que el dataframe sea de tipo pandas.core.frame.DataFrame y que este no este vacio
    ###################################################################################
    '''

    def test_get_data(self):
        df = get_data('XRPUSDT', '30')
        self.assertIsInstance(df, pd.core.frame.DataFrame)
        self.assertFalse(df.empty)

    '''
    ###################################################################################
    [Proposito]: Prueba para la funcion CalculateSupertrend del archivo ST_Indicators
    [Prueba]: Se espera que el dataframe sea de tipo pandas.core.frame.DataFrame y que este contenga las columnas adecuadas
    ###################################################################################
    '''

    def test_calculate_supertrend(self):
        df = get_data('XRPUSDT', '30')
        df = CalculateSupertrend(df, 3)
        self.assertIsInstance(df, pd.core.frame.DataFrame)
        self.assertFalse(df.empty)
        self.assertIn('Supertrend', df.columns)
        self.assertIn('Polaridad', df.columns)
        self.assertIn('ST_Inferior', df.columns)
        self.assertIn('ST_Superior', df.columns)


if __name__ == '__main__':
    unittest.main()
