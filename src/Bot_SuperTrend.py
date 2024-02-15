import scripts.ST_Indicators as op
import bybit
import psutil
import time
import logging as log
from  Label_Filter import LabelFilter
import config.Credenciales as id

COIN_SUPPORT = ['ETHUSDT','XRPUSDT'] #Monedas en las cuales se ejecutaran operaciones
CANTIDADES = [0.02, 30]
#Configure log file
logger = log.getLogger(__name__)
logger.addFilter(LabelFilter('TRADING'))
log.basicConfig(
    filename='logs/Trading.log',
    level=log.INFO,
    format='%(asctime)s - %(label)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)

client = bybit.bybit(test=False, api_key= id.Api_Key, api_secret=id.Api_Secret)
print('Login successful')
MAX = len(COIN_SUPPORT) - 1
posicion_list = [] #Lista que contendra las ordenes (Inicialmente vacia)
Polaridad_l = [0] * len(COIN_SUPPORT)  #Lista donde se van a guardar las polaridades respectivas de cada moneda (Inicialmente [0,0])
symb_cont = 0 #Contador de symbolos (Determina cual stock observar) (Inicialmente 0)
while(True):
    print(f"CPU Usage: {psutil.cpu_percent(interval=1)}% | RAM Usage: {psutil.virtual_memory()[2]}% | Disk Usage: {psutil.disk_usage('/')[3]}%") 
    posicion_list, Polaridad_l, symb_cont = op.Trading_logic(client,COIN_SUPPORT,'15', MAX, CANTIDADES, Polaridad_l, posicion_list, symb_cont)
    time.sleep(60) #Espera 60 segundos? para volver a ejecutar el ciclo