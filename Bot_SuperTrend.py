import ST_Indicators
import bybit
import Credenciales as id


#Ambiente de pruebas
client = bybit.bybit(test=False, api_key= id.Api_Key, api_secret=id.Api_Secret)
print('Login successful')
ST_Indicators.Trading('ETHUSDT','15', client)