import scripts.ST_Indicators as ST_Indicators
import bybit
import config.Credenciales as id

COIN_SUPPORT = ['ETHUSDT','XRPUSDT'] #Monedas en las cuales se ejecutaran operaciones
CANTIDADES = [0.02, 30]

client = bybit.bybit(test=False, api_key= id.Api_Key, api_secret=id.Api_Secret)
print('Login successful')
MAX = len(COIN_SUPPORT) - 1
ST_Indicators.Trading(COIN_SUPPORT,'15', client, MAX, CANTIDADES)