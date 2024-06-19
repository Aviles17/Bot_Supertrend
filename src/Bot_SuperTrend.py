import scripts.ST_Indicators as op
import psutil
import time
import logging as log
import sys
import json
import math
import requests
from pybit.unified_trading import HTTP
from datetime import datetime
import config.Credenciales as id

if __name__ == '__main__':
    
    COIN_SUPPORT = ['XRPUSDT','ONEUSDT'] #Monedas en las cuales se ejecutaran operaciones
    
    #Configure log file
    logger = log.getLogger(__name__)
    log.basicConfig(filename='Trading.log', level=log.INFO, format= '%(levelname)s - %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filemode='w')

    if id.Api_Key != '' and id.Api_Secret != '':
        client = HTTP(testnet=False, api_key=id.Api_Key, api_secret=id.Api_Secret)
        print('Login successful')
        qty_xrp,qty_one = op.calcular_qty_posicion(client)
        CANTIDADES = [qty_xrp,qty_one] #Cantidades de monedas a comprar o vender
        MAX = len(COIN_SUPPORT) - 1
        posicion_list = [] #Lista que contendra las ordenes (Inicialmente vacia)
        Polaridad_l = [0] * len(COIN_SUPPORT)  #Lista donde se van a guardar las polaridades respectivas de cada moneda (Inicialmente [0,0])
        symb_cont = 0 #Contador de symbolos (Determina cual stock observar) (Inicialmente 0)
        while(True):
            print(f"CPU Usage: {psutil.cpu_percent(interval=1)}% | RAM Usage: {psutil.virtual_memory()[2]}% | Disk Usage: {psutil.disk_usage('/')[3]}%")
            for i in range(len(COIN_SUPPORT)): 
                log.info(f"Entro al bucle de monedas: {COIN_SUPPORT[i]}")
                posicion_list, Polaridad_l, symb_cont = op.Trading_logic(client,COIN_SUPPORT,'15', MAX, CANTIDADES, Polaridad_l, posicion_list, symb_cont)
            time.sleep(30) #Espera 30 segundos por ciclo
    else:
        log.error('No se han ingresado las credenciales')
        raise Exception('No se han ingresado las credenciales')