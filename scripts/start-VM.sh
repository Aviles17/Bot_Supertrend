#!/bin/sh

#Cabe resaltar que este script solo funciona cuando las dependencias y proceso de instalación ya fue completado

# Ejecutar el programa de Heartbeat como servidor 
g++ scripts/Heartbeat_server.cpp -o Heartbeat_server
./Heartbeat_server &

# Ejecutar el script Bot_SUpertrend en segundo plano como cliente
nohup python src/Bot_SuperTrend.py > output.log &