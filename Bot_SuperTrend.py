import ST_Indicators
import bybit
import Credenciales as id

COIN_SUPPORT = ['ETHUSDT','XRPUSDT'] #Monedas en las cuales se ejecutaran operaciones

client = bybit.bybit(test=False, api_key= id.Api_Key, api_secret=id.Api_Secret)
print('Login successful')
MAX = len(COIN_SUPPORT) - 1
print(MAX)
ST_Indicators.Trading(COIN_SUPPORT,'15', client, MAX)