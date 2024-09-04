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
from dotenv import load_dotenv
import socket
import os

def Trading_setup():
    if Api_Key != None and Api_Secret != None:
        client = HTTP(testnet=False, api_key=Api_Key, api_secret=Api_Secret)
        print('Login successful')
        CANTIDADES  = op.calcular_qty_posicion(client, COIN_SUPPORT, COIN_LEVERAGE) #Cantidades de monedas a comprar o vender
        MAX = len(COIN_SUPPORT) - 1
        posicion_list = op.get_live_orders(client, COIN_SUPPORT, CANTIDADES) #Lista que contendra las ordenes (Recupera ordenes abiertas a traves del API)
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

def Trading_setup_LLT(ip_server: str, port_server: int):
    if ip_server != None and port_server != None:
        print(f'Conectando al servidor {ip_server}:{port_server}')
        server_address = (ip_server, port_server) #La configuración del servidor TCP debe ser igual a la del Heartbeat_server.cpp
    else:
        raise Exception('No se han configurado la ip y puerto en el archivo .env')
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(server_address)
            if Api_Key != None and Api_Secret != None:
                client = HTTP(testnet=False, api_key=Api_Key, api_secret=Api_Secret)
                print('Login successful')
                qty_xrp,qty_one = op.calcular_qty_posicion(client)
                CANTIDADES  = op.calcular_qty_posicion(client, COIN_SUPPORT, COIN_LEVERAGE) #Cantidades de monedas a comprar o vender
                MAX = len(COIN_SUPPORT) - 1
                posicion_list = op.get_live_orders(client, COIN_SUPPORT, CANTIDADES) #Lista que contendra las ordenes (Recupera ordenes abiertas a traves del API)
                Polaridad_l = [0] * len(COIN_SUPPORT)  #Lista donde se van a guardar las polaridades respectivas de cada moneda (Inicialmente [0,0])
                symb_cont = 0 #Contador de symbolos (Determina cual stock observar) (Inicialmente 0)
                while(True):
                    print(f"CPU Usage: {psutil.cpu_percent(interval=1)}% | RAM Usage: {psutil.virtual_memory()[2]}% | Disk Usage: {psutil.disk_usage('/')[3]}%")
                    for i in range(len(COIN_SUPPORT)): 
                        log.info(f"Entro al bucle de monedas: {COIN_SUPPORT[i]}")
                        posicion_list, Polaridad_l, symb_cont = op.Trading_logic(client,COIN_SUPPORT,'15', MAX, CANTIDADES, Polaridad_l, posicion_list, symb_cont)
                    s.sendall("Alive".encode('utf-8')) #Enviando Heartbeat
                    time.sleep(30) #Espera 30 segundos por ciclo
            else:
                log.error('No se han ingresado las credenciales')
                raise Exception('No se han ingresado las credenciales')

    except ConnectionRefusedError as e:
        log.error(f"Connection refused -> {e}")
        raise ConnectionRefusedError(f"Connection refused -> {e}")
    except BrokenPipeError as e:
        log.error(f"Broken pipe error - server not running? -> {e}")
        raise BrokenPipeError(f"Broken pipe error - server not running? -> {e}")
    except Exception as e:
        log.error(f"Error inesperado -> {e}")
        raise Exception(f"Error inesperado -> {e}")




if __name__ == '__main__':

    load_dotenv() #Cargar variables de entorno del archivo .env

    long_lasting_term = os.getenv('LLT')
    Api_Key = os.getenv('Api_Key')
    Api_Secret = os.getenv('Api_Secret')

    COIN_SUPPORT = ['XRPUSDT','ONEUSDT'] #Monedas en las cuales se ejecutaran operaciones
    COIN_LEVERAGE = [70,25] #Apalancamiento de cada una de las monedas
    
    #Configure log file
    logger = log.getLogger(__name__)
    log.basicConfig(filename='Trading.log', level=log.INFO, format= '%(levelname)s - %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filemode='w')

    #Ejecutar logica de trading dependiendo de el tipo de ejecución requerida
    if long_lasting_term == 'True':
        log.info('Ejecutando Trading con soporte Long Lasting Term')
        Trading_setup_LLT(os.getenv('IP'), int(os.getenv('PORT')))
    else:
        log.info('Ejecutando Trading sin soporte para Long Lasting Term')
        Trading_setup()
